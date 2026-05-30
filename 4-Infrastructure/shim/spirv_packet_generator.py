#!/usr/bin/env python3
"""
SPIR-V Packet Generator — OpPhi-driven packet descriptor for GPU shaders.

Reads SPIR-V assembly text → copy-if optimizer → emits:
  1. Optimized SPIR-V assembly (ready for Mesa/ANV/RADV)
  2. JSON packet descriptors (one per OpSelect, driven by OpPhi analysis)

For WGSL input: compile to SPIR-V assembly first using one of:
  - tint (from nixpkgs): nix-build '<nixpkgs>' -A tint
  - dawn (from nixpkgs): nix-build '<nixpkgs>' -A dawn
  - docker run --rm -v $PWD:/src gcross/wgsl-to-spv:latest /src/in.wgsl -o /src/out.spvasm

Packet descriptor schema (v1):
  {
    "packet_id": <result_id>,
    "type_id": <OpPhi args[0]>,
    "cond_id": <condition variable id>,
    "true_val_id": <value when cond=true>,
    "false_val_id": <value when cond=false>,
    "packet_bytes": <estimated packet size>,
    "spi_v_offset": <byte offset in output SPIR-V>,
  }

The 5 OpPhi fields fully determine the packet layout and are the canonical
representation for all downstream tooling (PIST simulation, Lean emission, etc.).

Usage:
  spirv_packet_generator.py input.spvasm [output_dir]
  spirv_packet_generator.py --analyze input.spvasm
  spirv_packet_generator.py --example
  spirv_packet_generator.py --wgsl-compile input.wgsl [output_dir]
    (requires: nix-build '<nixpkgs>' -A tint -o /tmp/tint)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from spirv_copy_if_optimizer import parse_spirv, transform_copy_if


# ── Packet Descriptor ─────────────────────────────────────────────────────────

@dataclass
class PacketDescriptor:
    packet_id: str
    type_id: str
    cond_id: str
    true_val_id: str
    false_val_id: str
    spi_v_offset: int
    raw_line: str


# ── SPIR-V Assembly Parser for OpSelect ───────────────────────────────────────

_SELECT_RE = re.compile(
    r'^\s*%\s*(?P<result_id>\d+)\s*=\s*OpSelect'
    r'\s+%\s*(?P<type_id>\S+)'
    r'\s+%\s*(?P<cond_id>\S+)'
    r'\s+%\s*(?P<true_id>\S+)'
    r'\s+%\s*(?P<false_id>\S+)'
    r'\s*(?:;.*)?$'
)


def extract_packet_descriptors(spirv_text: str) -> Tuple[List[PacketDescriptor], Dict[str, int]]:
    """Extract packet descriptors from SPIR-V text.

    Parses OpSelect lines to extract the 5 OpPhi-derived fields:
      %result = OpSelect %type %cond %true %false
    """
    descriptors: List[PacketDescriptor] = []
    offset = 0
    offset_map: Dict[str, int] = {}

    for line in spirv_text.splitlines():
        parts = line.strip().split()
        if parts:
            offset_map[parts[0].lstrip('%')] = offset
        offset += len(line) + 1

        m = _SELECT_RE.match(line.strip())
        if not m:
            continue

        descriptors.append(PacketDescriptor(
            packet_id=m.group('result_id'),
            type_id=m.group('type_id'),
            cond_id=m.group('cond_id'),
            true_val_id=m.group('true_id'),
            false_val_id=m.group('false_id'),
            spi_v_offset=offset_map.get(m.group('result_id'), -1),
            raw_line=line.strip(),
        ))

    return descriptors, offset_map


def estimate_packet_bytes(desc: PacketDescriptor) -> int:
    """Estimate packet size in bytes from descriptor fields.

    Conservative estimate based on SPIR-V word alignment:
      - 6 result/type/cond/true/false IDs = 6 * 4 bytes
      - 5 x % prefix + 4 x space = ~16 bytes raw text overhead
      - OpSelect opcode = 2 SPIR-V words (8 bytes)
      Total ≈ 48 bytes per packet descriptor.
    """
    return 48


# ── Toolchain: WGSL → SPIR-V via tint ────────────────────────────────────────

def compile_wgsl_to_spirv_asm(wgsl_path: Path, tint_path: Optional[Path] = None) -> Tuple[str, List[str]]:
    """Compile WGSL to SPIR-V assembly via tint.

    tint is built from nixpkgs:
      nix-build '<nixpkgs>' -A tint -o /tmp/tint

    Returns (spirv_asm, warnings). On failure, warnings contains error lines.
    """
    if tint_path is None:
        tint_path = Path('/tmp/tint/bin/tint')

    if not tint_path.exists():
        return '', [
            f'tint not found at {tint_path}; '
            'run: nix-build \'<nixpkgs>\' -A tint -o /tmp/tint'
        ]

    with tempfile.NamedTemporaryFile(suffix='.spvasm', delete=False, mode='w') as tmp:
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [str(tint_path), str(wgsl_path),
             '--format', 'spvasm', '-o', str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        return '', [f'tint not found at {tint_path}; install with: nix-build \'<nixpkgs>\' -A tint -o /tmp/tint']
    except subprocess.TimeoutExpired:
        return '', ['tint compilation timed out after 120s']
    finally:
        pass

    warnings = []
    for line in result.stderr.splitlines():
        line = line.strip()
        if line:
            warnings.append(line)

    if tmp_path.exists():
        asm = tmp_path.read_text()
        tmp_path.unlink(missing_ok=True)
        return asm, warnings

    return '', warnings or [result.stderr or 'unknown tint failure']


# ── Packet Generator ──────────────────────────────────────────────────────────

def generate_packets(
    input_path: Path,
    output_dir: Path,
    tint_path: Optional[Path] = None,
) -> Tuple[str, str]:
    """Run the full packet generator toolchain.

    SPIR-V asm → copy-if optimize → packet descriptors
    (For WGSL input: use --wgsl-compile flag instead.)

    Returns (spirv_output_path, json_output_path).
    Raises ValueError on failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    is_wgsl = input_path.suffix.lower() in ('.wgsl', '.wgsl.')

    if is_wgsl:
        spirv_asm, warnings = compile_wgsl_to_spirv_asm(input_path, tint_path)
        if not spirv_asm:
            raise ValueError(f'tint failed: {warnings[0] if warnings else "no output"}')
    else:
        spirv_asm = input_path.read_text()
        warnings = []

    optimized, n_transformed = transform_copy_if(spirv_asm)

    descriptors: List[dict] = []
    if optimized:
        packets, _ = extract_packet_descriptors(optimized)
        for desc in packets:
            descriptors.append({
                'packet_id': desc.packet_id,
                'type_id': desc.type_id,
                'cond_id': desc.cond_id,
                'true_val_id': desc.true_val_id,
                'false_val_id': desc.false_val_id,
                'spi_v_offset': desc.spi_v_offset,
                'packet_bytes': estimate_packet_bytes(desc),
            })

    stem = input_path.stem
    spirv_out = output_dir / f'{stem}.spv.txt'
    json_out = output_dir / f'{stem}_packets.json'

    spirv_out.write_text(optimized)

    bundle = {
        'schema': 'spirv_packet_descriptor_v1',
        'source': str(input_path),
        'packets': descriptors,
        'copy_if_transformed': n_transformed,
        'warnings': warnings,
    }
    json_out.write_text(json.dumps(bundle, indent=2))

    return str(spirv_out), str(json_out)


