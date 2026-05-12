# Omindirection Logogram Design and Compiler

Status: Draft v0.2
Date: 2026-05-08
Scope: system-agnostic design for oriented symbolic atoms, compiler validation, reversible projection, receipts, and implementation adapters
Claim state: first-principles design contract; not a theorem of symbolic truth, compression ratio, renderer correctness, or hardware behavior

## 1. Purpose

This document defines Omindirection from first principles.

Omindirection is a system-agnostic contract for encoding a symbolic payload as an oriented, placed, receipted atom. It does not depend on Typst, Lean, TiddlyWiki, GCCL, RRC, Tang9K, or any specific renderer or compiler. Those systems are adapters that may implement the contract.

The design problem is:

```text
Given a symbolic payload that may be read, projected, mirrored, placed,
compressed, rendered, or quarantined, preserve enough metadata to recover what
the payload is, how it is oriented, where it was placed, what was lost, and why
the projection was trusted or rejected.
```

The output of the design is an **omindirectional atom**:

```text
payload
+ identity
+ orientation
+ handedness
+ phase
+ position
+ status
+ residual policy
+ receipt
```

## 2. First Principles

Omindirection follows nine first principles.

### Principle 1: Payload Is Not Presentation

A symbolic payload and its visual rendering are different objects.

```text
payload != glyph != rendered layout
```

The payload must remain recoverable even if a renderer, font, language engine, display, transport, or hardware target changes.

### Principle 2: Direction Is Not Handedness

Flow direction and chirality are different axes.

```text
direction = how an atom flows through a carrier
chirality = how an atom is handed, mirrored, or phase-oriented
```

Left-to-right text does not imply left chirality. Right-to-left text does not imply right chirality.

### Principle 3: Chirality Is a Projection of Phase

Left/right handedness is a coarse view. The durable field is a cyclic phase.

```text
phase in Z/360Z
```

Chirality classes are derived or checked against phase:

```text
none         -> phase 0
left         -> phase 0..179
right        -> phase 180..359
ambidextrous -> any phase 0..359
```

### Principle 4: Position Is State, Not Decoration

Position is not merely where a renderer happened to put a mark. Position is a declared state field.

```text
position = placement kind + coordinate + local constraints
```

Moving an atom may change adjacency, mirror role, capture status, admissible continuations, or quarantine lane.

### Principle 5: Loss Must Be Declared

Any non-round-trip projection must declare its residual.

```text
rounded payload
+ residual sidecar
+ rehydration rule
```

Silent loss is invalid.

### Principle 6: Trust Requires Receipts

A trusted atom needs identity and provenance evidence.

```text
payload hash
+ source hash
+ receipt hash
```

No renderer output alone is a receipt.

### Principle 7: Adapters Are Views

Concrete systems are adapters over the atom contract.

```text
Typst view
Lean formal gate
TiddlyWiki card
JSON receipt
hardware packet
database row
SVG/PDF/HTML display
```

No adapter is the definition of Omindirection.

### Principle 8: Canonical Whitespace Is Derived, Not Stored

Ordinary inter-symbol whitespace is not payload identity when it can be
derived from symbol count and grammar state.

```text
symbol_0 symbol_1 symbol_2
  -> payload symbols: [symbol_0, symbol_1, symbol_2]
  -> derived boundaries: 2
  -> stored whitespace codes: 0
```

The canonical rule is:

```text
token order + symbol identity + grammar state -> display boundary
```

For canonical single-space token streams, the compiler stores symbol payloads
and reconstructs one display space between adjacent symbols during replay.
Non-canonical whitespace, including leading spaces, trailing spaces, multiple
spaces, tabs, newlines, layout-sensitive indentation, or poetic/semantic
negative space, is not silently erased. It must declare a residual or remain
HOLD.

Current receipt:

```text
shared-data/data/stack_solidification/whitespace_zero_grammar_probe.json
```

Lean gate:

```text
Semantics.WhitespaceFreeGrammar
```

### Principle 9: The Model Is Not Immune To Drift

Omindirection must apply its own information-theoretic warning to itself.

```text
unchecked substitution
+ sidecar mismatch
+ rounding loss
+ topology-label drift
  -> sub-noticeable residual creep
  -> corrupted replay
```

Bit rot is not only a storage failure. It is any accumulation of small,
unreceipted symbolic differences that stays below ordinary notice until the
inverse path no longer reconstructs the intended payload. The compiler must
treat these differences as residual, HOLD, or QUARANTINE events, not as harmless
presentation variance.

## 3. Abstract Data Model

The minimal abstract atom is:

```yaml
omni_atom:
  identity:
    symbol_id:
    semantic_key:
    canonical_payload:
    payload_hash:
  orientation:
    direction:
    chirality:
    phase:
  placement:
    kind:
    coord:
      x:
      y:
    liberties:
    captured_by:
    territory_id:
expression:
  tone:
  torsion:
  temporal:
  rhythm:
  spectral_mode:
  music_theory:
    pitch_class:
    interval:
    meter:
    tempo:
    mode:
    harmonic_function:
    voice_leading:
    tuning:
  semantic_interpretation:
    literary_device:
    motif:
    genre:
    medium:
    framing:
    montage:
    affect:
    audience_chart:
    anti_music:
    anti_bpm:
    adversarial_phased_audio:
  language:
  residual:
    rounding_rule:
    residual_sidecar:
  rendering:
    glyph:
    render_hint:
  receipt:
    source_hash:
    receipt_hash:
    decision:
```

