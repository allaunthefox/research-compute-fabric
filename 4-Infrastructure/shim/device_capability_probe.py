#!/usr/bin/env python3
"""
Device Capability Probe — classify every device in the cluster into a compute tier.

Scans DRM render nodes, FFmpeg encoders, framebuffer devices, and network
connectivity to assign each device the cheapest compute role it can handle.

Hierarchy (highest to lowest capability):
  GPU_CUDA     — NVIDIA discrete with CUDA (Ray GPU worker, NVENC)
  GPU_VAAPI    — AMD/Intel with VA-API (Ray worker, hardware encode)
  GPU_APU      — AMD integrated, shared memory (yuvj420p, bandwidth-optimized)
  CPU_FFMPEG   — No GPU, but FFmpeg with libx264 (Ray CPU worker)
  FRAMEBUFFER  — Has /dev/fb0 only (DMA backplane, 8.29 MB/frame at 1080p)
  ESP32        — MCU with Q0_16 scalar compute (FreeRTOS idle hook)
  RELAY        — Network only, no compute (forward frames)
  OFFLINE      — Unreachable

Usage:
    from device_capability_probe import probe_device, probe_cluster
    caps = probe_device()  # local device
    cluster_caps = probe_cluster(nodes)  # all nodes via SSH/kubectl

Matches: VCNHardwareCapabilities, MathOptimizationLoad from vcn_compute_substrate
"""

from __future__ import annotations

import os
import json
import struct
import subprocess
from enum import IntEnum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


class ComputeTier(IntEnum):
    """Compute capability tiers, ordered by decreasing capability."""
    GPU_CUDA = 6       # NVIDIA discrete + CUDA (NVENC, NVDEC)
    GPU_VAAPI = 5      # AMD/Intel discrete + VA-API hardware encode
    GPU_APU = 4        # AMD integrated, shared memory, bandwidth-optimized
    CPU_FFMPEG = 3     # Software encode only (libx264/libx265)
    FRAMEBUFFER = 2    # /dev/fb0 DMA backplane only
    ESP32 = 1          # MCU, Q0_16 scalar in idle hook
    RELAY = 0          # Network only, no compute
    OFFLINE = -1       # Unreachable


@dataclass
class GPUDevice:
    """A single GPU/render node detected on the system."""
    render_node: str         # e.g. "/dev/dri/renderD128"
    card_id: int             # e.g. 0
    vendor_id: str           # e.g. "0x10de"
    device_id: str           # e.g. "0x2783"
    vendor_name: str         # e.g. "nvidia", "amd", "intel"
    device_name: str         # e.g. "NVIDIA GeForce RTX 4070 SUPER"
    is_discrete: bool        # True for dGPU, False for iGPU/APU
    vram_mb: int = 0         # VRAM in MB (0 for shared memory)
    vaapi_profiles: List[str] = field(default_factory=list)


@dataclass
class FramebufferDevice:
    """A framebuffer device detected on the system."""
    device_path: str         # e.g. "/dev/fb0"
    width: int = 0
    height: int = 0
    bpp: int = 32            # bits per pixel
    capacity_bytes: int = 0  # width * height * (bpp // 8)


@dataclass
class DeviceCapabilities:
    """Complete capability profile for a single device/node."""
    hostname: str
    tier: ComputeTier = ComputeTier.RELAY
    gpus: List[GPUDevice] = field(default_factory=list)
    framebuffer: Optional[FramebufferDevice] = None
    has_ffmpeg: bool = False
    ffmpeg_encoders: List[str] = field(default_factory=list)
    preferred_encoder: str = "libx264"
    preferred_pixel_format: str = "yuv420p"
    max_resolution: Tuple[int, int] = (1920, 1080)
    ray_resources: dict = field(default_factory=dict)
    os_arch: str = "x86_64"
    total_memory_mb: int = 0
    # VCN alignment
    packing_density: str = "macroblock_1x"
    color_range: str = "tv"
    encoder_opts: List[str] = field(default_factory=list)


# ── Vendor ID mapping ────────────────────────────────────────────────────────

VENDOR_MAP = {
    "0x10de": "nvidia",
    "0x1002": "amd",
    "0x8086": "intel",
}

# Discrete GPU device ID ranges (approximate)
NVIDIA_DISCRETE_IDS = {"0x2", "0x1"}  # 0x2xxx = Ada, 0x1xxx = Ampere/Turing
AMD_DISCRETE_MARKERS = {"radeon", "rx ", "vega", "navi", "rdna"}
AMD_APU_MARKERS = {"graphics", "integrated", "apu", "drm", "ryzen", "radeon graphics"}


