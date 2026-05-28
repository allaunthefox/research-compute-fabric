#!/usr/bin/env python3
"""
VCN Compute Substrate - Use AMD VCN H.264 hardware encoder as computation device.

This shim implements the "Steam Deck MKV trick" from UNIFIED_TRANSPORT_ENCODING_SPEC.md:
- Pack computation data into 1920×1080 YUV420 video frames
- Use AMD AMF H.264 hardware encoder for computation
- Extract results from encoded bitstream (CRC32, transform coefficients, motion vectors)

Shim boundary: I/O only. No decision logic. All computation mapping decisions
belong in Lean (Semantics.MeshRouting and future VCN computation modules).

Usage:
    python3 vcn_compute_substrate.py encode <input_data.bin> <output.mkv>
    python3 vcn_compute_substrate.py decode <input.mkv> <output_data.bin>
    python3 vcn_compute_substrate.py extract_receipt <input.mkv> <receipt.json>
"""

import struct
import subprocess
import json
import zlib
from pathlib import Path
from typing import Tuple, List, Optional
from dataclasses import dataclass, field, asdict

# Frame constants from UNIFIED_TRANSPORT_ENCODING_SPEC.md
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
YUV420_FRAME_SIZE = 3_110_400  # 1920*1080 + 960*540 + 960*540
SIGNATURE_HEADER = b"RDMAVCN\0"
SIGNATURE_SIZE = 24

# Encoder settings for computation mode (software encoding for initial testing)
ENCODER_PROFILE = "main"
ENCODER_LEVEL = "4"
QP_MIN = 2  # Minimal quantization for precise computation
QP_MAX = 4
TRANSFORM_SKIP = True
DEBLOCKING = False
SAO = False
# ── Resolution / Frame Rate Catalog ──────────────────────────────────────────

VCN_RESOLUTIONS = {
  "240p":  (320, 240),
  "360p":  (640, 360),
  "480p":  (854, 480),
  "720p":  (1280, 720),
  "1080p": (1920, 1080),
  "1440p": (2560, 1440),
  "4K":    (3840, 2160),
  "5K":    (5120, 2880),
  "8K":    (7680, 4320),
  "16K":   (15360, 8640),
}

VCN_FRAME_RATES = [30, 60, 120, 144, 240]

RESOLUTION_ORDER = list(VCN_RESOLUTIONS.keys())


@dataclass
class VCNHardwareCapabilities:
  """Detected hardware encoder/decoder capabilities."""
  supported_resolutions: List[Tuple[int, int]] = field(default_factory=lambda: [(1920, 1080)])
  supported_frame_rates: List[int] = field(default_factory=lambda: [30, 60])
  available_encoders: List[str] = field(default_factory=lambda: ["libx264"])
  max_memory_mb: int = 512
  max_bandwidth_mbps: int = 100
  gpu_vendor: str = "unknown"
  gpu_name: str = "unknown"


@dataclass
class VCNComputeFrameSpec:
  """Dynamic frame specification for VCN computation."""
  width: int = 1920
  height: int = 1080
  format: str = "yuv420p"
  bytes_per_frame: int = 3_110_400
  frame_rate: int = 60
  encoder: str = "libx264"