The canonical atom is the normalized, hashable form of this packet.

## 4. Required Fields

The system-agnostic required fields are:

| Field | Required | Reason |
|---|---:|---|
| `symbol_id` | yes | stable registry identity |
| `semantic_key` | yes | inspectable meaning key |
| `canonical_payload` | yes | source payload before projection |
| `payload_hash` | yes | payload identity |
| `direction` | yes | explicit flow direction |
| `chirality` | yes | explicit handedness class |
| `phase` | yes | durable cyclic orientation |
| `placement.kind` | yes | position semantics |
| `placement.coord` | yes | declared coordinate |
| `placement.liberties` | yes | continuation/capture accounting |
| `placement.captured_by` | yes | capture source or null |
| `placement.territory_id` | yes | semantic basin or lane identity |
| `tone` | yes | status/expression class |
| `torsion` | yes | twist, shear, or binding stress |
| `temporal` | yes | order, recurrence, or pass index |
| `rhythm` | yes | cadence, beat, phonon packet, or recurrence chart |
| `spectral_mode` | yes | frequency/phonon/harmonic mode or null |
| `music_theory` | yes | pitch, interval, meter, harmony, voice-leading, and tuning chart |
| `semantic_interpretation` | yes | literary/media-arts reading chart with anti-music lane |
| `rounding_rule` | yes | rehydration rule or null |
| `residual_sidecar` | yes | residual reference or null |
| `source_hash` | yes | source record identity |
| `receipt_hash` | yes | compiler/validator receipt identity |
| `decision` | yes | ACCEPT, HOLD, or QUARANTINE |

Adapter-specific fields are optional:

| Field | Adapter Use |
|---|---|
| `glyph` | visual glyph, glyph ID, bitmap, vector, opcode, or LED token |
| `render_hint` | renderer-specific expression |
| `language` | natural-language shaping hint |
| `version` | adapter schema version |

Optional adapter fields may expose local drift diagnostics, but drift evidence
must still resolve into the required residual and receipt fields before
promotion.

## 5. Direction Axis

Direction declares flow through a carrier.

Allowed abstract values:

```text
forward
reverse
neutral
auto
```

Reference text adapters may map these to:

```text
forward -> ltr
reverse -> rtl
neutral -> none
auto    -> auto
```

Rules:

1. `auto` is allowed only before promotion.
2. Promoted atoms must have explicit non-auto direction.
3. Direction must not be inferred from language, font, glyph shape, or renderer output.
4. Direction must not imply chirality.

## 6. Chirality and Phase Axis

Chirality declares coarse handedness. Phase declares durable orientation.

Allowed chirality values:

```text
left
right
ambidextrous
none
```

Allowed phase values:

```text
0 <= phase < 360
```

Compatibility:

| Chirality | Valid Phase |
|---|---|
| `none` | `0` |
| `left` | `0..179` |
| `right` | `180..359` |
| `ambidextrous` | `0..359` |

Display prefixes are adapter conventions, not the core model. A reference text adapter may use:

| Chirality | Prefix |
|---|---|
| `left` | `L:` |
| `right` | `R:` |
| `ambidextrous` | `LR:` |
| `none` | empty |

## 7. Placement Axis

Placement declares how an atom inhabits a carrier.

Allowed placement kinds:

```text
row
mirrorLeft
mirrorRight
board
quarantine
```

Rules:

| Placement | Rule |
|---|---|
| `row` | ordered sequence lane |
| `mirrorLeft` | chirality must be `left` or `ambidextrous` |
| `mirrorRight` | chirality must be `right` or `ambidextrous` |
| `board` | must have at least one liberty or a declared capture |
| `quarantine` | decision must be `QUARANTINE` |

Coordinates are integers:

```yaml
coord:
  x: integer
  y: integer
```

Coordinate identity is not payload identity. Payload identity comes from `payload_hash`.

## 8. Local State: Liberties, Capture, Territory

The placement state carries local topology.

```text
liberties    = admissible continuation count
captured_by  = capture source or null
territory_id = stable basin, lane, region, or semantic cluster
```

Rules:

1. Row atoms may have zero liberties.
2. Board atoms with zero liberties must declare `captured_by`.
3. Captured atoms may remain as residual evidence.
4. Uncaptured board atoms with zero liberties are HOLD.
5. Territory is not proof of truth; it is a basin label.

## 9. Expression State

Expression fields modify how an atom is interpreted without changing payload identity.

```text
tone
torsion
temporal
rhythm
spectral_mode
music_theory
semantic_interpretation
language
```

Reference tone classes:

