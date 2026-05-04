import Semantics.Atoms
import Semantics.Lemmas
import Semantics.Projections

namespace Semantics.ENE

-- Endless Node Edges (ENE) Graph Database
-- A formalized semantic graph engine with typed nodes and edges.
-- Nodes represent different levels of semantic abstraction.
-- Edges represent proof-carrying relationships between semantic objects.

/-- Node types in the ENE semantic graph. -/
inductive NodeType
| atom           -- Irreducible semantic primitive
| lemma          -- canonicalical typed bundle of atoms
| wordform       -- Language-specific realization of a lemma
| observation    -- Raw input signal
| canonicalState -- Normalized invariant state
| attractor      -- Semantic basin / region
| signature      -- Discrete symbolic code
| interpretation -- Certified semantic projection
| loadProfile    -- Cognitive load annotation
| projection     -- Evidence-backed collapse surface
| inhibitor      -- Cognitive Landmine (adversarial warding)
| camouflage     -- Social Singularity (status-inverted masking)
| wardingField   -- Active repulsion region
deriving Repr, BEq

/-- A point in the MI-aware geometric space. Mirrors `ene_mi_signal.py`. -/
structure MIPoint where
  z : List Float           -- Feature vector
  mi : Float               -- Mutual information
  method : String          -- Best method at this point
  baselineBpb : Float      -- Cheap baseline BPB
  actualBpb : Float        -- Chosen method BPB
  support : Nat := 1
  confidence : Float := 1.0
  timestamp : Float := 0.0
deriving Repr, BEq

/-- A node in the ENE graph. -/
structure Node where
  id : Nat
  type : NodeType
  label : String
  payload : Option MIPoint := none
deriving Repr, BEq

/-- Edge classes control the semantic ecology of the graph. -/
inductive EdgeClass
| definitional     -- Constitutive relationship (lemma → atoms)
| analogical       -- Similarity across domains
| translational    -- Cross-language or cross-substrate mapping
| affective        -- Emotional or evaluative coloring
| inferential      -- Logical or causal consequence
| capabilityBearing -- Grants or transfers capability
| unstable         -- Provisional, subject to revision
| quarantined      -- Suspended pending audit
| derived          -- Computed from other edges
| realizational    -- Surface form instantiation
| projective       -- Mapping from raw to semantic
| evidentiary      -- Supports or contradicts
| loadAnnotated    -- Carries processing cost
| compositional    -- Part-whole or structural
| temporal         -- Sequence or causation in time
| warding          -- Repulsion field / Adversarial hardening
deriving Repr, BEq

/-- Edge types in the ENE graph. -/
inductive EdgeType
| has_atom         -- Lemma → Atom
| realizes         -- Wordform → Lemma
| projects_to      -- Observation → canonical
| assigned_to      -- canonical → Attractor
| has_signature    -- canonical → Signature
| supports         -- State/Evidence → Lemma
| contradicts      -- Evidence → Lemma (negative support)
| inherits         -- Lemma → Lemma
| evokes           -- Attractor → Lemma
| has_load         -- Node → LoadProfile
| derived_from     -- Interpretation → Projection
| similar_to       -- Node → Node
| composed_of      -- Interpretation → Node
| precedes         -- Temporal ordering
| causes           -- Causal influence
| path_step        -- Atomic path traversal
| witnesses        -- Emergence receipt
| collapsed_to     -- Projection → Scalar
| evolved_from     -- Self-modification trace
| wards            -- Inhibitor → Node
| camouflages      -- Camouflage → Node
deriving Repr, BEq

/-- An edge in the ENE graph.
Note: `edgeClass` is used instead of `class` because `class` is a reserved keyword. -/
structure Edge where
  id : Nat
  source : Node
  target : Node
  type : EdgeType
  edgeClass : EdgeClass
  weight : Float := 1.0
  justified : Bool := true
deriving Repr, BEq

/-- A property graph containing nodes and edges. -/
structure Graph where
  nodes : List Node
  edges : List Edge
  nextId : Nat := 0
deriving Repr

/-- An empty graph. -/
def Graph.empty : Graph := { nodes := [], edges := [], nextId := 0 }

/-- Insert a node into the graph, assigning it an ID. -/
def Graph.insertNode (g : Graph) (type : NodeType) (label : String) (payload : Option MIPoint := none) : Graph × Node :=
  let node := { id := g.nextId, type := type, label := label, payload := payload }
  ({ nodes := node :: g.nodes, edges := g.edges, nextId := g.nextId + 1 }, node)

/-- Insert an edge into the graph, assigning it an ID. -/
def Graph.insertEdge (g : Graph) (source : Node) (target : Node) (type : EdgeType) (edgeClass : EdgeClass) (weight : Float := 1.0) (justified : Bool := true) : Graph × Edge :=
  let edge := { id := g.nextId, source := source, target := target, type := type, edgeClass := edgeClass, weight := weight, justified := justified }
  ({ nodes := g.nodes, edges := edge :: g.edges, nextId := g.nextId + 1 }, edge)

/-- Find edges originating from a given node. -/
def Graph.outEdges (g : Graph) (n : Node) : List Edge :=
  g.edges.filter (λ e => e.source == n)

/-- Find edges targeting a given node. -/
def Graph.inEdges (g : Graph) (n : Node) : List Edge :=
  g.edges.filter (λ e => e.target == n)

/-- Find neighbors of a node via outgoing edges of a specific type. -/
def Graph.neighbors (g : Graph) (n : Node) (t : EdgeType) : List Node :=
  g.outEdges n |>.filter (λ e => e.type == t) |>.map (λ e => e.target)

/-- Check if a node exists in the graph. -/
def Graph.hasNode (g : Graph) (n : Node) : Bool :=
  g.nodes.contains n

/-- Map an Atom to its string label for graph lookup. -/
def atomLabel : Atom → String
| Atom.someone  => "someone"
| Atom.something => "something"
| Atom.do_      => "do_"
| Atom.happen   => "happen"
| Atom.move     => "move"
| Atom.cause    => "cause"
| Atom.die      => "die"
| Atom.want     => "want"
| Atom.know     => "know"
| Atom.feel     => "feel"
| Atom.think    => "think"
| Atom.good     => "good"
| Atom.bad      => "bad"
| Atom.because  => "because"
| Atom.not      => "not"

/-- A typed interface for lemma nodes: they must carry specific semantic atoms. -/
def Graph.lemmaHasAtom (g : Graph) (l : Node) (a : Atom) : Prop :=
  ∃ e ∈ g.edges, e.source == l ∧ e.type == EdgeType.has_atom ∧ ∃ n ∈ g.nodes, n == e.target ∧ n.label = atomLabel a

/-- A proposition that the graph contains no quarantined edges with positive weight.
This is a basic safety invariant: dangerous edges must be neutralized. -/
def Graph.noActiveQuarantine (g : Graph) : Prop :=
  ∀ e ∈ g.edges, e.edgeClass == EdgeClass.quarantined → e.weight ≤ 0.0

end Semantics.ENE
