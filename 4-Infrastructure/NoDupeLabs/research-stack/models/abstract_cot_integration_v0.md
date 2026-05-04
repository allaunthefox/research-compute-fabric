# Abstract-CoT Paper Integration v0

## Status

```yaml
status: HOLD
source_type: paper_equation_integration
paper: Thinking Without Words: Efficient Latent Reasoning with Abstract Chain-of-Thought
route_signature: models/abstract-cot/integration/v0
authority_scope: external_literature_context_and_candidate_equation_pack
proof_status: sketch_until_local_files_verified
```

## Integration summary

The Abstract-CoT paper contributes six equation families to the Research Stack equation map:

| ID | Equation | Role |
|---|---|---|
| `Abstract_CoT_Marginal_Likelihood` | `p(y|x) = Σ_z p(y|z,x)p(z|x)` | latent-path marginalization |
| `Abstract_CoT_Constrained_Decoding` | `πθ^abs(a|h) = πθ(a|h) * 1[a∈A] / Σ_{u∈A} πθ(u|h)` | constrained action/projection policy |
| `Abstract_CoT_Information_Bottleneck` | `I(Y;C) ≤ I(Y;Z_abs) ≤ I(Z_abs;C)` | latent bottleneck / data-processing guard |
| `Abstract_CoT_Power_Law_Distribution` | `p(token) ∝ token^{-α}` | symbolic-token heavy-tail prior |
| `Abstract_CoT_GRPO_Advantage` | `A_k = (R_k - μ) / σ` | normalized group-relative reward signal |
| `Abstract_CoT_Compression_Ratio` | `compression_ratio = E[|c_verbal|] / E[m]` | latent-vs-verbal compression measure |

## Forest interpretation

```text
verbal chain-of-thought
→ compressed latent reasoning state
→ constrained abstract action space
→ bottlenecked information channel
→ decoded answer / policy output
```

The strongest bridge into the existing Research Stack is the information bottleneck road:

```text
C = verbal/context carrier
Z_abs = compressed abstract latent chain
Y = answer/task target

C → Z_abs → Y
```

If this Markov structure holds, the data-processing inequality gives the intended guard:

```text
I(Y;C) ≤ I(Y;Z_abs) ≤ I(Z_abs;C)
```

This should remain a HOLD until the Lean formalization verifies the assumptions actually encoded in `EntropyMeasures.lean`.

## Lean placement

Expected Lean file integration:

```text
EntropyMeasures.lean
```

Expected additions:

```text
mutualInformation
informationBottleneck
```

Expected dependency relation:

```text
KL divergence / entropy / JSD
→ mutual information
→ data processing inequality
→ information bottleneck guard
```

## Research Stack routes

### Route 1 — Latent marginalization

```text
latent variable z
→ marginalize paths
→ answer likelihood p(y|x)
```

Outcome: HOLD.

### Route 2 — Constrained abstract decoding

```text
full policy πθ
→ abstract allowed action set A
→ renormalized constrained policy πθ_abs
```

Outcome: HOLD.

### Route 3 — Bottleneck / compression

```text
context C
→ abstract latent Z_abs
→ target Y
→ mutual-information inequalities
```

Outcome: high-priority HOLD because it directly connects compression, latent reasoning, and entropy measures.

### Route 4 — Power-law token prior

```text
token rank / token symbol
→ heavy-tailed probability mass
→ compression asymmetry
```

Outcome: HOLD; requires baseline checks to avoid false numeric pattern attraction.

### Route 5 — GRPO advantage

```text
reward samples R_k
→ group mean μ
→ group standard deviation σ
→ normalized advantage A_k
```

Outcome: HOLD; useful bridge into route weighting and policy update logic.

### Route 6 — Compression ratio

```text
verbal CoT length
→ latent abstract token count
→ compression_ratio
```

Outcome: HOLD; useful measurement candidate for Hutter/compression route.

## Authority boundary

```text
paper equation → external light source
Lean formalization → candidate proof object only if assumptions are explicit
numeric similarity → no basin
compression gain → no truth claim
```

The paper can illuminate the map. It cannot by itself promote a basin.

## Immediate validation gates

1. Verify `MATH_MODEL_MAP.tsv` contains the six equation IDs.
2. Verify `EntropyMeasures.lean` compiles after adding `mutualInformation` and `informationBottleneck`.
3. Check whether the Lean bottleneck theorem assumes an explicit Markov chain `C → Z_abs → Y`.
4. Route the six equations through Semantic Number Pattern Search.
5. Add the bottleneck road to the forest as HOLD, not basin.
6. If compilation fails, classify as SCAR: `abstract_cot_entropy_formalization_compile_failure`.

## Notes

This integration is important because it bridges:

```text
compression
latent reasoning
policy restriction
entropy / information measures
route weighting
```

That makes it relevant to the Hutter/compression road, but only after the assumptions are made explicit.