| Tone | Use |
|---|---|
| `witness` | accepted evidence or stable payload |
| `unknown` | unresolved or pre-promotion atom |
| `boundary` | edge, split, interface, or type boundary |
| `residual` | loss, tear, capture, sidecar, or quarantine |
| `growth` | active target, search frontier, or expansion |
| `neutral` | display-only or low-status atom |

Torsion is a signed or unsigned stress/twist value. Temporal is an order,
recurrence, pass, or corpus-time value. Rhythm is the cadence chart: it carries
beat, meter, recurrence interval, phonon packet cadence, or symbolic timing.
`spectral_mode` is the frequency/harmonic/phonon lane associated with that
cadence. `music_theory` is the structured adapter chart for pitch class,
interval, meter, tempo, mode, harmonic function, voice leading, and tuning.
`semantic_interpretation` is the literary/media-arts chart: motif, genre,
framing, montage, affect, audience chart, anti-music/anti-form signals, and
anti-BPM beat-grid resistance. `adversarial_phased_audio` is a safety lane for
detecting, refusing, or documenting audio/latency feedback patterns that could
disorient a person.
Language is an adapter hint and must not carry semantic authority by itself.

### Semantic / Literary / Media-Arts Interpretation Layer

The semantic layer is an interpretation layer before it is a truth layer. It
routes the same payload through literary and media-arts charts:

```text
payload
+ motif
+ genre
+ medium
+ framing / montage
+ affect / audience chart
+ anti-music or anti-form signal
+ residual interpretation sidecar
+ receipt
  -> route hint, replayable adapter, or HOLD interpretation shadow
```

This layer is useful for:

| Interpretation Surface | Logogram Role |
|---|---|
| motif | repeated semantic pattern or symbolic recurrence |
| theme | high-level pressure field, not proof |
| genre | expectation manifold and admissible continuation chart |
| medium | text, image, audio, film, game, diagram, interface, or performance carrier |
| framing | point of view, crop, narrator, boundary, or observer chart |
| montage / sequence | temporal juxtaposition and causal reading |
| metaphor / allegory | cross-domain adapter candidate |
| affect | emotional/tonal route pressure |
| audience chart | local observer projection and cultural prior |
| anti-music / anti-form | silence, noise, rupture, refusal, broken cadence, negative space |
| anti-BPM patterning | tempo refusal, rubato, missing pulse, broken beat grid, adversarial BPM ambiguity |
| adversarial phased audio | phase/latency feedback, entrainment, response-time manipulation, disorientation risk |

Rules:

1. Interpretation may route a logogram, but may not certify it.
2. Literary/media readings must declare whether they are motif extraction,
   genre routing, formal analysis, audience-chart projection, or residual
   interpretation.
3. Anti-music is a first-class negative-control lane: silence, rupture, noise,
   refusal, and broken cadence are signals, not absence of signal.
4. Anti-BPM is the timing-specific negative-control lane. It records refusal of
   stable tempo, ambiguous beat grids, rubato drift, missing downbeats, pulse
   collapse, polyrhythmic conflict, and adversarial BPM inference.
5. Adversarial phased audio is safety-critical. If a sound, phase relation,
   latency, repetition pattern, or response-time feedback loop is designed or
   suspected to disorient a person, the atom routes to
   `QUARANTINE_ADVERSARIAL_AUDIO` for defensive analysis only.
6. The compiler must not emit tactics, parameter recipes, or optimization
   guidance for disorienting a person with audio or response latency.
7. Anti-music/anti-form/anti-BPM cannot be used to excuse missing replay. It routes to
   `HOLD_INTERPRETATION_SHADOW` unless an adapter reconstructs the payload or
   declares residual loss.
8. Aesthetic elegance, thematic fit, or audience resonance is never a receipt.
9. Protected works, lyrics, scores, film frames, or media glyphs must not become
   canonical payload; only abstracted relations and receipted metadata may be
   carried.

### Phonon / Music Theory / Rhythm Notation Layer

Phonon, music theory, prosody, and rhythmic notations are admissible
expression-layer charts when they encode recurrence, phase, resonance, cadence,
interval relation, harmonic function, or spectral structure. They are not proof
objects by themselves.

```text
canonical payload
+ rhythm chart
+ spectral mode
+ music-theory chart
+ semantic interpretation chart
+ phase/torsion/temporal fields
+ residual timing sidecar
+ receipt
  -> recoverable payload or declared HOLD shadow
```

This layer is useful for:

| Notation Surface | Logogram Role |
|---|---|
| musical rhythm | cadence, recurrence, parity, timing shadow |
| pitch / harmonic notation | spectral mode and phase relation |
| pitch class | cyclic 12-tone or n-tone residue class |
| interval | distance relation, ratio class, or transformation step |
| meter | periodic grouping and stress pattern |
| tempo | event-rate normalization and timebase conversion |
| anti-BPM | tempo refusal, beat-grid ambiguity, rubato drift, broken pulse |
| mode / scale | allowed pitch basin and tonal chart |
| harmonic function | local role, tension, resolution, cadence |
| voice leading | low-cost transition path between states |
| tuning / temperament | frequency-ratio adapter and quantization rule |
| phonon modes | lattice vibration, resonance, material witness |
| prosody / meter | language rhythm and packet grouping |
| percussion / beat maps | event timing and interval compression |
| waveform staff / piano roll | discrete time-frequency chart |

