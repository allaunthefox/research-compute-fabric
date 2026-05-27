/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

TreeDIATKruskal.lean — proof scaffold for TreeDIAT/Kruskal behavior

This module upgrades TreeDIAT from a pure heuristic packet into a
Kruskal-facing proof surface. It intentionally does NOT claim a proof of
Kruskal's tree theorem or TREE(3). Instead it supplies:

  • an explicit homeomorphic-embedding relation for labelled binary trees,
  • certified size/leaf-count monotonicity under that embedding relation,
  • exact Nat-level score-order lemmas for the TreeDIAT routing heuristic,
  • a certificate type separating true Kruskal witnesses from scalar DIAT scores.

The rule is anti-drift: TreeDIAT scores may route/search/prune, but a real
Kruskal witness must carry an embedding proof.
-/

import Semantics.PistSimulation
import Mathlib.Tactic

namespace Semantics.PistSimulation

-- ════════════════════════════════════════════════════════════
-- §1  Exact tree measures independent of Q16.16 rounding
-- ════════════════════════════════════════════════════════════

/-- Exact depth of a labelled binary tree. A leaf has depth 1. -/
def treeDepthExact : TreeNode → Nat
  | .leaf _ => 1
  | .node _ l r => Nat.max (treeDepthExact l) (treeDepthExact r) + 1

/-- Exact number of leaves. -/
def treeLeafCountExact : TreeNode → Nat
  | .leaf _ => 1
  | .node _ l r => treeLeafCountExact l + treeLeafCountExact r

/-- Exact number of nodes. -/
def treeNodeCountExact : TreeNode → Nat
  | .leaf _ => 1
  | .node _ l r => treeNodeCountExact l + treeNodeCountExact r + 1

/-- Exact maximum label. -/
def treeMaxLabelExact : TreeNode → Nat
  | .leaf label => label
  | .node label l r => Nat.max label (Nat.max (treeMaxLabelExact l) (treeMaxLabelExact r))

/-- Exact label-count proxy matching TreeDIAT's `maxLabel + 1` convention. -/
def treeLabelCountExact (t : TreeNode) : Nat := treeMaxLabelExact t + 1

/-- Node count is always positive. -/
theorem treeNodeCountExact_pos (t : TreeNode) : 0 < treeNodeCountExact t := by
  induction t with
  | leaf label => simp [treeNodeCountExact]
  | node label l r ihL ihR => simp [treeNodeCountExact, ihL, ihR]

/-- Leaf count is always positive. -/
theorem treeLeafCountExact_pos (t : TreeNode) : 0 < treeLeafCountExact t := by
  induction t with
  | leaf label => simp [treeLeafCountExact]
  | node label l r ihL ihR => simp [treeLeafCountExact, ihL, ihR]

/-- A tree cannot have more leaves than nodes. -/
theorem treeLeafCountExact_le_nodeCountExact (t : TreeNode) :
    treeLeafCountExact t ≤ treeNodeCountExact t := by
  induction t with
  | leaf label => simp [treeLeafCountExact, treeNodeCountExact]
  | node label l r ihL ihR =>
      simp [treeLeafCountExact, treeNodeCountExact]
      omega

-- ════════════════════════════════════════════════════════════
-- §2  Kruskal-facing homeomorphic embedding relation
-- ════════════════════════════════════════════════════════════

/--
A conservative labelled-tree embedding relation.

`TreeEmbeds s t` means `s` can be found inside `t` by:
  • reflexivity,
  • descending into the left or right child of `t`, or
  • matching equal labels at a node and embedding left/right subtrees.

This is a proof-carrying witness relation. It is intentionally separate from
TreeDIAT's scalar `embeddingScore`, because the score is only a routing
heuristic, not a Kruskal certificate.
-/
inductive TreeEmbeds : TreeNode → TreeNode → Prop
  | refl (t : TreeNode) : TreeEmbeds t t
  | intoLeft {s : TreeNode} {label : Nat} {l r : TreeNode}
      (h : TreeEmbeds s l) : TreeEmbeds s (.node label l r)
  | intoRight {s : TreeNode} {label : Nat} {l r : TreeNode}
      (h : TreeEmbeds s r) : TreeEmbeds s (.node label l r)
  | node {label : Nat} {l₁ r₁ l₂ r₂ : TreeNode}
      (hL : TreeEmbeds l₁ l₂) (hR : TreeEmbeds r₁ r₂) :
      TreeEmbeds (.node label l₁ r₁) (.node label l₂ r₂)

