# Human Mathematical Translation Modes v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec extends `Translator_Packets_v0_1.md` into a broader research program: document the ways humans translate metaphor, imagery, gesture, analogy, embodied action, and conceptual blends into mathematics, then turn those translation modes into a reusable problem-attack model.

The purpose is not to replace proof. The purpose is to improve conjecture generation, problem decomposition, model selection, and formalization routing.

## Core thesis

Humans do not usually reach mathematics by one path. They use multiple translation modes:

```text
metaphor
analogy
gesture
image / diagram
motion / embodiment
conceptual blending
heuristic guessing
counterexample repair
symbol compression
formal proof
```

A useful research system should document these modes, detect which mode a human is using, and route the output into typed mathematical objects.

In OTOM terms:

```text
human intuition surface
→ translator packet
→ translation mode classifier
→ mathematical type assignment
→ operator / predicate / gate
→ equation / algorithm / theorem shape
→ receipt discipline
```

## Why this matters

Most hard problems do not arrive already encoded as clean formal statements. Humans often begin with:

```text
images
motions
strange analogies
partial patterns
bad names
wrong but useful guesses
physical intuitions
```

If these are discarded too early, the model loses discovery signal.

If they are believed too early, the model inflates metaphor into false law.

The solution is a gated translation model:

```text
preserve intuition
extract structure
assign type
build gate
test receipt
```

## Historical / literature anchors

This program has several research ancestors.

### Pólya — plausible reasoning and analogy

Pólya treated guessing, analogy, induction, false bypaths, and proof search as part of mathematical discovery. The relevance is direct: an intuitive packet can be treated as a plausible-reasoning object, not a proof.

### Lakoff and Núñez — embodied mathematical metaphor

Lakoff and Núñez argue that mathematical ideas are often structured by embodied conceptual metaphors, such as arithmetic as object collection or numbers as points on a line.

### Fauconnier and Turner — conceptual blending

Conceptual integration / blending describes how structure from multiple input spaces can project into a blended space that develops new inference structure.

### Gesture and embodiment research

Gesture studies show that mathematical understanding can be supported by pointing, representational gesture, fictive motion, and embodied action. This gives a basis for treating spatial and motor fragments as possible mathematical source domains.

### Formal cognitive models

Work by Guhe, Pease, Smaill, and related researchers models mathematical metaphor, analogy, anti-unification, and conceptual blending computationally. This provides precedent for making the translation pipeline formal enough to support automated reasoning.

### Mathematical practice cautions

Schlimm, Wagner, Friedman, and others warn that historical mathematical practice is messier than clean retrospective metaphor maps. This supports OTOM's Warden boundary: metaphor can motivate structure, but receipts decide promotion.

## Translation mode catalog

### 1. Metaphor mode

A concrete source domain structures an abstract target domain.

Example:

```text
numbers as points on a line
```

OTOM packet form:

```text
source object → target object
source relation → target relation
source operation → target operation
```

Attack use:

```text
When a problem feels abstract, search for a concrete source domain with matching relational structure.
```

Risk:

```text
false entailments from the source domain leak into the target domain
```

Gate:

```text
only preserve entailments that survive target-domain invariants
```

### 2. Analogy mode

A known mathematical or physical domain suggests structure in an unknown domain.

Example:

```text
finite equations → infinite series
rubber-sheet topology → polyhedra conjecture repair
arithmetic motion → path reasoning
```

Attack use:

```text
Find a solved domain with a similar relational graph, then map objects, morphisms, invariants, and failure cases.
```

Risk:

```text
surface similarity mistaken for structural similarity
```

Gate:

```text
require relation-preserving alignment, not word overlap
```

### 3. Gesture / motion mode

A hand movement, imagined motion, or motor simulation carries mathematical structure.

Example:

```text
rotate
slide
flip
stretch
collapse
flow
wrap
```

Attack use:

```text
Convert motion verbs into transformations, group actions, flows, or update rules.
```