Rules:

1. Rhythm and spectral notation may route a logogram, but may not certify it.
2. A rhythm chart must declare its clock: temporal time, torsion interval,
   corpus offset, phonon period, or adapter-specific beat.
3. A music-theory chart must declare its coordinate system: equal temperament,
   just intonation, pitch-class modulus, meter, tempo unit, and key/mode when
   relevant.
4. A phonon/music chart must declare whether it is exact, quantized, or a
   mnemonic shadow.
5. Quantized pitch, interval, rhythm, or tuning requires a residual sidecar.
6. Music-sheet or rhythm-only shadows remain `HOLD_SHADOW_ONLY` until the
   adapter reconstructs the canonical payload or declares loss.
7. Protected notation/glyph identity must not become canonical payload; only
   the timing/spectral relation may be borrowed.
8. Voice-leading cost may route a transition, but the receipt must still prove
   that the chosen path reconstructs the intended payload or declare residual
   loss.

## 10. Residual and Rehydration

A lossless atom may set:

```text
rounding_rule: null
residual_sidecar: null
```

A lossy or rounded atom must declare:

```text
rounding_rule
residual_sidecar
```

Rehydration rule:

```text
canonical payload + render/projection fields + residual sidecar
  -> original canonical payload, or declared lossy residual
```

If this rule is missing, the atom is HOLD.

### Residual Creep

Residual creep is the information-theoretic bit rot of the compiler surface.
It includes:

| Creep Mode | Required Handling |
|---|---|
| substitution drift | sidecar op or HOLD |
| candidate ambiguity | explicit `select_candidate` receipt |
| literal/hash collision | literal sidecar or HOLD |
| truncation | `append_truncated_cell` sidecar |
| topology-label drift | residual receipt, HOLD, or QUARANTINE |
| receipt/hash mismatch | HOLD |

The compiler must not smooth residual creep into prose, renderer style, or
semantic confidence. If replay changes, the atom is not accepted.

## 11. Receipt Model

A receipt is the trust boundary.

Minimum receipt fields:

```yaml
receipt:
  source_hash:
  payload_hash:
  receipt_hash:
  checks:
    required_fields:
    payload_hash_match:
    source_hash_present:
    explicit_direction:
    phase_valid:
    chirality_phase_compatible:
    placement_admissible:
    residual_declared:
    receipt_complete:
  decision:
```

Receipt rules:

1. `payload_hash` must be computed from `canonical_payload`.
2. `source_hash` must be computed from the input source record.
3. `receipt_hash` must be computed from the normalized atom and validation result.
4. Supplied hashes must be recomputed or marked externally witnessed.
5. Missing receipt evidence prevents ACCEPT.

## 12. Admission Gate

An atom is ACCEPT only when:

```text
required fields present
+ payload hash matches canonical payload
+ source hash present
+ direction is explicit
+ phase is in range
+ chirality is compatible with phase
+ placement is admissible
+ residual policy is declared
+ receipt is complete
```

Otherwise:

| Condition | Decision |
|---|---|
| recoverable missing evidence | HOLD |
| quarantine lane or destructive tear | QUARANTINE |
| complete and valid | ACCEPT |

## 13. Derived Compiler Pipeline

The compiler follows directly from the principles.

```text
input source
  -> parse
  -> normalize to canonical atom
  -> compute payload hash
  -> compute source hash
  -> validate orientation
  -> validate chirality/phase
  -> validate placement
  -> validate residual policy
  -> generate receipt
  -> decide ACCEPT/HOLD/QUARANTINE
  -> emit adapter views
```

### Phase 1: Parse

Accept any source that can produce the abstract fields:

- table row
- JSON/YAML packet
- symbolic expression
- compiler AST node
- visual glyph registry row
- board-state transition
- database record

### Phase 2: Normalize

Normalize to the abstract atom packet:

- field names become stable snake_case
- missing optional values become null
- phase becomes integer
- coordinates become integer `(x, y)`
- chirality, direction, placement, tone, and decision become enum values
- canonical payload becomes byte-stable

### Phase 3: Hash

Compute:

```text
payload_hash = H(canonical_payload)
source_hash  = H(source_record)
```

The hash algorithm is adapter-configurable, but the receipt must declare it.

### Phase 4: Validate

Validation order:

1. required fields
2. payload hash
3. source hash
4. explicit direction
5. phase bound
6. chirality/phase compatibility
7. mirror placement compatibility
8. board liberty/capture compatibility
9. quarantine lane compatibility
10. residual/rehydration declaration
11. residual creep/replay check
12. receipt completeness

### Phase 5: Decide

Decision rule:

```text
if all gates pass and decision target is ordinary lane:
  ACCEPT
elif quarantine placement or destructive lane is declared:
  QUARANTINE
else:
  HOLD
```

### Phase 6: Emit

Emit:

- canonical atom packet
- receipt packet
- zero or more adapter views