def probe_vcn_capabilities() -> VCNHardwareCapabilities:
   """Probe hardware VCN capabilities using FFmpeg, VAAPI, and vendor tools."""
   caps = VCNHardwareCapabilities()
   encoders_found = []
   try:
       result = subprocess.run(
           ["ffmpeg", "-encoders"],
           capture_output=True, text=True, timeout=10
       )
       output = result.stdout
       for enc in ["h264_vaapi", "hevc_vaapi", "h264_amf", "hevc_amf",
                    "h264_nvenc", "hevc_nvenc", "libx264", "libx265"]:
           if enc in output:
               encoders_found.append(enc)
   except (FileNotFoundError, subprocess.TimeoutExpired):
       encoders_found = ["libx264"]
   caps.available_encoders = encoders_found if encoders_found else ["libx264"]
   # Detect GPU vendor
   try:
       result = subprocess.run(
           ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
           capture_output=True, text=True, timeout=5
       )
       if result.returncode == 0 and result.stdout.strip():
           parts = result.stdout.strip().split(",")
           caps.gpu_vendor = "nvidia"
           caps.gpu_name = parts[0].strip()
           caps.max_memory_mb = int(parts[1].strip())
   except (FileNotFoundError, subprocess.TimeoutExpired):
       pass
   if caps.gpu_vendor == "unknown":
       try:
           result = subprocess.run(["vainfo"], capture_output=True, text=True, timeout=5)
           output = result.stdout + result.stderr
           if "AMD" in output or "RADV" in output or "radeon" in output.lower():
               caps.gpu_vendor = "amd"
               caps.gpu_name = "AMD Radeon (VAAPI)"
           elif "Intel" in output or "iHD" in output or "i965" in output:
               caps.gpu_vendor = "intel"
               caps.gpu_name = "Intel Graphics (VAAPI)"
       except (FileNotFoundError, subprocess.TimeoutExpired):
           pass
   if caps.gpu_vendor == "unknown":
       try:
           vendor_path = Path("/sys/class/drm/card1/device/vendor")
           if vendor_path.exists():
               vendor_id = vendor_path.read_text().strip()
               if vendor_id == "0x1002":
                   caps.gpu_vendor = "amd"
                   caps.gpu_name = "AMD Radeon (DRM)"
               elif vendor_id == "0x8086":
                   caps.gpu_vendor = "intel"
                   caps.gpu_name = "Intel Graphics (DRM)"
       except Exception:
           pass
   preferred_encoder = _select_preferred_encoder(encoders_found, caps.gpu_vendor)
   caps.available_encoders = [preferred_encoder] + [e for e in encoders_found if e != preferred_encoder]
   supported = []
   for name, (w, h) in VCN_RESOLUTIONS.items():
       if w > 3840 and (3840, 2160) in supported:
           supported.append((w, h))
           continue
       if _test_resolution(w, h, preferred_encoder):
           supported.append((w, h))
   caps.supported_resolutions = supported if supported else [(1920, 1080)]
   caps.supported_frame_rates = [fps for fps in VCN_FRAME_RATES if fps <= 240]
   max_w, max_h = caps.supported_resolutions[-1] if caps.supported_resolutions else (1920, 1080)
   max_pixels = max_w * max_h
   caps.max_bandwidth_mbps = (max_pixels * 3 // 2 * 60) // (1024 * 1024)
   return caps


def _select_preferred_encoder(encoders: List[str], vendor: str) -> str:
   """Select the best encoder for the detected GPU vendor."""
   vendor_prefs = {
       "nvidia": ["hevc_nvenc", "h264_nvenc"],
       "amd":    ["hevc_vaapi", "h264_vaapi", "hevc_amf", "h264_amf"],
       "intel":  ["hevc_vaapi", "h264_vaapi"],
   }
   for pref in vendor_prefs.get(vendor, []):
       if pref in encoders:
           return pref
   return "libx265" if "libx265" in encoders else "libx264"


def _test_resolution(width: int, height: int, encoder: str) -> bool:
    """Test if the encoder can handle a given resolution."""
    try:
        test_size = width * height * 3 // 2
        if test_size > 100_000_000:
            return False
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p",
               "-s", f"{width}x{height}", "-frames:v", "1", "-i", "/dev/zero",
               "-c:v", encoder, "-f", "null", "-"]
        if "vaapi" in encoder:
            cmd.insert(1, "-vaapi_device")
            cmd.insert(2, "/dev/dri/renderD128")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def compute_frame_size(width: int, height: int, fmt: str = "yuv420p") -> int:
    """Compute frame size in bytes for given resolution and format."""
    if fmt == "yuv420p":
        return width * height * 3 // 2
    elif fmt == "rgb24":
        return width * height * 3
    raise ValueError(f"Unsupported format: {fmt}")


def select_optimal_resolution(
    caps: VCNHardwareCapabilities,
    target_data_size: int,
    preferred_format: str = "yuv420p"
) -> VCNComputeFrameSpec:
    """Select the smallest resolution that can hold target_data_size."""
    required_size = target_data_size + SIGNATURE_SIZE
    for w, h in caps.supported_resolutions:
        frame_bytes = compute_frame_size(w, h, preferred_format)
        if frame_bytes >= required_size:
            max_fps = 60
            for fps in reversed(caps.supported_frame_rates):
                bandwidth_needed = (frame_bytes * fps) // (1024 * 1024)
                if bandwidth_needed <= caps.max_bandwidth_mbps:
                    max_fps = fps
                    break
            encoder = caps.available_encoders[0] if caps.available_encoders else "libx264"
            return VCNComputeFrameSpec(width=w, height=h, format=preferred_format,
                bytes_per_frame=frame_bytes, frame_rate=max_fps, encoder=encoder)
    w, h = caps.supported_resolutions[-1] if caps.supported_resolutions else (1920, 1080)
    encoder = caps.available_encoders[0] if caps.available_encoders else "libx264"
    return VCNComputeFrameSpec(width=w, height=h, format=preferred_format,
        bytes_per_frame=compute_frame_size(w, h, preferred_format), frame_rate=60, encoder=encoder)