Risk:

```text
gesture encodes local intuition but not global validity
```

Gate:

```text
local transformation must be checked against global invariants
```

### 4. Image / diagram mode

A visual layout exposes relationships before algebra does.

Example:

```text
standing-wave contour rings
Connect Four board as constrained columnar lattice
```

Attack use:

```text
Extract nodes, edges, regions, boundaries, symmetries, holes, gradients, and support predicates.
```

Risk:

```text
rendering artifact mistaken for underlying structure
```

Gate:

```text
distinguish observed surface from generative equation
```

### 5. Embodied constraint mode

Bodily or physical experience supplies constraints: containment, support, balance, path, force, distance, obstacle, pressure.

Example:

```text
support failure → SORRY Collapse Gate
winding tension → Torsion Flip Operator
```

Attack use:

```text
Identify hidden predicates such as support, containment, threshold, reachability, conservation, or orientation.
```

Risk:

```text
physical realism overclaimed when the model is only a toy formalism
```

Gate:

```text
state whether the constraint is physical, computational, formal, or metaphorical
```

### 6. Conceptual blending mode

Two or more source spaces combine into a new object whose inference structure is not identical to either source.

Example:

```text
kinetic standing wave + Sidon set → kinetic/Sidon relational lattice
oracle + DeltaPhi + cosine → IDPC oracle-interrogation gate
```

Attack use:

```text
Create a blended working space, then ask what new object, predicate, or invariant appears only in the blend.
```

Risk:

```text
blend becomes evocative but untyped
```

Gate:

```text
force each blended component to declare type, role, and invariant contribution
```

### 7. Heuristic / good-guessing mode

A non-deductive hunch proposes a path before proof exists.

Example:

```text
this phrase feels like torsion
this image feels like support collapse
```

Attack use:

```text
Generate candidate operators and test cheaply.
```

Risk:

```text
confidence grows faster than evidence
```

Gate:

```text
claim state remains BEAUTIFUL_PROVISIONAL until receipt-backed
```

### 8. Counterexample repair mode

A failed case forces refinement of the definition or theorem.

Example:

```text
if a flipped Sidon address aliases, the flip is not lawful
if support fails, pair signatures are no longer meaningful
```

Attack use:

```text
Search for failure cases, then classify whether to restrict the domain, modify the predicate, split the type, or lower the claim state.
```

Risk:

```text
patching every failure ad hoc
```

Gate:

```text
repair must reduce ambiguity or preserve a declared invariant
```

### 9. Symbol compression mode

A phrase, image, or notation compresses a larger operator.

Example:

```text
IDPC = Inverse Delta Phi over Cosine
SORRY = invalidation receipt
round and round and upside down = torsion flip
```

Attack use:

```text
Treat the symbol/name as an index to a larger typed packet.
```

Risk:

```text
name becomes authority
```

Gate:

```text
name has no proof power; it only aids recall and routing
```

### 10. Formalization mode

The translated packet is converted into definitions, predicates, equations, algorithms, or Lean theorem shapes.

Example:

```text
SupportFailed b → applySorryCollapseGate b emits sorry
SidonLike pairs → no AliasCollision pairs
```

Attack use:

```text
Convert operator candidates into finite checkable gates.
```

Risk:

```text
formal scaffold mistaken for validation of the original intuition
```

Gate:

```text
Lean proves only the formal statement it encodes
```

## Problem-attack model

Given a hard problem `P`, run the following loop.

### Step 1 — Capture surfaces

Collect all available informal material:

```text
phrases
images
diagrams
motions
metaphors
analogies
emotional mismatch signals
failure memories
```

### Step 2 — Packetize

For each surface, create a Translator Packet:

```text
rawSurface
object carrier
transform verb
trigger predicate
failure mode
receipt marker
possible target type
```

### Step 3 — Classify mode

Assign one or more translation modes:

```text
metaphor
analogy
gesture / motion
image / diagram
embodied constraint
conceptual blend
heuristic guess
counterexample repair
symbol compression
formalization
```

### Step 4 — Type assignment

Force the packet into one or more mathematical types:

```text
scalar field
vector state
local frame
lattice state
pair signature
graph
operator
predicate
receipt ledger
support condition
```

### Step 5 — Invariant extraction

Ask:

```text
What must stay true if this packet is useful?
```

Possible answers:

```text
no alias collisions
bounded reconstruction error
proof receipt required
support predicate holds
orientation flips only above threshold
confidence cannot exceed evidence support
```

### Step 6 — Gate construction

Convert the invariant into a pass/fail test:

```text
aliasCount = 0
reconstructionError <= epsilon
receiptExists = true
torsionScore >= torsionThreshold
supportStatus = invalid
```

### Step 7 — Formal split

Separate what belongs in prose/equations from what belongs in Lean:

```text
continuous PDE / metaphor / physical story → spec
finite predicate / discrete update / theorem shape → Lean
```

### Step 8 — Attack the problem

Use the typed packets to propose candidate decompositions:

```text
new operator
new invariant
new search heuristic
new benchmark
new failure mode
new theorem target
```

### Step 9 — Receipt discipline

Every candidate gets a claim state:

```text
BEAUTIFUL_PROVISIONAL
CALIBRATED_ENGINEERING_DELTA
REVIEWED
```

No packet becomes reviewed without proof, benchmark, measurement, or source receipt.

## OTOM formal model sketch

Let:

```text
S = set of informal surfaces
M = set of translation modes
T = set of mathematical target types
G = set of gates
R = set of receipts
```

A human mathematical translation run is:

```text
Translate : S -> Packet
Classify  : Packet -> P(M)
Type      : Packet x M -> P(T)
Gate      : Packet x T -> P(G)
Receipt   : G -> R
Promote   : Packet x R -> ClaimState
```

A problem attack is successful when it produces at least one packet whose gate yields a nontrivial, receiptable invariant:

```text
exists p, g, r:
  p = Translate(s)
  g in Gate(p, Type(p, Classify(p)))
  r validates g
```

## Relationship to 3I-ATLAS

This model maps cleanly into 3I-ATLAS:

```text
Interfaces:
  raw human surfaces, diagrams, gestures, metaphors, tool outputs

Invariants:
  gates, predicates, Warden boundaries, receipt requirements

Intelligence:
  mode classification, type assignment, counterexample repair, adaptation
```

So the translation model is itself a 3I-ATLAS system.

## Warden boundaries

### Blocked claims

```text
Human metaphor is automatically mathematical truth.
Every intuitive association deserves a theorem.
A formal model of translation proves a historical cognitive process.
A Lean gate validates the source metaphor.
Problem-solving heuristics replace proof.
```

### Allowed claims

```text
Humans use multiple documented mechanisms to generate mathematical ideas from nonformal material.
Those mechanisms can be cataloged as translation modes.
Translation modes can help attack problems by generating typed candidates.
Typed candidates can be converted into gates, equations, algorithms, or theorem shapes.
Promotion still requires receipts.
```

## Research tasks

1. Build a citation map for each translation mode.
2. Add examples from mathematical history for each mode.
3. Build a packet dataset from OTOM examples and historical examples.
4. Design a mode classifier for raw metaphor/gesture/image text.
5. Define benchmark problems where packets generate useful operators.
6. Compare packet-guided problem attack against ordinary prompt-based reasoning.
7. Formalize only finite gates in Lean; keep cognitive/historical claims source-bound.

## Strongest formulation

> Human Mathematical Translation Modes are the documented mechanisms by which people convert embodied, imagistic, metaphorical, analogical, and heuristic material into mathematical candidates. OTOM turns those modes into a problem-attack loop: packetize the intuition, classify the translation mode, assign mathematical type, extract invariants, build gates, and require receipts before promotion.