Adapter views must not mutate the canonical atom.

## 14. Error Codes

Stable error codes:

| Code | Meaning | Default Decision |
|---|---|---|
| `OMI_MISSING_FIELD` | required field absent | HOLD |
| `OMI_EMPTY_PAYLOAD` | canonical payload empty | HOLD |
| `OMI_HASH_MISMATCH` | payload hash mismatch | HOLD |
| `OMI_AUTO_DIRECTION` | direction remains auto at promotion | HOLD |
| `OMI_BAD_PHASE` | phase outside 0..359 | HOLD |
| `OMI_CHIRAL_PHASE_CONFLICT` | chirality incompatible with phase | HOLD |
| `OMI_BAD_MIRROR_LEFT` | mirror-left with wrong chirality | HOLD |
| `OMI_BAD_MIRROR_RIGHT` | mirror-right with wrong chirality | HOLD |
| `OMI_DEAD_BOARD_TILE` | board tile has zero liberties and no capture | HOLD |
| `OMI_QUARANTINE_LANE_MISMATCH` | quarantine lane/decision mismatch | QUARANTINE |
| `OMI_UNDECLARED_RESIDUAL` | lossy atom lacks residual rule or sidecar | HOLD |
| `OMI_MISSING_RECEIPT` | source/payload/receipt hash missing | HOLD |
| `OMI_RESIDUAL_CREEP` | sub-noticeable drift changes replay or inverse reconstruction | HOLD |

## 15. System-Agnostic Examples

Accepted row atom:

```yaml
omni_atom:
  identity:
    symbol_id: "ATOM.GAMMA.0001"
    semantic_key: "gamma_witness"
    canonical_payload: "Gamma_i"
    payload_hash: "sha256:..."
  orientation:
    direction: "forward"
    chirality: "ambidextrous"
    phase: 90
  placement:
    kind: "row"
    coord: { x: 0, y: 0 }
    liberties: 0
    captured_by: null
    territory_id: "row-0"
  expression:
    tone: "witness"
    torsion: 0
    temporal: 0
    language: null
  residual:
    rounding_rule: null
    residual_sidecar: null
  rendering:
    glyph: "Gamma"
    render_hint: null
  receipt:
    source_hash: "sha256:..."
    receipt_hash: "sha256:..."
    decision: "ACCEPT"
```

Held board atom:

```yaml
omni_atom:
  identity:
    canonical_payload: "Gamma_i"
    payload_hash: "sha256:..."
  orientation:
    direction: "forward"
    chirality: "ambidextrous"
    phase: 90
  placement:
    kind: "board"
    coord: { x: 2, y: 3 }
    liberties: 0
    captured_by: null
  receipt:
    decision: "HOLD"
    error: "OMI_DEAD_BOARD_TILE"
```

Quarantined atom:

```yaml
omni_atom:
  identity:
    canonical_payload: "semantic_tear"
    payload_hash: "sha256:..."
  orientation:
    direction: "reverse"
    chirality: "right"
    phase: 270
  placement:
    kind: "quarantine"
    coord: { x: 0, y: 0 }
    liberties: 0
    captured_by: "semantic_tear"
  expression:
    tone: "residual"
  receipt:
    decision: "QUARANTINE"
```

## 16. Adapter Contracts

Adapters must preserve the abstract atom.

### Text and Typesetting Adapter

A text renderer may lower:

```text
direction forward/reverse -> ltr/rtl
chirality left/right/ambidextrous -> prefix or style
phase -> visible phase label or hidden metadata
tone -> color/style
placement -> row/grid/board layout
```

The renderer is a view. It is not the validator.

### Formal Verification Adapter

A formal system may encode:

- enum domains
- compatibility functions
- admission predicates
- executable witnesses

The formal adapter should prove at least:

```text
accepted atom has explicit direction
accepted atom has receipt
auto-direction atom is not accepted
dead board atom is not accepted
quarantine atom is routed but not ordinary-accepted
```

### Wiki/Knowledge Adapter

A knowledge-base adapter may emit:

- one card per contract
- one card per accepted atom family
- one card per quarantine family
- backlinks to source and receipt

The card is documentation, not proof.

### Hardware or Packet Adapter

A hardware or packet adapter may emit:

- bounded glyph payload
- sidecar index
- residual lane
- receipt hash
- placement/phase/tone bits

The packet is a transport view, not the canonical atom.

### Database Adapter

A database adapter may store one normalized atom per row. It must preserve:

- canonical payload
- all enum fields
- coordinate fields
- hash fields
- decision
- receipt JSON

## 17. Reference Implementation Mapping

This repository currently contains one reference implementation family. It is not required by the abstract design.