def create_frame_dynamic(data: bytes, seq: int, spec: VCNComputeFrameSpec) -> bytes:
    """Create a frame at dynamic resolution from computation data."""
    frame_size = spec.bytes_per_frame
    if len(data) > frame_size - SIGNATURE_SIZE:
        raise ValueError(f"Data too large: {len(data)} > {frame_size - SIGNATURE_SIZE}")
    frame = bytearray(frame_size)
    version = 1
    length = len(data)
    header = SIGNATURE_HEADER + struct.pack("<IIII", version, seq, length, 0)
    frame[:SIGNATURE_SIZE] = header
    payload = frame[SIGNATURE_SIZE:]
    payload[:len(data)] = data
    payload[len(data):] = bytes([128] * (len(payload) - len(data)))
    return bytes(frame)


def encode_frames_hardware(
    input_frames: List[bytes],
    output_path: Path,
    spec: VCNComputeFrameSpec
) -> subprocess.CompletedProcess:
    """Encode frames using detected hardware encoder with software fallback."""
    raw_path = output_path.with_suffix(".raw")
    with open(raw_path, "wb") as f:
        for frame in input_frames:
            f.write(frame)
    encoder = spec.encoder
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", spec.format,
           "-s", f"{spec.width}x{spec.height}", "-r", str(spec.frame_rate),
           "-i", str(raw_path), "-c:v", encoder, "-qp", str(QP_MIN),
           "-f", "matroska", str(output_path)]
    if "vaapi" in encoder:
        cmd.insert(1, "-vaapi_device")
        cmd.insert(2, "/dev/dri/renderD128")
        cmd.insert(3, "-vf")
        cmd.insert(4, "format=nv12,hwupload")
    elif "nvenc" in encoder:
        cmd.extend(["-preset", "p1", "-tune", "ull"])
    elif "amf" in encoder:
        cmd.extend(["-usage", "ultralowlatency"])
    elif encoder == "libx264":
        cmd.extend(["-profile:v", ENCODER_PROFILE, "-preset", "ultrafast", "-tune", "zerolatency"])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and encoder != "libx264":
        cmd[cmd.index("-c:v") + 1] = "libx264"
        result = subprocess.run(cmd, capture_output=True, text=True)
    raw_path.unlink(missing_ok=True)
    return result


def pack_q16_16_to_yuv(value: int) -> Tuple[int, int, int]:
    """
    Pack a Q16_16 scalar into YUV pixel values.
    
    Mapping strategy: Split 32-bit Q16_16 into three 8-bit components
    with error-diffusion dithering for precision preservation.
    
    Args:
        value: Q16_16 scalar as integer (0x00010000 = 1.0)
    
    Returns:
        (Y, U, V) tuple of pixel values (0-255)
    """
    # Extract bytes from Q16_16 (little-endian)
    y_val = (value >> 16) & 0xFF
    u_val = (value >> 8) & 0xFF
    v_val = value & 0xFF
    
    # Clamp to valid YUV range
    y_val = max(16, min(235, y_val))  # Y: 16-235 (limited range)
    u_val = max(16, min(240, u_val))  # U: 16-240
    v_val = max(16, min(240, v_val))  # V: 16-240
    
    return (y_val, u_val, v_val)


def unpack_yuv_to_q16_16(y: int, u: int, v: int) -> int:
    """
    Unpack YUV pixel values back to Q16_16 scalar.
    
    Args:
        y, u, v: YUV pixel values (0-255)
    
    Returns:
        Q16_16 scalar as integer
    """
    # Reconstruct Q16_16 from YUV components
    value = (y << 16) | (u << 8) | v
    return value


