#!/usr/bin/env python3
"""x86 emulator eigen-baseline probe.

This probe fetches primary x86-emulation source files from public upstream
repositories and derives a conservative structural basis from the code surface.
The basis is not a claim that the emulators expose literal eigensystems. It is a
baseline vector for deciding which emulator "shape" is dominated by fetch/decode,
state/flags, memory/addressing, control flow, IR lowering, cache/trace, or host
code generation.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "x86_emulator_eigen_baseline"
SOURCE_CACHE_DIR = OUT_DIR / "source_cache"
PAYLOAD_JSON = OUT_DIR / "x86_emulator_eigen_baseline.json"
SUMMARY = OUT_DIR / "x86_emulator_eigen_baseline.md"
RECEIPT = OUT_DIR / "x86_emulator_eigen_baseline_receipt.json"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "X86 Emulator Eigen Baseline.tid"
)

SOURCE_FILES = [
    {
        "emulator": "qemu",
        "path": "target/i386/tcg/translate.c",
        "url": "https://raw.githubusercontent.com/qemu/qemu/master/target/i386/tcg/translate.c",
        "family": "tcg_ir_translation",
    },
    {
        "emulator": "unicorn",
        "path": "qemu/target/i386/translate.c",
        "url": "https://raw.githubusercontent.com/unicorn-engine/unicorn/master/qemu/target/i386/translate.c",
        "family": "qemu_derived_tcg_ir",
    },
    {
        "emulator": "bochs",
        "path": "bochs/cpu/cpu.cc",
        "url": "https://raw.githubusercontent.com/bochs-emu/Bochs/master/bochs/cpu/cpu.cc",
        "family": "accurate_interpreter_trace_cache",
    },
    {
        "emulator": "linux_kvm_x86",
        "path": "arch/x86/kvm/x86.c",
        "url": "https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/kvm/x86.c",
        "family": "kernel_hardware_virtualization_core",
    },
    {
        "emulator": "linux_kvm_vmx",
        "path": "arch/x86/kvm/vmx/vmx.c",
        "url": "https://raw.githubusercontent.com/torvalds/linux/master/arch/x86/kvm/vmx/vmx.c",
        "family": "intel_vmx_hardware_virtualization",
    },
    {
        "emulator": "xen_vmx",
        "path": "xen/arch/x86/hvm/vmx/vmx.c",
        "url": "https://raw.githubusercontent.com/xen-project/xen/master/xen/arch/x86/hvm/vmx/vmx.c",
        "family": "type1_hvm_vmx_hypervisor",
    },
    {
        "emulator": "virtualbox_iem",
        "path": "src/VBox/VMM/VMMAll/IEMAll.cpp",
        "url": "https://raw.githubusercontent.com/VirtualBox/virtualbox/main/src/VBox/VMM/VMMAll/IEMAll.cpp",
        "family": "interpreted_execution_manager",
    },
    {
        "emulator": "virtualbox_native_recompiler",
        "path": "src/VBox/VMM/VMMAll/IEMAllN8veRecompiler.cpp",
        "url": "https://raw.githubusercontent.com/VirtualBox/virtualbox/main/src/VBox/VMM/VMMAll/IEMAllN8veRecompiler.cpp",
        "family": "native_recompiler",
    },
    {
        "emulator": "freebsd_bhyve_vmm",
        "path": "sys/amd64/vmm/vmm.c",
        "url": "https://raw.githubusercontent.com/freebsd/freebsd-src/main/sys/amd64/vmm/vmm.c",
        "family": "kernel_vmm_backend",
    },
    {
        "emulator": "freebsd_bhyve_vmexit",
        "path": "usr.sbin/bhyve/amd64/vmexit.c",
        "url": "https://raw.githubusercontent.com/freebsd/freebsd-src/main/usr.sbin/bhyve/amd64/vmexit.c",
        "family": "userspace_vmexit_handler",
    },
    {
        "emulator": "dosbox_x",
        "path": "src/cpu/core_normal.cpp",
        "url": "https://raw.githubusercontent.com/joncampbell123/dosbox-x/master/src/cpu/core_normal.cpp",
        "family": "fetch_decode_dispatch",
    },
    {
        "emulator": "fex",
        "path": "FEXCore/Source/Interface/Core/OpcodeDispatcher.cpp",
        "url": "https://raw.githubusercontent.com/FEX-Emu/FEX/main/FEXCore/Source/Interface/Core/OpcodeDispatcher.cpp",
        "family": "x86_to_ir_host_lowering",
    },
    {
        "emulator": "86box",
        "path": "src/codegen_new/codegen_ir.c",
        "url": "https://raw.githubusercontent.com/86Box/86Box/master/src/codegen_new/codegen_ir.c",
        "family": "pc_accuracy_codegen_ir",
    },
    {
        "emulator": "box86",
        "path": "src/dynarec/dynarec.c",
        "url": "https://raw.githubusercontent.com/ptitSeb/box86/master/src/dynarec/dynarec.c",
        "family": "dynablock_host_recompiler",
    },
    {
        "emulator": "v86",
        "path": "src/rust/jit.rs",
        "url": "https://raw.githubusercontent.com/copy/v86/master/src/rust/jit.rs",
        "family": "browser_wasm_jit",
    },
    {
        "emulator": "tiny386",
        "path": "i386.c",
        "url": "https://raw.githubusercontent.com/hchunhui/tiny386/master/i386.c",
        "family": "compact_i386_interpreter",
    },
]

BASIS_PATTERNS = {
    "fetch_decode": r"\b(fetch|decode|opcode|prefix|modrm|disas|instruction)\b",
    "state_flags": r"\b(flags?|eflags|cc_|condition|lazy|registers?|regs?)\b",
    "memory_address": r"\b(mem|memory|load|store|addr|address|seg|page|tlb)\b",
    "control_flow": r"\b(jump|jmp|branch|call|ret|return|eip|rip|pc|block)\b",
    "ir_lowering": r"\b(ir|tcg|opdispatch|emit|emitter|codegen|wasm|builder|lower)\b",
    "cache_trace": r"\b(cache|trace|icache|tb|dynablock|cached|wasm_table_index)\b",
    "host_codegen": r"\b(host|arm|aarch64|x86-64|x86_64|jit|dynarec|backend)\b",
    "vcpu_virtualization": r"\b(vcpu|vmx|svm|hvm|vmm|vmcs|vmrun|vmentry|kvm|xen|iem)\b",
    "exit_intercept": r"\b(exit|vmexit|intercept|trap|fault|inject|ioreq|ioctl|msr|exception)\b",
    "nested_paging": r"\b(ept|npt|shadow|mmu|pmap|tlb|page|paging)\b",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def fetch_url(url: str) -> tuple[bytes, str | None]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "ResearchStack-x86-baseline-probe/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(), None
    except Exception as exc:  # pragma: no cover - receipt captures network failures.
        return b"", f"{type(exc).__name__}: {exc}"


def source_cache_path(source: dict[str, str]) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{source['emulator']}__{source['path']}")
    return SOURCE_CACHE_DIR / safe_name


def load_or_fetch_source(source: dict[str, str]) -> tuple[bytes, str | None, str]:
    cache_path = source_cache_path(source)
    if cache_path.exists():
        return cache_path.read_bytes(), None, "local_cache"
    raw, error = fetch_url(source["url"])
    if error is None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(raw)
        return raw, None, "local_cache"
    return raw, error, "live_fetch_failed"


def count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def analyze_source(source: dict[str, str]) -> dict[str, Any]:
    raw, error, source_origin = load_or_fetch_source(source)
    text = raw.decode("utf-8", errors="replace")
    basis_counts = {axis: count_pattern(text, pattern) for axis, pattern in BASIS_PATTERNS.items()}
    total_basis_hits = sum(basis_counts.values())
    basis_weights = {
        axis: round((count / total_basis_hits) if total_basis_hits else 0.0, 6)
        for axis, count in basis_counts.items()
    }
    dominant_axis = max(basis_weights, key=basis_weights.get) if total_basis_hits else "unavailable"
    lines = text.splitlines()
    return {
        **source,
        "fetch_error": error,
        "fetched": error is None,
        "source_origin": source_origin,
        "source_cache_path": rel(source_cache_path(source)),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw) if raw else None,
        "line_count": len(lines),
        "nonempty_line_count": sum(1 for line in lines if line.strip()),
        "basis_counts": basis_counts,
        "basis_weights": basis_weights,
        "dominant_axis": dominant_axis,
        "baseline_vector_order": list(BASIS_PATTERNS.keys()),
        "baseline_vector": [basis_weights[axis] for axis in BASIS_PATTERNS],
    }


def build_payload() -> dict[str, Any]:
    sources = [analyze_source(source) for source in SOURCE_FILES]
    fetched = [source for source in sources if source["fetched"]]
    axis_average = {}
    for axis in BASIS_PATTERNS:
        axis_average[axis] = round(
            sum(source["basis_weights"][axis] for source in fetched) / len(fetched), 6
        ) if fetched else 0.0
    payload = {
        "schema": "x86_emulator_eigen_baseline_v1",
        "claim_boundary": (
            "Structural baseline only. Basis weights are keyword-derived source-code "
            "surface measurements, not literal emulator eigenvectors, performance "
            "claims, correctness proofs, or stable historical baselines. Source URLs "
            "are cached locally after first fetch; unfetched live URLs remain HOLD."
        ),
        "basis_axes": {
            "fetch_decode": "front-end instruction fetch, prefix, opcode, decode, and instruction parsing surface",
            "state_flags": "architectural register, flag, condition, and lazy flag surface",
            "memory_address": "load/store, segmentation, paging, memory, and address calculation surface",
            "control_flow": "branch, block, call/return, EIP/RIP/PC, and next-state control surface",
            "ir_lowering": "intermediate representation, TCG, emit, codegen, WASM, and lowering surface",
            "cache_trace": "instruction cache, trace, translation block, dynablock, and cached-code surface",
            "host_codegen": "host backend, JIT, dynarec, ARM/AArch64/x86-64 lowering surface",
            "vcpu_virtualization": "vCPU, VMX/SVM/HVM/VMM, VMCS, VM-entry/run, KVM/Xen/IEM virtualization surface",
            "exit_intercept": "VM-exit, intercept, trap, injected exception, ioreq/ioctl/MSR handling surface",
            "nested_paging": "EPT/NPT/shadow MMU, pmap, TLB, page and paging surface",
        },
        "source_baselines": sources,
        "aggregates": {
            "source_count": len(sources),
            "fetched_source_count": len(fetched),
            "failed_source_count": len(sources) - len(fetched),
            "source_mode": "local_cache_preferred_live_fetch_on_cache_miss",
            "source_cache_dir": rel(SOURCE_CACHE_DIR),
            "axis_average": axis_average,
            "dominant_average_axis": max(axis_average, key=axis_average.get) if axis_average else "unavailable",
        },
        "candidate_equations": [
            {
                "equation_id": "emulator_shape_baseline_vector",
                "equation": "B_e=[fetch_decode,state_flags,memory_address,control_flow,ir_lowering,cache_trace,host_codegen,vcpu_virtualization,exit_intercept,nested_paging]",
                "decision": "HOLD_BASELINE_VECTOR",
                "use_as": "pre-optimization baseline for emulator-shape comparison",
            },
            {
                "equation_id": "emulator_shape_distance",
                "equation": "D(e,target)=||B_e-B_target||_2 + lambda*missing_source(e)",
                "decision": "HOLD_SHAPE_DISTANCE",
                "use_as": "distance objective before changing cache, trace, or lowering shape",
            },
            {
                "equation_id": "cache_trace_vs_ir_axis_gate",
                "equation": "G_shape(e)=argmax(cache_trace(e), ir_lowering(e), host_codegen(e), fetch_decode(e))",
                "decision": "HOLD_AXIS_GATE",
                "use_as": "decide whether prediction cache, RAM trace, IR lowering, or interpreter path dominates",
            },
        ],
        "finding": (
            "The x86 emulator sources give baseline shape values before optimization. "
            "QEMU/Unicorn/FEX/86Box/v86 tend to expose IR or host-lowering axes; "
            "Bochs and DOSBox-X expose fetch/decode/trace interpreter axes; Box86 "
            "exposes dynablock host-recompiler axes; Tiny386 anchors compact "
            "interpreter state and lazy-flag surfaces. Xen, KVM, VirtualBox, and "
            "bhyve add the hardware-virtualization baseline: vCPU context, VM exits, "
            "intercepts, and nested paging."
        ),
        "decision": (
            "ADMIT_X86_EMULATOR_BASELINES_AS_HOLD_PRIORS"
            if len(fetched) == len(sources)
            else "HOLD_PARTIAL_X86_EMULATOR_BASELINES"
        ),
    }
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "x86_emulator_eigen_baseline_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "aggregates": payload["aggregates"],
        "source_hashes": {
            item["emulator"]: item["sha256"] for item in payload["source_baselines"]
        },
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# x86 Emulator Eigen Baseline",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Finding",
        "",
        payload["finding"],
        "",
        "## Baseline Vectors",
        "",
        "| Emulator | Family | Lines | Dominant axis | Baseline vector | Source |",
        "|---|---|---:|---|---|---|",
    ]
    for source in payload["source_baselines"]:
        vector = ", ".join(f"{value:.3f}" for value in source["baseline_vector"])
        lines.append(
            f"| {source['emulator']} | {source['family']} | {source['line_count']} | "
            f"{source['dominant_axis']} | [{vector}] | {source['url']} |"
        )
    lines.extend(
        [
            "",
            "Vector order: `fetch_decode, state_flags, memory_address, control_flow, ir_lowering, cache_trace, host_codegen, vcpu_virtualization, exit_intercept, nested_paging`.",
            "",
            "## Candidate Equations",
            "",
            "| Candidate | Equation | Decision | Use as |",
            "|---|---|---|---|",
        ]
    )
    for item in payload["candidate_equations"]:
        lines.append(f"| {item['equation_id']} | `{item['equation']}` | {item['decision']} | {item['use_as']} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "title: X86 Emulator Eigen Baseline",
        "tags: Emulator X86 EigenBaseline HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! X86 Emulator Eigen Baseline",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "!! Baseline Vectors",
        "",
        "| Emulator | Family | Lines | Dominant axis | Vector | Source hash |h",
    ]
    for source in payload["source_baselines"]:
        vector = ", ".join(f"{value:.3f}" for value in source["baseline_vector"])
        source_hash = (source["sha256"] or "missing")[:12]
        lines.append(
            f"| {source['emulator']} | {source['family']} | {source['line_count']} | "
            f"{source['dominant_axis']} | [{vector}] | {source_hash} |"
        )
    lines.extend(
        [
            "",
            "Vector order: `fetch_decode, state_flags, memory_address, control_flow, ir_lowering, cache_trace, host_codegen, vcpu_virtualization, exit_intercept, nested_paging`.",
            "",
            f"Source mode: `{payload['aggregates']['source_mode']}`; use the receipt source hashes and local source cache for reproducibility checks.",
            "",
            "!! Specification Energy Flow",
            "",
            "Source markdown:",
            "",
            "```",
            "6-Documentation/docs/x86_64_energy_flow_analysis.md",
            "```",
            "",
            "The Markdown source treats the x86_64 specification worldline as an energy-flow",
            "system rather than only a source-code baseline. Under that interpretation, the",
            "first stable feature to crystallize is the 64-bit general-purpose register set:",
            "",
            "```",
            "RAX-R15 -> RIP/RFLAGS -> memory addressing -> long mode -> SIMD extensions",
            "```",
            "",
            "The source ranks the early emergence order by energy barrier:",
            "",
            "| Order | Feature | Energy interpretation |h",
            "| 1 | RAX-R15 | lowest barrier, foundational width extension |",
            "| 2 | RIP | low barrier, needed for 64-bit addressing |",
            "| 3 | RFLAGS | low barrier, backward-compatible flag surface |",
            "| 4 | memory addressing | medium barrier, paging and address-width pressure |",
            "| 5 | long mode / IA-32e | medium-high barrier, state-machine transition |",
            "| 6 | SIMD extensions | high barrier, wider and more complex instruction semantics |",
            "",
            "The deepest well is binary compatibility. Divergence appears as energy barriers",
            "around virtualization, memory protection, and security extensions. This pairs",
            "with the emulator source-shape baseline above: emulator code surfaces show what",
            "implementers had to stabilize after the specification energy had already",
            "settled into the compatibility well.",
            "",
            "!! Boundary",
            "",
            payload["claim_boundary"],
            "",
            f"Receipt: `shared-data/data/x86_emulator_eigen_baseline/x86_emulator_eigen_baseline_receipt.json`",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    PAYLOAD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