# ── CLI ───────────────────────────────────────────────────────────────────────

EXAMPLE_SPIR_V = """; SPIR-V fragment shader with copy-if pattern
OpCapability Shader
%1 = OpExtInstImport "GLSL.std.450"
OpMemoryModel Logical GLSL450
OpEntryPoint Fragment %main "main" %color %delta
OpExecutionMode %main OriginUpperLeft
OpDecorate %color Location 0
OpDecorate %delta Location 1
%void = OpTypeVoid
%3 = OpTypeFunction %void
%float = OpTypeFloat 32
%v4float = OpTypeVector %float 4
%float_0 = OpConstant %float 0.0
%float_1 = OpConstant %float 1.0
%bool = OpTypeBool
%_ptr_Output_v4float = OpTypePointer Output %v4float
%_ptr_Input_float = OpTypePointer Input %float
%color = OpVariable %_ptr_Output_v4float Output
%delta = OpVariable %_ptr_Input_float Input
%main = OpFunction %void None %3
%5 = Label
%10 = OpLoad %float %delta
%11 = OpFOrdNotEqual %bool %10 %float_0
OpSelectionMerge %15 None
OpBranchConditional %11 %12 %13
%12 = Label
%14 = OpCompositeConstruct %v4float %10 %10 %10 %float_1
OpBranch %15
%13 = Label
OpBranch %15
%15 = Label
%16 = OpPhi %v4float %14 %12 %float_0 %13
OpStore %color %16
OpReturn
OpFunctionEnd"""


