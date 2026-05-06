/-
  The Moser spindle is known to be 4-chromatic; a computational proof
  would require exact coordinates and exhaustive search over 3^7 colorings.
  This is an external graph-theoretic fact.
-/
structure Moser4ChromaticHypothesis where
  requires_four_colors (c : Coloring 3) (h_moser : c.points = moserPoints) :
    ¬ isLawful c

end Semantics.Benchmarks.HadwigerNelson