| Abstract Role | Current Adapter |
|---|---|
| formal gate | `0-Core-Formalism/lean/Semantics/Semantics/Omindirection.lean` |
| substitution law gate | `0-Core-Formalism/lean/Semantics/Semantics/LogogramSubstitution.lean` |
| candidate dictionary commit gate | `0-Core-Formalism/lean/Semantics/Semantics/CandidateDictionary.lean` |
| symbology borrowing gate | `0-Core-Formalism/lean/Semantics/Semantics/SymbologyBorrowing.lean` |
| continued fraction compression gate | `0-Core-Formalism/lean/Semantics/Semantics/ContinuedFractionCompression.lean` |
| LadderLUT ordered-ID gate | `0-Core-Formalism/lean/Semantics/Semantics/LadderLUT.lean` |
| HexLogogram Atlas grouping gate | `0-Core-Formalism/lean/Semantics/Semantics/HexLogogramAtlas.lean` |
| Manifold Boundary Atlas RRC candidate gate | `0-Core-Formalism/lean/Semantics/Semantics/ManifoldBoundaryAtlas.lean` |
| substitution audit | `4-Infrastructure/shim/math_logogram_substitution_audit.py` |
| sidecar packer | `4-Infrastructure/shim/math_logogram_sidecar_packer.py` |
| omindirection compiler | `4-Infrastructure/shim/omindirection_logogram_compiler.py` |
| corpus benchmark | `4-Infrastructure/shim/math_logogram_corpus_substitution_benchmark.py` |
| typesetting adapter | `6-Documentation/reports/typst/omindirection.typ` |
| LUT adapter | `typst/registries/symbology-typesetting-lut.typ` |
| wiki contract | `6-Documentation/tiddlywiki-local/wiki/tiddlers/Omindirection Logogram Contract.tid` |
| GCCL integration | `6-Documentation/docs/specs/GCCL_ENCODING_CONTRACT.md` |
| logogram source | `4-Infrastructure/shim/math_logogram_surface_builder.py` |

Reference verification:

```text
cd 0-Core-Formalism/lean/Semantics
lake build Semantics.Omindirection
lake build Semantics.LogogramSubstitution
lake build Semantics.CandidateDictionary
lake build Semantics.SymbologyBorrowing
lake build Semantics.ContinuedFractionCompression
lake build Semantics.LadderLUT
lake build Semantics.HexLogogramAtlas
lake build Semantics.ManifoldBoundaryAtlas
lake build Semantics
```

Expected witness outcomes:

```text
atomAdmissible rowWitnessAtom        = true
atomAdmissible autoDirectionAtom     = false
atomAdmissible mirrorRightAtom       = true
atomAdmissible deadBoardAtom         = false
atomQuarantined quarantineAtom       = true
decideSubstitution literalAtom       = accept
decideSubstitution knownCommand      = hold
decideSubstitution hashedIdentifier  = hold
decideSubstitution truncatedPayload  = hold
decideSubstitution semanticTear      = quarantine
ladderPromotable decimalThreeDigitPacket = true
ladderPromotable tinyLadderPacket        = false
ladderPromotable badBasePacket           = false
atlasPromotable canonicalHexAtlas        = true
atlasPromotable tinyHexAtlas             = false
atlasPromotable badHexBaseAtlas          = false
atlasPromotable badGroupAtlas            = false
boundaryAtlasPromotable canonicalBoundaryAtlas = true
boundaryAtlasPromotable tinyBoundaryAtlas      = false
boundaryAtlasPromotable badBoundaryDomainAtlas = false
boundaryAtlasAloneDoesNotProject              = true
```

## 18. Reference Compiler Shape

A concrete compiler may expose:

```text
omindirection-compile \
  --input source.ext \
  --input-kind lut|json|yaml|ast|board \
  --atom-out atoms.jsonl \
  --receipt-out receipts.jsonl \
  --adapter-out target.ext
```

Minimum outputs:

```text
atoms.jsonl
receipts.jsonl
adapter output, if requested
```

The compiler must be able to run without a renderer.

## 19. Symbology-Derived Logogram Gate

Symbology-derived logograms may borrow density principles from existing notation
systems, but they must not make the borrowed glyph identity into the payload.
The allowed extraction is:

```text
source symbology
  -> design grammar
  -> original Omindirection atom
  -> byte-code / candidate-dictionary route
  -> residual repair
  -> receipt
```

Reference design:

```text
6-Documentation/docs/specs/SYMBOLOGY_DERIVED_LOGOGRAM_DESIGN.md
```

Formal gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/SymbologyBorrowing.lean
```

Byte law:

```text
B(atom)
+ B(dictionary/reference state)
+ B(thresholds or mode parameters)
+ B(residual)
+ B(receipt)
< B(baseline)
```

If the byte law fails, the symbol is display or inspection structure, not a
compression promotion.

The compiler must reject any candidate where:

```text
protected glyph identity -> payload identity
```

The lawful path is:

```text
borrow compression principle
not protected symbol identity
```

## 20. Substitution Audit Gate

## 20A. Continued Fraction Compression Gate

Ratio-heavy logogram metadata may be encoded as continued-fraction packets when
the value can be replayed as an exact numerator/denominator carrier or when a
residual sidecar declares the approximation.

Reference design:

```text
6-Documentation/docs/specs/CONTINUED_FRACTION_COMPRESSION_ADAPTATION.md
```

Formal gate:

```text
0-Core-Formalism/lean/Semantics/Semantics/ContinuedFractionCompression.lean
```

Useful adaptation surfaces:

```text
phi / Fibonacci ratios
golden-angle phase steps
recursive branch-cut ratio ladders
fixed-point thresholds
sidecar byte-law parameters
holographic boundary / bulk ratios
```

Promotion rule:

```text
continued fraction packet promotes
  -> exact rational replay
  -> byte law satisfied
