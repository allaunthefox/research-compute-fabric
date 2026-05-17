#import "@preview/auto-bidi:0.1.0": auto-dir, rl, lr, force-lang

// Omindirection: repo-local dense symbolic flow layer.
//
// This is intentionally a thin Typst plugin surface rather than a patched
// upstream package. The document can use auto-bidi for prose while this layer
// keeps logogram packets explicit, isolated, and receipt-friendly.

#let omi-show(body) = auto-dir.with(detect-by: "auto")(body)

#let omi-payload(body, dir: "auto", lang: none) = {
  let directed = if dir == "rtl" {
    rl(body)
  } else if dir == "ltr" {
    lr(body)
  } else {
    body
  }

  if lang == none {
    directed
  } else {
    force-lang(lang, directed)
  }
}

#let omi-chiral-label(chirality) = {
  if chirality == "left" {
    "L:"
  } else if chirality == "right" {
    "R:"
  } else if chirality == "ambidextrous" {
    "LR:"
  } else {
    ""
  }
}

#let omi-phase-label(phase) = {
  if phase == none {
    ""
  } else {
    "@" + str(phase) + "deg:"
  }
}

#let omi-torsion-label(torsion) = {
  if torsion == none {
    ""
  } else {
    "tau=" + str(torsion) + ":"
  }
}

#let omi-temporal-label(temporal) = {
  if temporal == none {
    ""
  } else {
    "t=" + str(temporal) + ":"
  }
}

#let omi-rounding-label(rounding) = {
  if rounding == none {
    ""
  } else {
    "q=" + str(rounding) + ":"
  }
}

#let omi-residual-label(residual) = {
  if residual == none {
    ""
  } else {
    "r=" + str(residual) + ":"
  }
}

#let omi-atom(
  body,
  dir: "auto",
  lang: none,
  tone: "neutral",
  chirality: "none",
  phase: none,
  torsion: none,
  temporal: none,
  rounding: none,
  residual: none,
) = {
  let fill = if tone == "witness" {
    rgb("#edf7ee")
  } else if tone == "unknown" {
    rgb("#edf2fb")
  } else if tone == "boundary" {
    rgb("#f1eef7")
  } else if tone == "residual" {
    rgb("#fff0eb")
  } else if tone == "growth" {
    rgb("#eff8df")
  } else {
    luma(245)
  }

  let chiral-prefix = omi-chiral-label(chirality)
  let phase-prefix = omi-phase-label(phase)
  let torsion-prefix = omi-torsion-label(torsion)
  let temporal-prefix = omi-temporal-label(temporal)
  let rounding-prefix = omi-rounding-label(rounding)
  let residual-prefix = omi-residual-label(residual)
  let prefix = chiral-prefix + phase-prefix + torsion-prefix + temporal-prefix + rounding-prefix + residual-prefix
  let chiral-body = if prefix == "" {
    body
  } else {
    prefix + body
  }

  box(
    inset: (x: 3pt, y: 1pt),
    outset: 0pt,
    stroke: 0.45pt + luma(115),
    fill: fill,
    omi-payload(chiral-body, dir: dir, lang: lang),
  )
}

#let omi-flow(
  cells,
  dir: "auto",
  lang: none,
  tone: "neutral",
  chirality: "none",
  phase: none,
  torsion: none,
  temporal: none,
  rounding: none,
  residual: none,
  gap: 3pt,
) = {
  for cell in cells {
    omi-atom(
      cell,
      dir: dir,
      lang: lang,
      tone: tone,
      chirality: chirality,
      phase: phase,
      torsion: torsion,
      temporal: temporal,
      rounding: rounding,
      residual: residual,
    )
    h(gap)
  }
}

#let omi-chiral360(
  body,
  phase,
  dir: "auto",
  tone: "neutral",
  torsion: none,
  temporal: none,
  rounding: none,
  residual: none,
) = {
  omi-atom(
    body,
    dir: dir,
    tone: tone,
    chirality: "ambidextrous",
    phase: phase,
    torsion: torsion,
    temporal: temporal,
    rounding: rounding,
    residual: residual,
  )
}

#let omi-static-target(body, phase, torsion, temporal, dir: "ltr", rounding: none, residual: none) = {
  omi-atom(
    body,
    dir: dir,
    tone: "growth",
    chirality: "ambidextrous",
    phase: phase,
    torsion: torsion,
    temporal: temporal,
    rounding: rounding,
    residual: residual,
  )
}

#let omi-rehydratable(body, rounding, residual, phase: none, temporal: none, dir: "ltr") = {
  omi-atom(
    body,
    dir: dir,
    tone: "witness",
    chirality: "ambidextrous",
    phase: phase,
    temporal: temporal,
    rounding: rounding,
    residual: residual,
  )
}

#let omi-chiral-pair(body, left-dir: "ltr", right-dir: "rtl") = {
  grid(
    columns: (1fr, 1fr),
    gutter: 8pt,
    omi-atom(body, dir: left-dir, tone: "boundary", chirality: "left"),
    align(right, omi-atom(body, dir: right-dir, tone: "residual", chirality: "right")),
  )
}

#let omi-mirror(left-cells, right-cells, left-dir: "ltr", right-dir: "rtl") = {
  grid(
    columns: (1fr, 1fr),
    gutter: 8pt,
    omi-flow(left-cells, dir: left-dir, tone: "witness"),
    align(right, omi-flow(right-cells, dir: right-dir, tone: "unknown")),
  )
}

#let omi-demo() = [
  #omi-flow(("rho", "C=U Lambda U^T", "G=A^T A", "Gamma_i"), dir: "ltr", tone: "witness")

  #v(4pt)

  #omi-flow(("עד", "שער", "קבלה"), dir: "rtl", lang: "he", tone: "unknown")

  #v(4pt)

  #omi-mirror(
    ("field", "spectral", "shear", "packet"),
    ("עד", "שער", "קבלה"),
  )

  #v(4pt)

  #omi-chiral-pair("Gamma_i")

  #v(4pt)

  #omi-flow(("Gamma_i", "Gamma_i", "Gamma_i", "Gamma_i"), dir: "ltr", tone: "growth", chirality: "ambidextrous", phase: 0)
  #v(2pt)
  #omi-chiral360("Gamma_i", 90, dir: "ltr", tone: "witness")
  #h(3pt)
  #omi-chiral360("Gamma_i", 180, dir: "rtl", tone: "boundary")
  #h(3pt)
  #omi-chiral360("Gamma_i", 270, dir: "rtl", tone: "residual")

  #v(4pt)

  #omi-static-target("Hutter-token", 42, 7, 1024)
  #h(3pt)
  #omi-static-target("Hutter-token", 137, 2, 2048)
  #h(3pt)
  #omi-static-target("Hutter-token", 311, 11, 4096)

  #v(4pt)

  #omi-rehydratable("rounded-core", "q8", "sidecar-a13f", phase: 42, temporal: 1024)
]