/-- Any tree embeds in itself. -/
theorem TreeEmbeds.self (t : TreeNode) : TreeEmbeds t t := TreeEmbeds.refl t

/-- If `s` embeds in `t`, `s` has no more nodes than `t`. -/
theorem treeEmbeds_nodeCount_le {s t : TreeNode} (h : TreeEmbeds s t) :
    treeNodeCountExact s ≤ treeNodeCountExact t := by
  induction h with
  | refl t => simp [treeNodeCountExact]
  | intoLeft h ih =>
      simp [treeNodeCountExact]
      omega
  | intoRight h ih =>
      simp [treeNodeCountExact]
      omega
  | node hL hR ihL ihR =>
      simp [treeNodeCountExact]
      omega

/-- If `s` embeds in `t`, `s` has no more leaves than `t`. -/
theorem treeEmbeds_leafCount_le {s t : TreeNode} (h : TreeEmbeds s t) :
    treeLeafCountExact s ≤ treeLeafCountExact t := by
  induction h with
  | refl t => simp [treeLeafCountExact]
  | intoLeft h ih =>
      simp [treeLeafCountExact]
      omega
  | intoRight h ih =>
      simp [treeLeafCountExact]
      omega
  | node hL hR ihL ihR =>
      simp [treeLeafCountExact]
      omega

-- ════════════════════════════════════════════════════════════
-- §3  Exact TreeDIAT score-order lemmas
-- ════════════════════════════════════════════════════════════

/-- Exact Nat denominator behind TreeDIAT's heuristic score. -/
def scoreDenNat (depth labelCount : Nat) : Nat := depth * labelCount + 1

/-- Exact rational-score order by cross multiplication.

`scoreLENat a b` means:

  leafA / (depthA·labelsA + 1) ≤ leafB / (depthB·labelsB + 1)

without constructing a rational or entering Q16.16 rounding. -/
def scoreLENat
    (leafA depthA labelsA leafB depthB labelsB : Nat) : Prop :=
  leafA * scoreDenNat depthB labelsB ≤ leafB * scoreDenNat depthA labelsA

/-- TreeDIAT score denominator is never zero. -/
theorem scoreDenNat_pos (depth labelCount : Nat) : 0 < scoreDenNat depth labelCount := by
  unfold scoreDenNat
  omega

/-- Holding label-count fixed, deeper trees have a larger score denominator. -/
theorem scoreDenNat_depth_mono {d₁ d₂ labels : Nat} (h : d₁ ≤ d₂) :
    scoreDenNat d₁ labels ≤ scoreDenNat d₂ labels := by
  unfold scoreDenNat
  exact Nat.add_le_add_right (Nat.mul_le_mul_right labels h) 1

/-- Holding depth fixed, more labels have a larger score denominator. -/
theorem scoreDenNat_label_mono {depth labels₁ labels₂ : Nat} (h : labels₁ ≤ labels₂) :
    scoreDenNat depth labels₁ ≤ scoreDenNat depth labels₂ := by
  unfold scoreDenNat
  exact Nat.add_le_add_right (Nat.mul_le_mul_left depth h) 1

/-- With the same leaf count and labels, increasing depth cannot increase the exact score. -/
theorem scoreLENat_same_leaf_deeper_lowers
    {leaf dShallow dDeep labels : Nat} (hDepth : dShallow ≤ dDeep) :
    scoreLENat leaf dDeep labels leaf dShallow labels := by
  unfold scoreLENat
  exact Nat.mul_le_mul_left leaf (scoreDenNat_depth_mono hDepth)

/-- With the same depth and labels, increasing leaf count cannot lower the exact score. -/
theorem scoreLENat_same_shape_more_leaves_raises
    {leafSmall leafLarge depth labels : Nat} (hLeaf : leafSmall ≤ leafLarge) :
    scoreLENat leafSmall depth labels leafLarge depth labels := by
  unfold scoreLENat
  exact Nat.mul_le_mul_right (scoreDenNat depth labels) hLeaf