```

Substitution is the first lossless-compression gate. A compiler may replace a
canonical token cell with a bounded glyph payload only when the receipt can
prove how to recover the canonical payload or declares the residual needed to
do so.

The repository audit harness is:

```text
4-Infrastructure/shim/math_logogram_substitution_audit.py
```

It emits:

```text
4-Infrastructure/shim/math_logogram_substitution_audit_receipt.json
```

The audit checks three layers:

1. **Round-trip fidelity**: source is canonicalized to token cells, packed into
   a glyph payload, then reconstructed at canonical-token scope.
2. **Substitution detection**: each token is classified as `known_command`,
   `known_symbol`, `single_char_literal`, or `hashed_multichar_residual`.
3. **GCCL receipt shape**: each fixture records `compression_ratio`,
   `round_trip`, and `residual`.

The audit distinguishes two round-trip scopes:

| Scope | Meaning |
|---|---|
| `payload_only` | glyph bytes alone reconstruct the canonical token string |
| `with_display_cell_sidecar` | glyph bytes plus display-cell sidecar reconstruct the canonical token string |

Current finding:

```text
fixture_count: 5
payload_only_round_trip_count: 1
sidecar_round_trip_count: 5
accept_count: 1
hold_count: 3
quarantine_count: 1
raw_bytes: 120
payload_bytes: 42
json_sidecar_bytes: 5140
packed_sidecar_estimate_bytes: 174
compression_ratio_raw_to_payload: 2.857142857142857
compression_ratio_raw_to_payload_plus_json_sidecar: 0.023157082207641837
compression_ratio_raw_to_payload_plus_packed_sidecar_estimate: 0.5555555555555556
audit_passed: true
```

This means the current compiler is not yet globally payload-only lossless.
Known command and symbol glyph bytes collide with ordinary ASCII byte values,
multi-character unknown identifiers are hashed, and token streams longer than
16 cells are truncated into a bounded payload. Those cases are lawful only when
the receipt declares the residual sidecar, or they remain HOLD. Semantic tears
route to QUARANTINE.

Claim boundary: this audit proves fixture-level residual detection. It does not
prove global losslessness for all math, chemistry, or symbolic strings.

### Sidecar Encoding

The sidecar is structured correction data, not an opaque byte patch. The first
reference sidecar is:

```text
math_logogram_sidecar_v1
```

It uses three correction operations:

| Operation | Meaning |
|---|---|
| `select_candidate` | glyph byte has multiple legal token meanings; choose the canonical token |
| `literal_token` | glyph byte is a hash/residual carrier; store the literal token bytes |
| `append_truncated_cell` | token cell was outside the bounded payload; append the missing cell |

Rehydration rule:

```text
glyph payload
  + sidecar candidate selections
  + sidecar literal tokens
  + sidecar truncated cells
  -> canonical token string
```

The JSON sidecar in the audit receipt is intentionally verbose so the residual
can be inspected. It is not the compression target. The receipt also records a
`sidecar_bytes_packed_estimate` that prices a simple binary envelope:

```text
opcode + token index + glyph/candidate metadata + optional token bytes
```

Current fixture-level packed estimate is still larger than the raw input once
sidecars are included. That is expected on five tiny fixtures. Compression can
only become meaningful when corpus-level reuse lets the sidecar refer to shared
token tables, candidate dictionaries, and repeated residual patterns.

### Omindirection Integration

The reference omindirection compiler treats substitution audit output as an
admission input:

```text
surface canonical cell
  -> substitution audit receipt
  -> omindirectional atom residual fields
  -> atom decision
```

Reference command:

```text
python 4-Infrastructure/shim/omindirection_logogram_compiler.py
```

Outputs:

```text
4-Infrastructure/shim/omindirection_logogram_atoms.jsonl
4-Infrastructure/shim/omindirection_logogram_compiler_receipt.json
```

Mapping:

| Substitution Result | Atom Field Effect |
|---|---|
| `ACCEPT` | `decision = ACCEPT`, `residual_sidecar = null` |
| `HOLD` | `decision = HOLD`, `residual_sidecar = sidecar ref` |
| `QUARANTINE` | `decision = QUARANTINE`, `placement.kind = quarantine`, `tone = residual` |

The atom validator must not promote a substituted payload merely because its
hash exists. Promotion also requires the substitution receipt to prove
payload-only recovery or declare a residual sidecar.

Current compiler output:

```text
atom_count: 5
accept_count: 1
hold_count: 3
quarantine_count: 1
sidecar_ref_count: 4
```

### Benchmark Path

The benchmark path is measurement-first:

```text
corpus
  -> surface compiler
  -> substitution audit
  -> ACCEPT/HOLD/QUARANTINE histogram
  -> payload bytes + packed sidecar estimate
  -> candidate decompressor replay
