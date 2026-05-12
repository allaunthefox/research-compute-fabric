#!/usr/bin/env python3
"""Extract and fold equations from the holographic/fractional/recursive connectome prior."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
SOURCE_RECEIPT = SHIM / "holographic_fractional_recursive_connectome_prior_receipt.json"
RECEIPT = SHIM / "holographic_fractional_recursive_equation_fold_receipt.json"
CURRICULUM = SHIM / "holographic_fractional_recursive_equation_fold_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    source = json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    equations: list[dict[str, Any]] = [
        {
            "id": "connectome_laplacian",
            "lane": "connectome_harmonic_and_manifold_reconfiguration",
            "source_shape": "L_G = D_G - A_G",
            "semantics": "graph Laplacian from structural adjacency and degree matrix",
            "folded_use": "route/equation graph operator whose eigenspaces define candidate modes",
            "receipt_obligation": "graph_state_hash, edge_weight_schema, harmonic_basis_id",
        },
        {
            "id": "connectome_harmonic_decomposition",
            "lane": "connectome_harmonic_and_manifold_reconfiguration",
            "source_shape": "L_G phi_k = lambda_k phi_k; x(t) = sum_k a_k(t) phi_k",
            "semantics": "activity or route state expanded in graph-Laplacian eigenmodes",
            "folded_use": "candidate transform basis over route/equation dependency graph",
            "receipt_obligation": "basis bytes and reconstruction residual are counted",
        },
        {
            "id": "fractional_state_dynamics",
            "lane": "fractional_memory_dynamics",
            "source_shape": "D_t^alpha x(t) = F(x(t), u(t), theta), 0 < alpha <= 1",
            "semantics": "non-integer derivative carries long-memory dynamics",
            "folded_use": "history-sensitive route state updater",
            "receipt_obligation": "fractional_order_alpha, memory_kernel_id, history_window_cost",
        },
        {
            "id": "fractional_memory_kernel",
            "lane": "fractional_memory_dynamics",
            "source_shape": "x_t = x_0 + sum_{tau < t} K_alpha(t - tau) F(x_tau, u_tau)",
            "semantics": "discrete memory convolution approximation to fractional dynamics",
            "folded_use": "bounded state history for nonstationary compression routes",
            "receipt_obligation": "kernel parameters and retained history bytes are counted",
        },
        {
            "id": "recursive_self_update",
            "lane": "recursive_self_organizing_update",
            "source_shape": "h_{n+1} = R_theta(h_n, x_n, G_n); G_{n+1} = U_phi(G_n, h_{n+1})",
            "semantics": "recursive state and graph update under new structured input",
            "folded_use": "equation/route graph rewrite proposal",
            "receipt_obligation": "validation_receipt_id and rollback_state_hash required",
        },
        {
            "id": "holographic_boundary_bulk_split",
            "lane": "holographic_boundary_bulk_encoding",
            "source_shape": "b = P_boundary(z); z_hat = R_bulk(b, r_exact)",
            "semantics": "compact boundary representation plus interior/bulk recovery",
            "folded_use": "short route descriptor plus exact residual rehydration",
            "receipt_obligation": "boundary_code_id, bulk_state_commitment, exact residual hash",
        },
        {
            "id": "exact_holographic_closure",
            "lane": "holographic_boundary_bulk_encoding",
            "source_shape": "H(decode(boundary_code, residual)) == H(source)",
            "semantics": "boundary code has no compression authority until exact decode closes",
            "folded_use": "Hutter promotion gate",
            "receipt_obligation": "decoded hash and measured total bytes",
        },
        {
            "id": "deep_holographic_inverse",
            "lane": "deep_holographic_reconstruction",
            "source_shape": "z_hat = f_theta(y_phase_or_sparse); e = ||A z_hat - y||",
            "semantics": "learned inverse reconstruction with measurement residual",
            "folded_use": "candidate inverse map for route proposals",
            "receipt_obligation": "holographic_reconstruction_error_bound and exact residual lane",
        },
        {
            "id": "atlas_optimal_transport_remap",
            "lane": "atlas_remapping_and_domain_adaptation",
            "source_shape": "T* = argmin_T <C,T> + epsilon KL(T || mu nu^T), T1=mu, T^T1=nu",
            "semantics": "remap connectome/equation coordinates between atlases or schemas",
            "folded_use": "dialect/schema transfer between equation maps",
            "receipt_obligation": "atlas_mapping_id and domain_adaptation_guard_id",
        },
        {
            "id": "domain_adversarial_invariance",
            "lane": "atlas_remapping_and_domain_adaptation",
            "source_shape": "min_{F,C} max_D L_task(C(F(x)), y) - lambda L_domain(D(F(x)), d)",
            "semantics": "learn features predictive for task while suppressing domain identity",
            "folded_use": "negative-transfer guard for borrowed equation features",
            "receipt_obligation": "held-out target validation; no proof transfer by confidence alone",
        },
        {
            "id": "fractal_dimension_marker",
            "lane": "fractal_and_heavy_tail_network_markers",
            "source_shape": "D_f = lim_{epsilon -> 0} log N(epsilon) / log(1/epsilon)",
            "semantics": "multiscale covering dimension of graph or functional state geometry",
            "folded_use": "route segmentation and topology diagnostic",
            "receipt_obligation": "diagnostic only unless tied to exact byte validation",
        },
        {
            "id": "heavy_tail_connectivity_marker",
            "lane": "fractal_and_heavy_tail_network_markers",
            "source_shape": "P(K > k) ~ C k^{-beta}",
            "semantics": "heavy-tailed node/edge influence distribution",
            "folded_use": "prioritize high-influence route/equation nodes",
            "receipt_obligation": "tail-fit cost and uncertainty reported; no promotion authority",
        },
        {
            "id": "network_reconfiguration_objective",
            "lane": "dynamic_network_reconfiguration",
            "source_shape": "G* = argmin_{G'} L_function(G') + lambda C_rewire(G,G') + gamma I_unstable(G')",
            "semantics": "choose new graph under function, rewrite cost, and instability penalty",
            "folded_use": "bounded topology rewrite objective for equation/route graph",
            "receipt_obligation": "perturbation_operator_id, measured function, rollback_state_hash",
        },
    ]

    folded_equations = [
        {
            "id": "folded_route_state",
            "shape": (
                "S_route = (G_hash, Phi_L, boundary_code, bulk_commit, alpha, "
                "K_alpha, R_update, T_atlas, D_guard, F_marker, e_holo, "
                "C_history, validation_receipt, rollback_hash)"
            ),
            "use": "single folded state carrying the extracted equation family into DD search",
        },
        {
            "id": "folded_cost",
            "shape": (
                "C_total = bytes_payload + bytes_boundary + bytes_bulk_commit + "
                "bytes_memory_kernel + bytes_history_window + bytes_residual + "
                "bytes_witness"
            ),
            "use": "prevents holographic or fractional lanes from hiding payload in model state",
        },
        {
            "id": "folded_promotion_gate",
            "shape": (
                "promote iff H(decode(route)) == H(source) and C_total < incumbent "
                "and validation_receipt exists and rollback_hash exists"
            ),
            "use": "keeps exact decode/hash authority outside every predictor",
        },
        {
            "id": "folded_nan0_guard",
            "shape": (
                "NaN0 iff unbounded(K_alpha) or missing(residual) or missing(rollback) "
                "or hidden_payload(boundary_code)"
            ),
            "use": "fail-closed guard for unbounded memory, hidden bulk state, and unsafe recursion",
        },
        {
            "id": "folded_basis_reconstruction",
            "shape": "x_hat = sum_{k in K_kept} a_k phi_k + r_exact",
            "use": "harmonic compression only counts if omitted modes are paid in exact residual",
        },
    ]

    receipt: dict[str, Any] = {
        "schema": "holographic_fractional_recursive_equation_fold_v1",
        "source_receipt": str(SOURCE_RECEIPT.relative_to(REPO)),
        "source_receipt_hash": source["receipt_hash"],
        "primary_read": (
            "The extractable math folds into a graph-state route model: Laplacian "
            "harmonics propose modes, holographic boundary/bulk split proposes a "
            "descriptor/residual separation, fractional dynamics supply bounded "
            "memory, recursive updates propose graph rewrites, OT/domain-adversarial "
            "terms remap schemas, and fractal/heavy-tail markers remain diagnostics."
        ),
        "extracted_equation_count": len(equations),
        "folded_equation_count": len(folded_equations),
        "equations": equations,
        "folded_equations": folded_equations,
        "fold_in_decision": [
            "keep harmonic bases as candidate transforms, not proof",
            "count boundary code, bulk commitment, memory kernel, history window, residual, and witness bytes",
            "reject unbounded fractional kernels as NaN0",
            "require rollback before recursive graph updates promote",
            "treat fractal and heavy-tail terms as pruning diagnostics only",
            "promote only through exact decode/hash/measured-byte closure",
        ],
        "claim_boundary": (
            "This is a local equation fold over user-supplied literature synthesis. "
            "It is not a derivation of the cited papers, not a biological proof, "
            "and not evidence of compression improvement without local byte tests."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_extracted_equation",
            "input": "equation from holographic/fractional/recursive connectome literature",
            "target": "harmonic, boundary_bulk, fractional_memory, recursive_update, atlas_remap, adversarial_invariance, fractal_marker, heavy_tail, or reconfiguration_objective",
        },
        {
            "task": "fold_equation_into_route_state",
            "input": "source-shaped equation",
            "target": "DD state fields plus receipt obligations",
        },
        {
            "task": "reject_hidden_math_payload",
            "input": "boundary code, memory kernel, or recursive state with uncounted payload",
            "target": "NaN0 or invalid receipt",
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    print(json.dumps({
        "receipt": str(RECEIPT.relative_to(REPO)),
        "curriculum": str(CURRICULUM.relative_to(REPO)),
        "receipt_hash": receipt["receipt_hash"],
        "source_receipt_hash": receipt["source_receipt_hash"],
        "extracted_equation_count": receipt["extracted_equation_count"],
        "folded_equation_count": receipt["folded_equation_count"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
