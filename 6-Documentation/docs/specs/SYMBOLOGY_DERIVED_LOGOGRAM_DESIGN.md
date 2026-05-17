# Symbology-Derived Logogram Design

Status: Draft v0.1
Date: 2026-05-08
Scope: lawful extraction of symbol-density principles into original Omindirection atoms
Claim state: design and compiler contract; not a copyright opinion, cultural claim, compression benchmark claim, or endorsement of copying glyph systems

## 1. Purpose

This document defines the safe quarry rule for dense symbolic systems.

The goal is not to copy scripts, glyphs, alphabets, or fictional symbol sets.
The goal is to extract compression principles and visual grammars, then reissue
them as original, receipted Omindirection atoms.

Canonical rule:

```text
borrow the compression principle
not the protected symbol identity
```

Lawful path:

```text
source symbology
  -> extracted design grammar
  -> original Omindirection atom
  -> payload hash
  -> explicit direction/chirality/phase/placement
  -> residual policy
  -> receipt
  -> byte-savings witness
```

Formal anchor:

```text
0-Core-Formalism/lean/Semantics/Semantics/SymbologyBorrowing.lean
```

## 2. Source Classes

| Source Class | Targets | Borrowed Principle |
|---|---|---|
| Array languages | APL, J, K/Q, BQN, Uiua | dense one-symbol transforms, rank, tacit composition |
| Code-golf languages | 05AB1E, Jelly, GolfScript, Pyth | custom code pages, implicit arguments, opcode density |
| Math notation | logic, set theory, tensors, category notation | relation families, proof/status operators, binding glyphs |
| Shorthand systems | Pitman, Gregg, Teeline, Tironian notes | omission plus residual recovery, phrase collapse |
| Logographic systems | Hanzi, Kanji, hieroglyphic systems, Blissymbolics | radicals, determinatives, concept composition |
| Syllabaries and featural scripts | Hangul, Cherokee, Canadian Aboriginal Syllabics, Yi, Vai | compact syllable packets, feature-bearing shape |
| Ancient scripts | Cuneiform, Linear B, Ogham, Runes, Mayan glyph clusters | block atoms, positional clusters, class marks |
| Constructed or fictional scripts | mode-based or fictional alphabets | mode remapping, phase, chirality, stroke grammar |
| Specialist symbol systems | alchemy, astrology, music, chess, IPA | domain-specific compact vocabularies |

These classes are inspiration surfaces only. They do not grant the resulting
atom semantic authority, legal clearance, cultural authority, or compression
competitiveness.

## 3. Borrowable Principles

Allowed principles:

| Principle | Use |
|---|---|
| `denseOperator` | one atom invokes a high-dimensional transform |
| `modifierFamily` | base atom plus modifier changes arity, mode, or route |
| `customCodePage` | compact byte identity separate from display glyph |
| `residualOmission` | omitted material is recovered by a sidecar |
| `radicalComposition` | smaller atoms compose into a concept family |
| `syllablePacket` | multiple low-level units become one packet atom |
| `semanticDeterminative` | class mark narrows interpretation without replacing payload |
| `phaseChiralityGrammar` | orientation carries structural metadata |
| `domainNotation` | specialist compact marks become domain atoms |

Forbidden shortcut:

```text
literal glyph copy -> payload identity
```

The glyph is always an optional view. The payload is the recoverable canonical
object.

## 4. Omindirection Atomization

Every borrowed principle must become an internal atom:

```yaml
symbol_id:
semantic_key:
canonical_payload:
payload_hash:
glyph:
direction:
chirality:
phase:
placement:
residual_sidecar:
receipt_hash:
decision:
```

The source system may explain why the atom exists. It does not define what the
atom means. Meaning and recovery come from the internal payload and receipt.

## 5. Extraction Ladder

```text
1. Mine symbol family
2. Identify compression principle
3. Reject literal glyph identity as payload
4. Convert to original Omindirection atom
5. Assign byte-code or compact route ID
6. Attach expert behavior or transform semantics
7. Add residual repair path
8. Emit receipt
9. Promote only if byte accounting wins
```

## 6. Byte Law

The byte law is:

```text
B(atom)
+ B(dictionary/reference state)
+ B(thresholds or mode parameters)
+ B(residual)
+ B(receipt)
< B(baseline)
```

If the inequality fails, the symbol may still be useful for display or
inspection, but it is not a compression promotion.

Lean-facing predicate:

```text
byteLawHolds atomBytes dictionaryBytes thresholdBytes residualBytes receiptBytes baselineBytes
```

## 7. Initial Quarry

Start with these because they expose dense structure without forcing literal
glyph reuse:

```text
APL
BQN
Uiua
J
K/Q
05AB1E
Jelly
Mathematical Operators
Supplemental Mathematical Operators
IPA
Pitman shorthand
Gregg shorthand
Blissymbolics
Egyptian hieroglyphic sign organization
Alchemical-symbol organization
Tengwar-like shape grammar
Canadian Aboriginal Syllabics
Nushu
Ogham
Runes
Cuneiform
```

For fictional and culturally specific systems, the default is stricter:

```text
extract mode/chirality/feature grammar only
do not copy literal glyphs
do not imply cultural ownership or equivalence
```

## 8. Compiler Gate

The compiler must reject or hold any borrowed-symbol candidate unless:

1. The atom is original to the internal registry.
2. Protected glyph identity is not copied into payload identity.
3. Payload hash is declared.
4. Direction is declared.
5. Chirality and phase are declared.
6. Placement is declared.
7. Residual policy is declared.
8. Receipt hash is declared.
9. Compression promotion has a byte-savings witness.

Lean gates:

```text
borrowedSymbologyLawful
borrowedSymbologyPromotable
copiedGlyphBlocksLawfulBorrow
promotableBorrowIsLawful
```

## 9. Relation To Candidate Dictionaries

Symbology-derived atoms should feed the vectorless candidate dictionary as
internal payloads, not as external glyph borrowings.

```text
borrowed principle
  -> original atom payload
  -> candidate dictionary entry
  -> selectCandidate range reference
  -> replay receipt
```

This lets dense symbol design improve the sidecar stream without introducing
embedding vectors or unreceipted visual identity.

## 10. Claim Boundary

This design borrows symbology as compression physics:

```text
symbol density
+ orientation
+ phase
+ composition
+ domain shorthand
+ residual repair
```

It does not copy protected glyphs, prove compression wins, define cultural
meaning, or replace legal review for a public glyph set. Public-facing glyph
design should use original marks or cleared open resources.