def main():
    args = sys.argv[1:]

    if not args or args[0] == '--example':
        print("=== SPIR-V Packet Generator ===")
        print()
        print("Example SPIR-V assembly (copy-if pattern):")
        print(EXAMPLE_SPIR_V)
        print()

        with tempfile.NamedTemporaryFile(suffix='.spvasm', delete=False, mode='w') as tmp:
            tmp.write(EXAMPLE_SPIR_V)
            tmp_path = Path(tmp.name)

        try:
            spirv_out, json_out = generate_packets(tmp_path, Path('/tmp'))
            print(f"SPIR-V assembly: {spirv_out}")
            print(f"Packet descriptors: {json_out}")
            print()
            bundle = json.loads(Path(json_out).read_text())
            print(json.dumps(bundle, indent=2))
        finally:
            tmp_path.unlink(missing_ok=True)
        return

    if args[0] == '--wgsl-compile':
        if len(args) < 2:
            print("Usage: spirv_packet_generator.py --wgsl-compile <input.wgsl> [output_dir] [tint_path]", file=sys.stderr)
            sys.exit(1)
        wgsl_path = Path(args[1])
        output_dir = Path(args[2]) if len(args) > 2 else wgsl_path.parent
        tint_path = Path(args[3]) if len(args) > 3 else None

        if not wgsl_path.exists():
            print(f"File not found: {wgsl_path}", file=sys.stderr)
            sys.exit(1)

        spirv_out, json_out = generate_packets(wgsl_path, output_dir, tint_path)
        print(f"SPIR-V assembly: {spirv_out}")
        print(f"Packet descriptors: {json_out}")
        return

    if args[0] == '--analyze':
        if len(args) < 2:
            print("Usage: spirv_packet_generator.py --analyze <input.spvasm>", file=sys.stderr)
            sys.exit(1)
        input_path = Path(args[1])
        if not input_path.exists():
            print(f"File not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        _, json_out = generate_packets(input_path, Path('/tmp'))
        data = json.loads(Path(json_out).read_text())

        print(f"=== {input_path.name} ===")
        print(f"  Copy-if patterns transformed: {data['copy_if_transformed']}")
        print(f"  Packet descriptors: {len(data['packets'])}")
        for pkt in data['packets']:
            print(f"    %{pkt['packet_id']}: type=%{pkt['type_id']} "
                  f"cond=%{pkt['cond_id']} true=%{pkt['true_val_id']} "
                  f"false=%{pkt['false_val_id']} "
                  f"({pkt['packet_bytes']} bytes)")
        if data['warnings']:
            print(f"  Warnings: {data['warnings']}")
        return

    if len(args) < 1:
        print("Usage: spirv_packet_generator.py <input.spvasm> [output_dir]", file=sys.stderr)
        print("       spirv_packet_generator.py --wgsl-compile <input.wgsl> [output_dir] [tint_path]", file=sys.stderr)
        print("       spirv_packet_generator.py --analyze <input.spvasm>", file=sys.stderr)
        print("       spirv_packet_generator.py --example", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args[0])
    output_dir = Path(args[1]) if len(args) > 1 else input_path.parent

    if not input_path.exists():
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        spirv_out, json_out = generate_packets(input_path, output_dir)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"SPIR-V assembly: {spirv_out}")
    print(f"Packet descriptors: {json_out}")


if __name__ == '__main__':
    main()