def _run(cmd: List[str], timeout: int = 5) -> Optional[str]:
    """Run a command, return stdout or None on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return None


def _detect_gpus() -> List[GPUDevice]:
    """Scan all DRM render nodes and classify each GPU."""
    gpus = []
    drm_dir = Path("/sys/class/drm")

    if not drm_dir.exists():
        return gpus

    for card_dir in sorted(drm_dir.glob("card*")):
        card_name = card_dir.name  # e.g. "card0", "card1"
        try:
            card_id = int(card_name.replace("card", ""))
        except ValueError:
            continue

        vendor_path = card_dir / "device" / "vendor"
        device_path = card_dir / "device" / "device"
        render_node = f"/dev/dri/renderD{128 + card_id}"

        if not vendor_path.exists() or not Path(render_node).exists():
            continue

        vendor_id = vendor_path.read_text().strip()
        device_id = device_path.read_text().strip() if device_path.exists() else "0x0000"
        vendor_name = VENDOR_MAP.get(vendor_id, "unknown")

        # Get device name from various sources
        device_name = _get_gpu_name(vendor_name, card_dir, card_id)

        # Classify discrete vs integrated
        is_discrete = _is_discrete_gpu(vendor_name, device_name, device_id)

        # Get VRAM
        vram_mb = _get_vram_mb(vendor_name, card_dir)

        # Probe VA-API profiles
        vaapi_profiles = _probe_vaapi_profiles(render_node)

        gpu = GPUDevice(
            render_node=render_node,
            card_id=card_id,
            vendor_id=vendor_id,
            device_id=device_id,
            vendor_name=vendor_name,
            device_name=device_name,
            is_discrete=is_discrete,
            vram_mb=vram_mb,
            vaapi_profiles=vaapi_profiles,
        )
        gpus.append(gpu)

    return gpus


def _get_gpu_name(vendor: str, card_dir: Path, card_id: int) -> str:
    """Get GPU name from nvidia-smi, DRI, or DRM."""
    if vendor == "nvidia":
        out = _run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        if out:
            return out.strip().split("\n")[0]

    # Try DRI name
    name_path = card_dir / "device" / "product_name"
    if name_path.exists():
        return name_path.read_text().strip()

    # Fallback to vendor-based naming
    return f"{vendor.upper()} GPU (card{card_id})"


def _is_discrete_gpu(vendor: str, name: str, device_id: str) -> bool:
    """Classify GPU as discrete or integrated."""
    name_lower = name.lower()

    if vendor == "nvidia":
        # NVIDIA GPUs with CUDA are always discrete (for our purposes)
        out = _run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        return out is not None

    if vendor == "amd":
        # Check APU markers first
        for marker in AMD_APU_MARKERS:
            if marker in name_lower:
                return False
        # Check discrete markers
        for marker in AMD_DISCRETE_MARKERS:
            if marker in name_lower:
                return True
        # If device has VRAM > 1GB, likely discrete
        vram = _get_vram_mb(vendor, Path(f"/sys/class/drm/card{device_id}"))
        if vram > 1024:
            return True
        # Default: if we can't tell, assume iGPU (conservative)
        return False

    if vendor == "intel":
        # Intel is almost always integrated (except Arc)
        return "arc" in name_lower

    return False


def _get_vram_mb(vendor: str, card_dir: Path) -> int:
    """Get VRAM size in MB."""
    if vendor == "nvidia":
        out = _run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"])
        if out:
            try:
                return int(out.strip().split("\n")[0])
            except ValueError:
                pass

    # Try DRM VRAM info
    vram_path = card_dir / "device" / "mem_info_vram_total"
    if vram_path.exists():
        try:
            return int(vram_path.read_text().strip()) // (1024 * 1024)
        except ValueError:
            pass

    return 0


def _probe_vaapi_profiles(render_node: str) -> List[str]:
    """Probe VA-API profiles for a render node."""
    out = _run(["vainfo", "--display", "drm", "--device", render_node], timeout=10)
    if not out:
        return []
    profiles = []
    for line in out.split("\n"):
        if "VAProfile" in line and ":" in line:
            profiles.append(line.strip().split(":")[0].strip())
    return profiles


def _detect_framebuffer() -> Optional[FramebufferDevice]:
    """Detect framebuffer device and its capabilities."""
    fb_path = Path("/dev/fb0")
    if not fb_path.exists():
        return None

    # Try to get framebuffer info from /sys
    fb_sys = Path("/sys/class/graphics/fb0")
    width, height, bpp = 1920, 1080, 32  # defaults

    virt_size = fb_sys / "virtual_size"
    if virt_size.exists():
        try:
            parts = virt_size.read_text().strip().split(",")
            width, height = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass

    bits_per_pixel = fb_sys / "bits_per_pixel"
    if bits_per_pixel.exists():
        try:
            bpp = int(bits_per_pixel.read_text().strip())
        except ValueError:
            pass

    return FramebufferDevice(
        device_path=str(fb_path),
        width=width,
        height=height,
        bpp=bpp,
        capacity_bytes=width * height * (bpp // 8),
    )


def _detect_ffmpeg() -> Tuple[bool, List[str], str]:
    """Detect FFmpeg and available encoders."""
    out = _run(["ffmpeg", "-encoders"], timeout=10)
    if not out:
        return False, [], "libx264"

    encoders = []
    for enc in ["h264_nvenc", "hevc_nvenc", "h264_vaapi", "hevc_vaapi",
                 "h264_amf", "hevc_amf", "libx264", "libx265"]:
        if enc in out:
            encoders.append(enc)

    preferred = encoders[0] if encoders else "libx264"
    return True, encoders, preferred


def _get_arch() -> str:
    """Detect system architecture."""
    import platform
    machine = platform.machine()
    if machine == "aarch64":
        return "arm64"
    return machine


# ── Main probe function ──────────────────────────────────────────────────────

def probe_device(hostname: str = "") -> DeviceCapabilities:
    """Probe the local device and return complete capability profile.

    Assigns the highest compute tier the device can handle:
      GPU_CUDA > GPU_VAAPI > GPU_APU > CPU_FFMPEG > FRAMEBUFFER > ESP32 > RELAY
    """
    if not hostname:
        import socket
        hostname = socket.gethostname()

    caps = DeviceCapabilities(hostname=hostname, os_arch=_get_arch())

    # 1. Detect GPUs
    caps.gpus = _detect_gpus()

    # 2. Detect FFmpeg
    caps.has_ffmpeg, caps.ffmpeg_encoders, caps.preferred_encoder = _detect_ffmpeg()

    # 3. Detect framebuffer
    caps.framebuffer = _detect_framebuffer()

    # 4. Get system memory
    try:
        meminfo = Path("/proc/meminfo").read_text()
        for line in meminfo.split("\n"):
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                caps.total_memory_mb = kb // 1024
                break
    except (FileNotFoundError, ValueError):
        pass

    # 5. Assign tier and configure
    caps.tier, caps.ray_resources, caps.preferred_pixel_format, caps.packing_density = \
        _assign_tier(caps)

    # 6. Set encoder options based on tier
    caps.encoder_opts = _get_encoder_opts(caps)

    return caps


def _assign_tier(caps: DeviceCapabilities):
    """Assign compute tier based on detected capabilities."""

    # Check for NVIDIA discrete with CUDA
    for gpu in caps.gpus:
        if gpu.vendor_name == "nvidia" and gpu.is_discrete:
            return (
                ComputeTier.GPU_CUDA,
                {"GPU": 1, "nvidia.com/gpu": 1},
                "yuv444p",
                "yuv444_3x",
            )

    # Check for AMD/Intel discrete with VA-API
    for gpu in caps.gpus:
        if gpu.is_discrete and gpu.vaapi_profiles:
            return (
                ComputeTier.GPU_VAAPI,
                {"GPU": 1},
                "yuv444p",
                "yuv444_3x",
            )

    # Check for AMD APU/iGPU (shared memory, bandwidth-optimized)
    for gpu in caps.gpus:
        if not gpu.is_discrete and gpu.vendor_name in ("amd", "intel"):
            return (
                ComputeTier.GPU_APU,
                {"GPU": 1},
                "yuvj420p",  # Full-range YUV420, 50% less bandwidth
                "independent_y_6x",
            )

    # FFmpeg available (software encode)
    if caps.has_ffmpeg:
        return (
            ComputeTier.CPU_FFMPEG,
            {"CPU": 1},
            "yuv420p",
            "macroblock_1x",
        )

    # Framebuffer only
    if caps.framebuffer:
        return (
            ComputeTier.FRAMEBUFFER,
            {"framebuffer": 1},
            "argb8888",  # Direct pixel mapping
            "framebuffer_raw",
        )

    # Default: relay (network only)
    return (ComputeTier.RELAY, {}, "yuv420p", "macroblock_1x")


def _get_encoder_opts(caps: DeviceCapabilities) -> List[str]:
    """Get FFmpeg encoder options based on tier."""
    if caps.tier == ComputeTier.GPU_CUDA:
        return ["-preset", "lossless", "-tune", "zerolatency", "-color_range", "pc"]
    if caps.tier == ComputeTier.GPU_VAAPI:
        return ["-qp", "0", "-color_range", "pc"]
    if caps.tier == ComputeTier.GPU_APU:
        return ["-qp", "0", "-color_range", "pc"]
    if caps.tier == ComputeTier.CPU_FFMPEG:
        return ["-preset", "ultrafast", "-tune", "zerolatency"]
    return []


# ── Cluster probe ────────────────────────────────────────────────────────────

def probe_cluster(nodes: List[str]) -> List[DeviceCapabilities]:
    """Probe all nodes in the cluster via SSH."""
    results = []
    for node in nodes:
        out = _run([
            "ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
            f"root@{node}",
            "python3 -c \"import sys; sys.path.insert(0, '/opt/vcn'); "
            "from device_capability_probe import probe_device; "
            "import json; print(json.dumps(probe_device().__dict__, default=str))\""
        ], timeout=15)
        if out:
            try:
                data = json.loads(out.strip())
                # Reconstruct dataclass
                data["tier"] = ComputeTier(data["tier"])
                data["gpus"] = [GPUDevice(**g) for g in data.get("gpus", [])]
                if data.get("framebuffer"):
                    data["framebuffer"] = FramebufferDevice(**data["framebuffer"])
                results.append(DeviceCapabilities(**data))
            except (json.JSONDecodeError, TypeError):
                results.append(DeviceCapabilities(
                    hostname=node, tier=ComputeTier.OFFLINE))
        else:
            results.append(DeviceCapabilities(
                hostname=node, tier=ComputeTier.OFFLINE))
    return results


# ── Ray scheduling helper ────────────────────────────────────────────────────

def get_ray_placement_strategy(caps: DeviceCapabilities) -> dict:
    """Get Ray scheduling parameters for this device's tier.

    Returns dict suitable for @ray.remote() options.
    """
    if caps.tier == ComputeTier.GPU_CUDA:
        return {"num_gpus": 1, "resources": {"NVENC": 1}}
    if caps.tier == ComputeTier.GPU_VAAPI:
        return {"num_gpus": 1, "resources": {"VAAPI": 1}}
    if caps.tier == ComputeTier.GPU_APU:
        return {"num_gpus": 1, "resources": {"APU": 1}}
    if caps.tier == ComputeTier.CPU_FFMPEG:
        return {"num_cpus": 1}
    if caps.tier == ComputeTier.FRAMEBUFFER:
        return {"resources": {"framebuffer": 1}}
    return {}


def get_framebuffer_resolution(caps: DeviceCapabilities) -> Tuple[int, int]:
    """Get the optimal framebuffer resolution for this device.

    For framebuffer-only devices, returns the actual fb size.
    For GPU devices, returns the VCN resolution that matches.
    """
    if caps.framebuffer:
        return (caps.framebuffer.width, caps.framebuffer.height)
    return caps.max_resolution


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Device Capability Probe")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--cluster", nargs="+", help="Probe remote nodes via SSH")
    args = parser.parse_args()

    if args.cluster:
        results = probe_cluster(args.cluster)
    else:
        results = [probe_device()]

    if args.json:
        output = []
        for caps in results:
            d = asdict(caps)
            d["tier"] = caps.tier.name
            output.append(d)
        print(json.dumps(output, indent=2, default=str))
    else:
        for caps in results:
            print(f"\n{'='*60}")
            print(f"  {caps.hostname} ({caps.os_arch})")
            print(f"  Tier: {caps.tier.name} (value={caps.tier})")
            print(f"{'='*60}")

            if caps.gpus:
                for gpu in caps.gpus:
                    dtype = "dGPU" if gpu.is_discrete else "iGPU/APU"
                    print(f"  GPU: {gpu.device_name} [{dtype}]")
                    print(f"    Render: {gpu.render_node} ({gpu.vendor_id}:{gpu.device_id})")
                    if gpu.vram_mb:
                        print(f"    VRAM: {gpu.vram_mb} MB")
                    if gpu.vaapi_profiles:
                        print(f"    VA-API: {len(gpu.vaapi_profiles)} profiles")
            else:
                print("  GPU: none")

            if caps.framebuffer:
                fb = caps.framebuffer
                print(f"  Framebuffer: {fb.device_path} ({fb.width}x{fb.height} {fb.bpp}bpp)")
                print(f"    Capacity: {fb.capacity_bytes / (1024*1024):.1f} MB")

            print(f"  FFmpeg: {'yes' if caps.has_ffmpeg else 'no'}")
            if caps.ffmpeg_encoders:
                print(f"    Encoders: {', '.join(caps.ffmpeg_encoders)}")
            print(f"  Preferred: {caps.preferred_encoder} ({caps.preferred_pixel_format})")
            print(f"  Ray resources: {caps.ray_resources}")
            print(f"  Memory: {caps.total_memory_mb} MB")


if __name__ == "__main__":
    main()
