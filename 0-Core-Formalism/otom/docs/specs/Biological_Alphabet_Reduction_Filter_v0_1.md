# Biological Alphabet Reduction Filter v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This is an OTOM/GCL interpretation of a reported Ec19-style biological alphabet-reduction result. It is a research filter and evidence-mapping spec, not a claim that a true 19-amino-acid organism has been created.

## Source boundary

The relevant report describes an engineered *E. coli* strain in which AI-guided protein design removed isoleucine from many ribosomal proteins. The article explicitly states that the strain is not a true 19-amino-acid organism because isoleucine remains broadly present elsewhere in the genome.

The spec therefore treats the result as:

```text
partial subsystem alphabet reduction
not global organism-level alphabet deletion
```

## Core thesis

A biological translation subsystem can sometimes tolerate deletion of one canonical symbol when an adapter process supplies compensatory structural edits.

In OTOM terms:

```text
symbol deletion
→ structural adapter search
→ local edit validation
→ composition test
→ fitness / stability receipt
```

## GCL mapping

| Biological event | GCL / OTOM interpretation |
|---|---|
| 20 amino acid alphabet | Source alphabet |
| Remove isoleucine from ribosomal proteins | SymbolDeletion |
| Replace with leucine/valine plus nearby edits | AdapterMap / compensatory embedding |
| Individual edits pass fitness gate | PassesLocalGate |
| Combined edits initially kill cells | local_passes does not imply global_passes |
| Manual debugging of lethal interactions | AdversarialTrial / contra-surface repair |
| Final strain maintains high fitness | provisional composition receipt |
| 450 generations without reversion | stability receipt |
| Isoleucine remains elsewhere in genome | lambda-scale boundary |

## Δφγλ reading

```text
Δ = fitness loss, folding error, assembly mismatch, lethal interaction, reversion pressure
φ = preserved ribosomal protein function, fold, interface, translation viability
γ = alphabet-reduction pressure imposed by deleting isoleucine
λ = ribosomal-protein subsystem, not whole genome
```

The important compression lesson is:

```text
alphabet compression is lawful only when φ survives under declared γ at declared λ with bounded Δ
```

## Required Warden gates

### Gate 1 — Domain boundary

Blocked claim:

```text
Ec19 is a 19-amino-acid organism.
```

Allowed claim:

```text
Ec19-style engineering demonstrates partial isoleucine removal in a ribosomal-protein subsystem.
```

### Gate 2 — Local/global distinction

Blocked claim:

```text
Every local edit works, therefore the composed organism works.
```

Allowed claim:

```text
Local edit viability must be re-tested under composed-system constraints.
```

### Gate 3 — Compensation requirement

Blocked claim:

```text
A deleted symbol can simply be replaced by its nearest neighbor.
```

Allowed claim:

```text
A deleted symbol may require compensatory edits distributed across the local structural context.
```

### Gate 4 — Stability receipt

Promotion above `BEAUTIFUL_PROVISIONAL` requires:

```text
fitness receipt
composition receipt
stability / generation receipt
source provenance
scope declaration
```

## Lean artifact

This spec is paired with:

```text
tools/lean/Semantics/Semantics/AlphabetReduction.lean
```

The Lean module encodes:

```text
AminoAcid
Alphabet
SymbolDeletion
LocalEdit
ComposedEdit
PassesLocalGate
PassesCompositionGate
AlphabetReductionResult
```

Its key theorem is:

```text
local_viability_does_not_imply_composed_viability
```

Meaning:

```text
there exists a composed edit batch where each local edit passes but the full composition fails
```

That theorem captures the central anti-overclaiming lesson.

## Non-goals

This spec does not claim:

```text
life only needs 19 amino acids
Ec19 is globally alphabet-reduced
AI has solved whole-genome redesign
local protein design is enough for organism design
biological analogy proves GCL
```

## Strongest formulation

The useful claim is:

> Partial biological alphabet reduction is possible when symbol deletion is paired with structural compensation and composition-level validation.

That is the part OTOM should absorb.