```

The first corpus target should be a bounded local slice before `enwik8`, because
the sidecar table design needs iteration. A valid benchmark report must include:

1. raw corpus bytes
2. canonical bytes
3. glyph payload bytes
4. JSON sidecar bytes for inspection
5. packed sidecar estimate bytes
6. actual packed sidecar bytes once implemented
7. replay success/failure count
8. ACCEPT/HOLD/QUARANTINE histogram
9. claim boundary

No Hutter Prize claim follows from the fixture audit. The audit only creates the
measurement surface required to test whether a glyph stream plus sidecar stream
can become competitive.

Reference command:

```text
python 4-Infrastructure/shim/math_logogram_corpus_substitution_benchmark.py \
  --slice-bytes 8192 \
  --chunk-chars 160 \
  --max-chunks 64
```

Current bounded `enwik8` slice result:

```text
sample_count: 52
raw_bytes: 8119
canonical_bytes: 9244
payload_bytes: 821
packed_sidecar_estimate_bytes: 25197
payload_plus_packed_sidecar_estimate_bytes: 26018
compression_ratio_raw_to_payload: 9.889159561510354
compression_ratio_raw_to_payload_plus_packed_sidecar_estimate: 0.31205319394265507
accept_count: 0
hold_count: 52
quarantine_count: 0
payload_only_round_trip_count: 0
sidecar_round_trip_count: 52
```

This says the current generic text path is reversible with sidecars, but not
competitive. The ACCEPT rate is zero on this XML-heavy text slice because the
current canonicalizer treats most multi-character text as residual-bearing
tokens. A corpus-scale win would require a reusable dictionary/candidate table,
a real sidecar entropy codec, or a stronger canonicalizer such as the planned
RaTeX/math-specific path for symbolic content.

### Hardware-Safe Packing Path

The hardware path should be simulated before targeting Tang9K:

```text
glyph payload stream
  + sidecar operation stream
  + receipt hash/index stream
  -> packet bitstream
  -> host replay verifier
  -> hardware adapter
```

The bounded 16-byte payload remains a packet constraint. The sidecar stream is
the lawful recovery channel. Expanding the fixed payload is not the first fix;
the first fix is an efficient sidecar codec with replay evidence.

### Candidate Dictionary Commit Gate

The vectorless candidate dictionary is now a formal GCCL-Rep carrier. It is not
an embedding index and not a semantic-nearest-neighbor system. It is an ordered
external token table with committed payload entries and exact range references.

Lean anchor:

```text
0-Core-Formalism/lean/Semantics/Semantics/CandidateDictionary.lean
```

Formal shape:

```text
CandidateEntry
  -> CandidateDict
  -> CandidateSidecarRef(kind, start, length)
  -> replayCandidateRef
  -> CandidateDictCommit
  -> toGcclRepEvent
  -> candidateRefPromotable
```

The reference keeps `SidecarOp` finite. Concrete database range metadata lives
in `CandidateSidecarRef`, so the existing substitution law surface does not need
open string matching or vector lookup.

Verified witnesses:

```text
select_gamma_replays_single_entry
select_pair_replays_two_entries
out_of_bounds_select_replays_none
literal_token_is_not_dictionary_select
example_commit_verified
bad_count_commit_not_verified
bad_entry_commit_not_verified
verified_commit_implies_verified_gccl_rep
replay_some_implies_candidate_ref_admissible
candidate_ref_promotion_implies_commit_verified
candidate_ref_promotion_implies_lawful_transition
```

Reference sidecar packing command:

```text
python 4-Infrastructure/shim/math_logogram_sidecar_packer.py
```

Outputs:

```text
4-Infrastructure/shim/math_logogram_sidecar_stream.bin
4-Infrastructure/shim/math_logogram_sidecar_packer_receipt.json
```

## 21. Compliance Checklist

A system implements Omindirection if it can answer yes to all of these:

1. Does it keep payload identity separate from rendering?
2. Does it encode direction explicitly?
3. Does it encode chirality separately from direction?
4. Does it validate phase bounds?
5. Does it validate chirality/phase compatibility?
6. Does it encode placement separately from renderer layout?
7. Does board placement account for liberties or capture?
8. Does quarantine placement require a quarantine decision?
9. Does it declare residual and rehydration policy?
10. Does it emit source, payload, and receipt hashes?
11. Does it produce ACCEPT/HOLD/QUARANTINE decisions?
12. Can it emit the canonical atom without any specific renderer?
13. Does it detect residual creep before accepting an atom?

## 22. Open Implementation Work

1. Implement a renderer-independent compiler that emits canonical atoms and receipts.
2. Add adapter tests for Typst, JSONL, wiki, and packet views.
3. Add round-trip tests from canonical atom to adapter view and back.
4. Add a board helper adapter for visual placement.
5. Add receipt hashing fixtures.
6. Add hardware-safe packing as an optional adapter, not as a core assumption.
7. Add corpus-level residual-creep histograms for substitutions, topology labels, and sidecar replay.
8. Implement the database-backed candidate dictionary adapter against the Lean commit gate.
