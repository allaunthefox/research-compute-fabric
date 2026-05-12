#import "@preview/auto-bidi:0.1.0": auto-dir, rl, lr, force-lang

// Repo-local wrapper over auto-bidi. Prose may auto-flow RTL/LTR, while
// logograms stay protected as dense symbolic atoms.
#let logogram-atom(body, dir: "ltr") = {
  let payload = if dir == "rtl" {
    rl(body)
  } else {
    lr(body)
  }
  box(
    inset: (x: 3pt, y: 1pt),
    outset: 0pt,
    stroke: 0.45pt + luma(120),
    fill: luma(245),
    payload,
  )
}

#let logogram-flow(cells, dir: "ltr", gap: 3pt) = {
  for cell in cells {
    logogram-atom(cell, dir: dir)
    h(gap)
  }
}

#let logogram-demo() = [
  #logogram-flow(("rho", "C=U Lambda U^T", "G=A^T A", "Gamma_i"))

  #v(4pt)

  #force-lang("he")[
    #logogram-flow(("עד", "שער", "קבלה"), dir: "rtl")
  ]
]
