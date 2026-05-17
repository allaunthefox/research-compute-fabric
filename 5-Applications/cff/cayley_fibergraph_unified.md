# Cayley Fibergraph × Braid/Rope × PIST/NUVMAP — Unified Framework

## Summary

Compression as lawful symbolic motion on a finite transformation fiber. Every
symbol becomes a group element, every transition becomes a braid crossing or
rope twist, every state becomes a product-fiber figure, and every memory
allocation point becomes a NUVMAP coordinate in the group's spectral manifold.

## The Four Layers

```
Symbol stream (ACGT...)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: GROUP ASSIGNMENT                                    │
│                                                              │
│   s_i ∈ Σ  →  g_i ∈ G                                       │
│                                                              │
│   For DNA: G = V₄ (Klein four-group)                        │
│   A→(1,0)  C→(x,0)  G→(1,z)  T→(x,z)                       │
│                                                              │
│   Complement (A↔T, C↔G) = z-axis flip = involution           │
│   Transition (A→G) = xy-plane rotation = σ operator          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: BRAID/ROPE FIBER ENCODING                           │
│                                                              │
│   g_{i+1} = a_i · g_i    where a_i ∈ A ⊂ G is the ACTION    │
│                                                              │
│   Braid (Artin B_n):                                         │
│     a_i = σ_k     (swap strands k and k+1)                   │
│     a_i = σ_k^{-1} (reverse swap)                            │
│     Relations: σ_i σ_j = σ_j σ_i (|i-j|>1)                  │
│               σ_i σ_{i+1} σ_i = σ_{i+1} σ_i σ_{i+1}         │
│                                                              │
│   Rope (multicolor):                                         │
│     a_i = (strand_j, color_k, twist_ℓ)                       │
│     twist ∈ {+1, -1, 0} = overpass/underpass/straight        │
│     color ∈ palette  = semantic category tag                 │
│                                                              │
│   COMPRESSION: store ACTION sequence, not STATE sequence      │
│   H(a_0, a_1, ..., a_n) < H(g_0, g_1, ..., g_n)             │
│   when G matches the latent symmetry of the data              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: CAYLEY FIBERGRAPH PROJECTION                        │
│                                                              │
│   Each g ∈ G has a visual fiber F_g:                         │
│     F_g = { edges from g to neighbors in Cayley graph }      │
│                                                              │
│   Cayley distance from identity:                             │
│     d_G(e, g) = minimum word length σ_{i1}···σ_{ik} = g      │
│                                                              │
│   Spectral coordinate (from graph Laplacian L_G):            │
│     v_g = λ_k · φ_k(g)                                       │
│     where (λ_k, φ_k) is the k-th eigenpair of L_G            │
│                                                              │
│   Mass-number (recoverability weight):                       │
│     μ(g) = |orbit(g)| · log₂(|G|)                            │
│     where orbit(g) = { xg : x ∈ G } is the action orbit      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: NUVMAP ADDRESS PROJECTION                           │
│                                                              │
│   NUVMAP_G(g_i) = (u_i, v_i, m_i, F_{g_i})                  │
│                                                              │
│   u_i = d_G(e, g_i)        Cayley-graph radius (address x)   │
│   v_i = spectral_coord_i   Laplacian eigenmode (address y)   │
│   m_i = μ(g_i)             recoverability mass (z-weight)    │
│   F_{g_i} = fiber(g_i)     visual product-fiber (color)      │
│                                                              │
│   Storage allocation: q_i ∝ m_i / (r_i + ε)                  │
│   High-orbit elements → more qubits, low-orbit → sparse       │
└──────────────────────────────────────────────────────────────┘
```

## The Compression Hypothesis

```
C_fiber(S; G) = encode( g_0, (a_0, a_1, ..., a_{n-1}), NUVMAP_G(g_i) )

where:  g_0      = initial group element (log₂|G| bits)
        a_i      = action update from g_i to g_{i+1}
        g_{i+1}  = a_i · g_i   (Cayley table lookup)

Goal:    |C_fiber(S; G)| < |C_naive(S)|
         H(action_stream) < H(symbol_stream)

when G matches the latent symmetry of the source.
```

## FAMM Routing Through the Fibergraph

```
FAMM_{t+1} = bind( FAMM_t, F_{a_t · g_t}, Δ_fiber )

where:  FAMM_t       = current memory policy state
        F_{a_t·g_t}  = product-fiber of current element
        Δ_fiber       = cost of transition (Cayley distance × braid complexity)
        bind          = lawful symbolic transform (preserves invariant)
```

## DNA-Specific Instantiation

```
G_DNA = V₄ (Klein four-group, order 4)
  e = (0,0,0)  — identity
  a = (1,0,0)  — A (adenine)            a² = e
  b = (0,1,0)  — C (cytosine)           b² = e
  c = (0,0,1)  — G (guanine)            c² = e
  abc = (1,1,1) — T (thymine)           (abc)² = e

  Complement pairs:  A↔T  = a ↔ abc   (z-axis flip)
                      C↔G  = b ↔ c     (x-axis flip)

  Braid encoding:
    symbol ACGT → group (a, b, c, abc)
    transition a→b = σ_1 (forward crossing)
    transition b→a = σ_1^{-1} (reverse crossing)
    complement = σ_c (twist operator)

  Rope encoding:
    Each base = colored strand: A=red, C=blue, G=green, T=yellow
    Complement = same strand, opposite twist (±1)
    Codon = 3-strand braid word with color twist
```

## Eigenvalue Verification (the Compressor Manifold)

26+ lossless compressors applied to 31 genetic sequences. The cross-compressor
NCD correlation matrix decomposes into:

1. **Structural cluster** (brotli/zstd/xz/bzip2/lzma/7z): λ₀ dominates,
   high family separation (Δ > 0.4). These compressors see the group structure.

2. **Fast cluster** (lz4/lzop/lzo/pigz): low λ₀, near-zero separation.
   These compressors are structurally blind — they flatten the fibergraph.

3. **Spectral cluster** (flac/wavpack/png/jpeg-xl): transform-based tools
   map DNA bases to frequency/color space. Their eigenvalues differ from
   the structural cluster because they encode spatial relationships, not
   sequential patterns.

The eigenvector manifold position of each compressor IS its fibergraph
signature — how it projects the 31-sequence corpus through its compression
operator.

## Lean/Coq Verification Targets

1. `∀ g ∈ V₄, g² = e` — all non-identity elements are involutions (complement = involution)
2. `mass(k, t) = mass(mirror(k, t))` — PIST mass preserved under mirror (braid relation σ_i σ_i^{-1} = e)
3. `d_G(e, a·b) ≤ d_G(e, a) + d_G(e, b)` — triangle inequality in Cayley graph (routing cost bound)
4. `λ₁(L_G) > 0` iff G is connected — spectral gap = existence of fibergraph structure
5. `NUVMAP(g) = NUVMAP(g^{-1})` iff g is an involution — address symmetry ↔ group property