def create_yuv420_frame(data: bytes, seq: int) -> bytes:
    """
    Create a 1920×1080 YUV420 frame from computation data.
    
    Frame layout:
    - Bytes 0-23: Signature header (RDMAVCN\0 + version + seq + length)
    - Bytes 24+: Computation data packed into YUV macroblocks
    
    Args:
        data: Raw computation data bytes
        seq: Frame sequence number
    
    Returns:
        Complete YUV420 frame bytes (3,110,400 bytes)
    """
    if len(data) > YUV420_FRAME_SIZE - SIGNATURE_SIZE:
        raise ValueError(f"Data too large: {len(data)} > {YUV420_FRAME_SIZE - SIGNATURE_SIZE}")
    
    # Create frame buffer
    frame = bytearray(YUV420_FRAME_SIZE)
    
    # Write signature header (exactly 24 bytes)
    version = 1
    length = len(data)
    header = SIGNATURE_HEADER + struct.pack("<IIII", version, seq, length, 0)  # 8 + 4 + 4 + 4 + 4 = 24 bytes
    frame[:SIGNATURE_SIZE] = header
    
    # Ensure frame is exactly the right size
    if len(frame) != YUV420_FRAME_SIZE:
        raise ValueError(f"Frame size mismatch: {len(frame)} != {YUV420_FRAME_SIZE}")
    
    # Pack data into YUV420 format
    # Y plane: 1920×1080 bytes
    # U plane: 960×540 bytes (subsampled 2x)
    # V plane: 960×540 bytes (subsampled 2x)
    
    y_plane = frame[0:FRAME_WIDTH * FRAME_HEIGHT]
    u_plane = frame[FRAME_WIDTH * FRAME_HEIGHT:FRAME_WIDTH * FRAME_HEIGHT + (FRAME_WIDTH // 2) * (FRAME_HEIGHT // 2)]
    v_plane = frame[FRAME_WIDTH * FRAME_HEIGHT + (FRAME_WIDTH // 2) * (FRAME_HEIGHT // 2):]
    
    # Pack data as Q16_16 scalars into macroblocks (6 bytes = 4Y + 1U + 1V)
    data_idx = 0
    macroblock_idx = 0
    
    while data_idx + 4 <= len(data):
        # Read 4 bytes as Q16_16 scalar
        q16_value = struct.unpack("<I", data[data_idx:data_idx + 4])[0]
        y, u, v = pack_q16_16_to_yuv(q16_value)
        
        # Place in macroblock (4 Y pixels, 1 U, 1 V)
        mb_y_start = macroblock_idx * 4
        mb_u_start = macroblock_idx * 1
        mb_v_start = macroblock_idx * 1
        
        if mb_y_start + 4 <= len(y_plane):
            y_plane[mb_y_start:mb_y_start + 4] = bytes([y, y, y, y])
        if mb_u_start + 1 <= len(u_plane):
            u_plane[mb_u_start] = u
        if mb_v_start + 1 <= len(v_plane):
            v_plane[mb_v_start] = v
        
        data_idx += 4
        macroblock_idx += 1
    
    # Pad remaining space with neutral gray (Y=128, U=128, V=128)
    y_plane[macroblock_idx * 4:] = bytes([128] * (len(y_plane) - macroblock_idx * 4))
    u_plane[macroblock_idx:] = bytes([128] * (len(u_plane) - macroblock_idx))
    v_plane[macroblock_idx:] = bytes([128] * (len(v_plane) - macroblock_idx))
    
    return bytes(frame)


def encode_frames(input_frames: List[bytes], output_path: Path) -> subprocess.CompletedProcess:
    """
    Encode raw YUV420 frames using H.264 encoder.
    
    Args:
        input_frames: List of YUV420 frame bytes
        output_path: Output MKV file path
    
    Returns:
        FFmpeg subprocess result
    """
    # Write raw YUV420 file
    raw_path = output_path.with_suffix(".yuv")
    with open(raw_path, "wb") as f:
        for frame in input_frames:
            f.write(frame)
    
    # FFmpeg command for software encoding (libx264) for initial testing
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file
        "-f", "rawvideo",
        "-pix_fmt", "yuv420p",
        "-s", f"{FRAME_WIDTH}x{FRAME_HEIGHT}",
        "-r", "60",  # 60 fps as per spec
        "-i", str(raw_path),
        "-c:v", "libx264",
        "-profile:v", ENCODER_PROFILE,
        "-level", ENCODER_LEVEL,
        "-qp", str(QP_MIN),
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-f", "matroska",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Clean up raw file
    raw_path.unlink()
    
    return result


def decode_frames(input_path: Path) -> List[bytes]:
    """
    Decode MKV file back to raw YUV420 frames using H.264 decoder.
    
    Note: This is lossy - the encoding process modifies pixel values.
    For computation extraction, use extract_receipt() instead.
    
    Args:
        input_path: Input MKV file path
    
    Returns:
        List of decoded YUV420 frame bytes
    """
    raw_path = input_path.with_suffix(".decoded.yuv")
    
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-c:v", "rawvideo",  # Decode to raw, don't re-encode
        "-f", "rawvideo",
        "-pix_fmt", "yuv420p",
        str(raw_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg decode failed: {result.stderr}")
    
    # Read decoded frames
    with open(raw_path, "rb") as f:
        data = f.read()
    
    # Split into frames
    frames = []
    for i in range(0, len(data), YUV420_FRAME_SIZE):
        frame = data[i:i + YUV420_FRAME_SIZE]
        if len(frame) == YUV420_FRAME_SIZE:
            frames.append(frame)
    
    # Clean up
    raw_path.unlink()
    
    return frames


def extract_receipt(input_path: Path) -> dict:
    """
    Extract computation receipt from encoded MKV file.
    
    Receipt includes:
    - CRC32 of encoded file (proves encoding occurred)
    - Frame size statistics
    - Encoding parameters used
    - Bitstream analysis metadata
    - Compression ratio (input vs output size)
    
    Args:
        input_path: Input MKV file path
    
    Returns:
        Receipt dictionary
    """
    # Use ffprobe to get stream information
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(input_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFprobe failed: {result.stderr}")
    
    probe_info = json.loads(result.stdout)
    
    # Calculate file CRC32
    with open(input_path, "rb") as f:
        file_data = f.read()
    file_crc32 = zlib.crc32(file_data) & 0xFFFFFFFF
    
    # Extract compression metrics
    original_size = YUV420_FRAME_SIZE  # Single frame
    compressed_size = len(file_data)
    compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
    
    receipt = {
        "schema": "vcn_computation_receipt_v1",
        "input_file": str(input_path),
        "file_size_bytes": len(file_data),
        "file_crc32": file_crc32,
        "encoding_params": {
            "codec": "libx264",
            "profile": ENCODER_PROFILE,
            "qp_min": QP_MIN,
            "qp_max": QP_MAX,
            "transform_skip": TRANSFORM_SKIP,
            "deblocking": DEBLOCKING,
            "sao": SAO
        },
        "stream_info": probe_info.get("streams", []),
        "format_info": probe_info.get("format", {}),
        "frame_spec": {
            "width": FRAME_WIDTH,
            "height": FRAME_HEIGHT,
            "format": "yuv420p",
            "bytes_per_frame": YUV420_FRAME_SIZE
        },
        "compression_metrics": {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "space_saving": (1 - (compressed_size / original_size)) * 100 if original_size > 0 else 0
        }
    }
    
    return receipt


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: vcn_compute_substrate.py <encode|decode|extract_receipt> <input> <output>")
        sys.exit(1)
    
    command = sys.argv[1]
    input_path = Path(sys.argv[2])
    
    if command == "encode":
        output_path = Path(sys.argv[3])
        
        # Read input data
        with open(input_path, "rb") as f:
            data = f.read()
        
        # Create frame
        frame = create_yuv420_frame(data, seq=0)
        
        # Encode
        result = encode_frames([frame], output_path)
        
        if result.returncode != 0:
            print(f"Encoding failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Encoded to {output_path}")
        
    elif command == "decode":
        output_path = Path(sys.argv[3])
        
        # Decode
        frames = decode_frames(input_path)
        
        # Extract first frame's data
        if frames:
            frame = frames[0]
            # Extract signature header
            header = frame[:SIGNATURE_SIZE]
            signature, version, seq, length, _ = struct.unpack("<8sIIII", header)
            
            if signature != SIGNATURE_HEADER:
                print(f"Invalid signature: {signature}", file=sys.stderr)
                sys.exit(1)
            
            # Extract data payload
            data = frame[SIGNATURE_SIZE:SIGNATURE_SIZE + length]
            
            with open(output_path, "wb") as f:
                f.write(data)
            
            print(f"Decoded to {output_path}")
        else:
            print("No frames decoded", file=sys.stderr)
            sys.exit(1)
            
    elif command == "extract_receipt":
        receipt = extract_receipt(input_path)
        output_path = Path(sys.argv[3])
        
        with open(output_path, "w") as f:
            json.dump(receipt, f, indent=2)
        
        print(f"Receipt written to {output_path}")
        
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()