/-- Exact denominator attached to an existing TreeDIAT packet. -/
def treeDIATScoreDen (td : TreeDIAT) : Nat := scoreDenNat td.depth td.labelCount

/-- Exact rational-order shadow for existing TreeDIAT packets. -/
def treeDIATScoreLE (a b : TreeDIAT) : Prop :=
  a.leafCount * treeDIATScoreDen b ≤ b.leafCount * treeDIATScoreDen a

/-- Existing TreeDIAT packet denominator is never zero. -/
theorem treeDIATScoreDen_pos (td : TreeDIAT) : 0 < treeDIATScoreDen td := by
  unfold treeDIATScoreDen
  exact scoreDenNat_pos td.depth td.labelCount

/-- Same leaves and labels: the deeper TreeDIAT packet has no higher exact score. -/
theorem treeDIAT_same_leaf_deeper_lowers_score {a b : TreeDIAT}
    (hLeaf : a.leafCount = b.leafCount)
    (hLabel : a.labelCount = b.labelCount)
    (hDepth : b.depth ≤ a.depth) :
    treeDIATScoreLE a b := by
  unfold treeDIATScoreLE treeDIATScoreDen
  rw [hLeaf, hLabel]
  exact Nat.mul_le_mul_left b.leafCount (scoreDenNat_depth_mono hDepth)

/-- Same depth and labels: the TreeDIAT packet with fewer leaves has no higher exact score. -/
theorem treeDIAT_same_depth_label_more_leaves_raises_score {a b : TreeDIAT}
    (hDepth : a.depth = b.depth)
    (hLabel : a.labelCount = b.labelCount)
    (hLeaf : a.leafCount ≤ b.leafCount) :
    treeDIATScoreLE a b := by
  unfold treeDIATScoreLE treeDIATScoreDen
  rw [hDepth, hLabel]
  exact Nat.mul_le_mul_right (scoreDenNat b.depth b.labelCount) hLeaf

-- ════════════════════════════════════════════════════════════
-- §4  Proof-carrying Kruskal witness boundary
-- ════════════════════════════════════════════════════════════

/--
A positive Kruskal-style witness for a pair of tree states.

The scalar TreeDIAT packet is available for routing, but the certificate is
the `embeds` proof. This prevents the project from confusing a heuristic
score with Kruskal's theorem or TREE(3).
-/
structure TreeDIATKruskalCertificate where
  earlier : TreeNode
  later   : TreeNode
  embeds  : TreeEmbeds earlier later

/-- Earlier packet carried by a proof certificate. -/
def TreeDIATKruskalCertificate.earlierPacket (c : TreeDIATKruskalCertificate) : TreeDIAT :=
  treeToDIAT c.earlier

/-- Later packet carried by a proof certificate. -/
def TreeDIATKruskalCertificate.laterPacket (c : TreeDIATKruskalCertificate) : TreeDIAT :=
  treeToDIAT c.later

/-- A certificate guarantees node-count monotonicity. -/
theorem TreeDIATKruskalCertificate.nodeCount_le (c : TreeDIATKruskalCertificate) :
    treeNodeCountExact c.earlier ≤ treeNodeCountExact c.later :=
  treeEmbeds_nodeCount_le c.embeds

/-- A certificate guarantees leaf-count monotonicity. -/
theorem TreeDIATKruskalCertificate.leafCount_le (c : TreeDIATKruskalCertificate) :
    treeLeafCountExact c.earlier ≤ treeLeafCountExact c.later :=
  treeEmbeds_leafCount_le c.embeds

/-- Trivial fixture: the bushy tree embeds in itself. -/
def fixtureBushyKruskalCertificate : TreeDIATKruskalCertificate :=
  { earlier := fixtureBushyTree
  , later := fixtureBushyTree
  , embeds := TreeEmbeds.self fixtureBushyTree }

/-- A bad Kruskal prefix is an ordered list with no earlier tree embedding in a later tree. -/
def KruskalBadPrefix (xs : List TreeNode) : Prop :=
  xs.Pairwise (fun earlier later => ¬ TreeEmbeds earlier later)

end Semantics.PistSimulation
