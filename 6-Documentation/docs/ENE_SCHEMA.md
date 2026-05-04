# ENE Substrate: Technical Specification & Schema

**Status:** PROJECT DATA / REFERENCE  
**Cross-reference:** `BRAIN_AS_MANIFOLD.md`, `FPGA_WARDEN_NODE_SPEC.md`

## 1. Overview
The Effective Neural Engine (ENE) Substrate is a meta-topological storage system designed to map knowledge domains into a hyperbolic semantic manifold. Unlike traditional relational databases, ENE treats data as "packages" with specific settlement states and semantic vectors.

## 2. Primary Schema: `packages` Table
The core of the system is the `packages` table in `data/substrate_index.db`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `pkg` | TEXT | Unique identifier (Namespace/Name). |
| `version` | TEXT | ISO-8601 version string. |
| `tier` | TEXT | Epistemic layer: `CORE`, `INFRA`, `RESEARCH`. |
| `domain` | TEXT | Knowledge domain (e.g., `neural_manifold`). |
| `archetype` | TEXT | Content class (e.g., `chat_session`, `spec`). |
| `description` | TEXT | Human-readable snippet or summary. |
| `tags` | JSON | Array of strings for discovery. |
| `source` | TEXT | Provenance identifier (e.g., `YourAIScroll`). |
| `sha256` | TEXT | Content integrity hash. |
| `indexed_utc` | TEXT | Ingestion timestamp. |
| `concept_anchor` | JSON | **The Lineage Tag.** Tracks the idea's "Settlement State". |
| `concept_vector`| JSON | 14-dimension coordinate in the hyperbolic manifold. |
| `idea_weights` | JSON | Conceptual density scores (0.0 - 1.0). |
| `analog_map` | JSON | Pre-computed local analog translations between domains. |

## 3. The Concept Anchor (Lineage)
The `concept_anchor` tracks how "settled" an idea is. All imports from YourAIScroll default to `SEED`.

### Resolution Levels:
- **SEED**: Raw intuition, undefined edges.
- **FORMING**: Actively developing, shifting boundaries.
- **STABLE**: Well understood, theoretical framework complete.
- **CRYSTALLIZED**: Fully settled, ready for manifold compression.
- **COMPRESSED**: Encoded into core DSP/FPGA logic via the **Manifold-Blit Operator** ($\oplus$).

## 4. Manifold Geometry
ENE assumes a hyperbolic geometry ($K < 0$) for semantic storage.
- **Direction = Meaning**: The direction of the `concept_vector` encodes the semantic cluster.
- **Magnitude = Activation**: Magnitude represents the conceptual importance or activation frequency.

### 4.1 Semantic Axis Mapping (14D)
The vector space follows a $\phi^{-i}$ weighted axis scaling (Axis 0 = 1.0, Axis 13 $\approx$ 0.002).

| Axis | Weight ($\phi^{-i}$) | Semantic Focus |
| :--- | :--- | :--- |
| 0 | 1.000 | **Substrate / Entropy / Foam** (General Existence) |
| 1 | 0.618 | **Compression / Information Theory** |
| 2 | 0.382 | **Physics / Thermodynamics / Energy** |
| 3 | 0.236 | **Neural / Cognitive / Manifold** |
| 4 | 0.146 | **Formalization / Lean / Logic** |
| 5 | 0.090 | **Markets / Economic / MEV** |
| 6 | 0.056 | **Safety / Alignment / Audit** |
| 7 | 0.034 | **Attestation / Provenance / Cryptography** |
| 8 | 0.021 | **Hardware / FPGA / Warden** |
| 9 | 0.013 | **Signal / DSP / Carriers** |
| 10 | 0.008 | **Synthesis / Bioinfo / DNA** |
| 11 | 0.005 | **Decisions / Pathing / Planning** |
| 12 | 0.003 | **Archive / Historical / Lineage** |
| 13 | 0.002 | **Sovereignty / Identity / Self** |

## 5. Plugin Integration (YourAIScroll)
The `POST /ingest` endpoint bridges external AI insights into this substrate.
- **Targeting**: Use `"target": "ene"` in the payload.
- **Auto-Mapping**: Titles are slugified into `aiscroll/` package names.
- **Default Tier**: All browser exports are assigned the `RESEARCH` tier.

## 6. Linear-ENE Bridge
Every ENE ingestion via the `/ingest` endpoint automatically creates a tracking issue in your **Linear** project space.
- **Traceability**: The Linear Issue URL is stored in the `session_id` column of the `packages` table.
- **Context**: The issue description contains a reference back to the ENE package name.
- **Settlement Control**: Use Linear to track the evolution of a `SEED` concept as it moves toward `CRYSTALLIZED` status.

## 7. Protocol Inheritance Law
...
- **Distributed Availability**: Once verified, the protocol becomes a first-class citizen of the manifold, available for local execution on any node without further attestation.

## 8. $\varphi$-Weighted Manifold Flag Sort
The system uses a 3-way partition logic to autonomously order research trajectories based on their **Metatyping Invariant ($\Sigma$)**.

| Flag | Condition ($\Sigma$) | Technical Regime |
| :--- | :--- | :--- |
| **Red Flag** | $\Sigma < 4.0$ | **DRIFT**: Unlawful or noisy signal; quarantined. |
| **White Flag** | $4.0 \le \Sigma < 10.0$ | **FORMING**: Questionable but potentially interesting; review required. |
| **Blue Flag** | $\Sigma \ge 10.0$ | **CRYSTALLINE**: Verified truth; stable in the manifold. |

- **Topological Pivot**: The partitioning threshold is derived from the **Golden Stratum Gate ($\phi$)**.
- **Recursive Depth**: Within the Blue Flag group, data is further sorted along the 14 axes of the manifold.

## 9. Thermodynamic N-Space Partition (Landauer Sort)
Replacing the purely mathematical heuristic ($\phi$), the system utilizes a **Universal Physical Constant**—the **Boltzmann Constant ($k_B$)** via the **Landauer Limit ($W \ge k_B T \ln 2$)**—to physically partition the N-space based on Informatic Stress and entropy generation.

| Thermodynamic Flag | Substrate State | Technical Regime |
| :--- | :--- | :--- |
| **Dissipative** | High Entropy Loss | **UNLAWFUL**: Fails the Landauer bound; quarantined. |
| **Reversible** | Adiabatic Shift | **REVIEW**: Marginal energy cost; requires proof. |
| **Landauer** | Optimal Coherence | **VERIFIED**: Hits the physical limit of efficiency; stable. |

- **Physical Grounding**: By mapping trajectory quality ($\Sigma$) to thermodynamic depth, the system ensures that data ordering is not just mathematically sorted, but constrained by the fundamental energy limits of computation.

---
*Generated by Gemini CLI - April 2026*
