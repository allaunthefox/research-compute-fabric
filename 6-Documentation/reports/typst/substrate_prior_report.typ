#import "@preview/auto-bidi:0.1.0": *
#import "@preview/unify:0.8.0": num, qty, numrange, qtyrange
#import "omindirection.typ": omi-show, omi-atom, omi-flow, omi-mirror, omi-demo
#import "logogram-bidi.typ": logogram-atom, logogram-flow, logogram-demo
#set document(title: "Research Stack Substrate Prior Report")
#set page(width: 8.5in, height: 11in, margin: 0.75in)
#set text(size: 10pt)
#set heading(numbering: "1.")
#show: auto-dir.with(
  detect-by: "auto",
  hebrew-font: "Noto Sans Hebrew",
  arab-font: "Noto Naskh Arabic",
  english-font: ("New Computer Modern", "Libertinus Serif"),
  base-font: "New Computer Modern",
)

= Research Stack Substrate Prior Report

Generated: 2026-05-07T17:39:50.629849+00:00

Receipt ID: `8a32694ee8373506f140c7da`

== Claim Boundary

This report is a visualization and documentation artifact. It is not a theorem proof, solver certificate, hardware benchmark, QPU submission receipt, or biological-computing capability claim.

== Source Tiddlers

1. Erdos Four Primitive Diagnostics -- `6e57b3c0a84250ca`
2. Erdos DAG FAMM Investigation -- `c4a6f9eabdc648a2`
3. Erdos DAG FAMM Historical Run Note -- `1cfdf5a3c58dad99`
4. Four Primitive FPGA Acceleration Research -- `7f4d1c439bfa520c`
5. Quandela Noise Residual Shaver -- `c58a0ac1fe756de5`
6. Thermodynamic Computing Surface Prior -- `f1b27907fa8a8450`
7. Biological Reservoir Surface Prior -- `e17f7cf954a2e488`
8. Monocurl Interactive Math Animation Prior -- `faf7f6b72ba081e0`
9. Typst Math Typesetting Surface Prior -- `d6b1e9287c5cdb71`
10. Typst Universe Useful Package Sweep -- `d2e5ec0a2079e3a3`
11. Typst Auto Bidi Dense Flow Prior -- `3ff2006065d4ba85`
12. Typst Omindirection Plugin Surface -- `e1eab0db8fe92b02`
13. Typst Logogram Bidi Layer -- `e8b75b24fd2f51e6`
14. Typst WUBRG Color Code Prior -- `2ca64858db5edc03`
15. Typst Unify Units Package Prior -- `e859bd0fc290bd04`
16. Typst Universe Package Registry Prior -- `8a642c328e83ea8b`
17. Typst Typshade Bioalignment Package Prior -- `9a5fad3e732a905c`
18. Typst Alchemist Molecule Package Prior -- `81eba5101fff1432`
19. OpenClaw Shared Bus Surface -- `c8b451a67aefd465`
20. OpenClaw Capability Surface -- `bac49972b72e22bd`
21. Epigenetic Go-Tile Meta-Manifold -- `64d00c9d078be287`
22. Hutter Static Target Omindirection Prior -- `b16e430337a955f4`
23. PAQ Style Compression Review -- `e36d4ffb329d09a4`
24. Rehydratable Non-Core Rounding Prior -- `9245971fe6512422`
25. Omindirection Compression Concept Ledger -- `0393ddc6147b9f80`
26. MathXML Domain Graph Import -- `bcacd0f9129c9299`
27. Finance Math OTOM Layer -- `62ccc6c8bbca8e00`
28. Finance Claim LUT Compression Harness -- `7a0cf1e92720b524`
29. Remote Compression Test Ladder -- `69fc3961d0be9d27`
30. Virtual Baud Reconstruction Layer -- `fea1aa1777981eee`
31. Committee Jupyter Book Explanation Plan -- `aaee293009eabd21`
32. Cursed Doom Goals -- `b9e4b5b48fe1b92c`

== Receipt Metrics

These values are presentation examples copied from source notes or receipts; they are not new measurements.

#table(
  columns: (1fr, 1fr, 1fr),
  [Metric], [Value], [Boundary],
  [Historical FAMM engram strength], [$num("20.85")$], [historical harness note],
  [Historical FAMM delay diversity], [$num("3.00")$], [historical harness note],
  [Mollin-Walsh temporal density], [$qty("82.11", "percent")$], [historical harness note],
  [Quandela average noise shave score], [$num("0.6444444444444445")$], [dry-run routing receipt],
  [Conservative PCIe FPGA speedup], [$numrange("2", "20")$], [hypothesis until measured],
)

== Omindirection Logogram Layer Smoke

The following row is a presentation smoke for protected symbolic atoms under the repo-local `omindirection.typ` plugin surface.

#omi-demo()

== Notes

=== Erdos Four Primitive Diagnostics

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Erdos Four Primitive Diagnostics.tid`

Hash: `6e57b3c0a84250ca4e4133ee3b23cad13ad556302037daf4547335d7ed0da1b3`

```text
! Erdos Four Primitive Diagnostics

This index records Erdős-style conjecture experiments as diagnostic packets, not theorem claims.

!! Active Cards

* Erdos Gyarfas Detector Anomaly — power-of-two cycle test must emit a verified Γ_fail packet before any counterexample claim is trusted.
* Erdos Selfridge Finite Smoke Test — finite generated covering-system samples found no odd-moduli violation, but this is not a proof of the full conjecture.
* Erdos DAG FAMM Investigation — receipt-first DAG/FAMM harness for Gyárfás, Selfridge, and Mollin-Walsh finite investigations.
* Erdos DAG FAMM Historical Run Note — older DAG/FAMM interpretation preserved as search-pruning history, with theorem claims demoted to finite harness behavior.

!! Four-Primitive Reading

The accurate framework claim is:

> The four primitives provide a diagnostic coordinate system over Erdős-style objects: field density, spectral structure, shear balance, and packetized obstruction witnesses.

For graph-cycle problems:

* ρ(x) = edge and degree density.
* C = UΛU^T = adjacency spectral structure.
* G = A^T A = graph rigidity or degree deformation.
* Γ_i = cycle packet, missing-cycle residual, and counterexample certificate.

For covering-system problems:

* ρ(x) = residue/modulus coverage density.
* C = UΛU^T = covering overlap spectrum.
* G = A^T A = even/odd modulus balance.
* Γ_i = covering-system packet plus violation witness.

!! Local Evidence

* 4-Infrastructure/shim/test_erdos_gyarfas_4primitive_results.json
* 4-Infrastructure/shim/test_erdos_selfridge_4primitive_results.json
* 4-Infrastructure/shim/investigate_erdos_gyarfas_refined.py
* 4-Infrastructure/shim/investigate_erdos_dag_famm.py
* 4-Infrastructure/shim/investigate_erdos_dag_famm_results.json

!! Rule

...
```

=== Erdos DAG FAMM Investigation

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Erdos DAG FAMM Investigation.tid`

Hash: `c4a6f9eabdc648a274c8a35de2c0bceb47545c1ea4d3706c0cee14ea46e3ecd7`

```text
! Erdos DAG FAMM Investigation

This card records the receipt-first DAG/FAMM investigation harness for Erdős-style experiments.

!! Artifact

* Harness: 4-Infrastructure/shim/investigate_erdos_dag_famm.py
* Results: 4-Infrastructure/shim/investigate_erdos_dag_famm_results.json

!! Method

The DAG is the audit workflow, not the mathematical object under test.

* gyarfas_packet_receipts
* selfridge_covering_receipts
* mollin_walsh_powerful_receipts
* dag_famm_synthesis

The FAMM layer is a finite associative memory matrix over packet domains and statuses. It stores compact packet summaries, receipts, and anomaly classes so later runs can be compared without promoting smoke tests into theorem claims.

!! Current Run

The current local run produced:

~~~
erdos_gyarfas:
  verified_has_power_two_cycle: 5
erdos_selfridge:
  invalid_packet: 2
  finite_smoke_pass: 2
erdos_mollin_walsh:
  finite_smoke_pass: 3
~~~

For the Gyárfás packets, every tested circulant graph packet emitted explicit power-of-two cycle witnesses. This is evidence that the new packet gate can avoid the earlier detector-anomaly shape.

For Selfridge and Mollin-Walsh, the output is only finite smoke evidence.

!! Claim Boundary

No theorem-level result is claimed.

The harness emits:

* packet receipts,
* verifier status,
* finite smoke classifications,
* anomaly classifications,
* a FAMM matrix for cross-run comparison.

Promotion rule: only verified packets promote. Finite smoke tests remain finite.
```

=== Erdos DAG FAMM Historical Run Note

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Erdos DAG FAMM Historical Run Note.tid`

Hash: `1cfdf5a3c58dad99be337e9ca3b480d535323e8940796f304dcba46096a2baf8`

```text
! Erdos DAG FAMM Historical Run Note

This tiddler preserves an older DAG + FAMM interpretation note because it remains useful as a comparison point for the current receipt-first harness.

!! Historical Summary

Older post summary:

~~~
Erdos-Gyarfas:
  Previous result: False
  Refined DAG + FAMM result: True
  FAMM metrics:
    engram_strength: 20.85
    delay_diversity: 3.00
  historical_interpretation:
    Temporal structure appeared to influence cycle formation.

Erdos-Mollin-Walsh:
  Previous result: False
  Refined DAG + FAMM result: False
  DAG metrics:
    acyclic: 100%
    temporal_density: 82.11%
  FAMM metrics:
    engram_strength: 2701.89
    delay_diversity: 2.67
  historical_interpretation:
    Consecutive triples of powerful numbers were found regardless of temporal structure.
~~~

Older post conclusion:

~~~
Erdos-Gyarfas:
  DAG + FAMM changed the harness result from False -> True.

Erdos-Mollin-Walsh:
  DAG + FAMM did not change the harness result.
~~~

!! Corrected Reading

The useful durable claim is not theorem-level.

Corrected claim:

~~~
DAG + FAMM changed the finite harness behavior for the Gyárfás experiment.
DAG + FAMM did not change the finite harness behavior for the Mollin-Walsh experiment.
~~~

Do not promote this into:

~~~
The Erdős-Gyárfás conjecture is true for temporally structured graphs.
The harness proves or disproves either conjecture.
~~~

The safer statement is:

~~~
Generated temporally structured graph samples emitted power-of-two cycle witnesses in the refined harness.
That suggests the original random/detector path was brittle and that temporal packet structure is a useful diagnostic coordinate.
~~~

!! Relation To Current Harness

Current card: Erdos DAG FAMM Investigation

Current harness artifacts:

...
```

=== Four Primitive FPGA Acceleration Research

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Four Primitive FPGA Acceleration Research.tid`

Hash: `7f4d1c439bfa520c9c0bb454851b564577edeb1f5d11f8ce3b1b9d1380a9eebe`

```text
! Four Primitive FPGA Acceleration Research

This tiddler tracks FPGA acceleration as a research subject for the four-primitives framework.

The useful claim is:

~~~
FPGA surfaces can accelerate witness production, pruning, packetized transforms, and bounded residual search.
They do not replace theorem verification or repair detector bugs.
~~~

!! Primitive Mapping

| Primitive | FPGA fit | First useful kernel |
| Field Primitive / ρ(x⃗) | strong | parallel reductions, densities, counters, bounded aggregations |
| Spectral Primitive / C = UΛUᵀ | conditional | SpMV, power iteration, spectral buckets, filters; not full arbitrary eigensolve first |
| Shear Primitive / G = AᵀA | conditional | fixed-point small/medium matrix products, variance accumulators, Q16.16 DSP pipelines |
| Packet Primitive / Γᵢ | strong | pattern matching, symbol substitution, witness receipts, CRC/hash lanes |
| Erdos DAG FAMM Investigation | strong if bounded | frontier queues, delay lines, resumable packet state, temporal gates |

!! Target Split

Tang Nano 9K:

~~~
USB/UART framed packet
  -> Q16.16 primitive kernel
  -> tiny DAG/FAMM state update
  -> witness receipt
  -> host verifier
~~~

Use Tang9K for physical witnessing and tiny kernels, not large graph speedup claims.

PCIe-class FPGA / N3000-style target:

~~~
host pinned memory / DMA ring
  -> surface tiles
  -> reduction / packet / SpMV / fixed-point DSP kernels
  -> receipt ring
  -> CPU/GPU verifier
~~~

Use PCIe FPGA for well-shaped streaming kernels, batched reductions, fixed-point DSP banks, and packet receipts.

!! Conservative Feasibility

Strong first targets:

* field-density reductions
* packet primitive receipts
* symbol substitution / Hutter-style token surfaces
* bounded DAG/FAMM state machines
...
```

=== Quandela Noise Residual Shaver

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Quandela Noise Residual Shaver.tid`

Hash: `c58a0ac1fe756de59af0737fe9ace9b780499002d1cee25bcd0f0b5e60dda631`

```text
! Quandela Noise Residual Shaver

This tiddler records the dry-run rule for treating a noisy photonic environment as a residual-shaving skin over the Quandela tasking surface.

Durable source: 4-Infrastructure/shim/quandela_noise_residual_shaver.py

Receipt: 4-Infrastructure/shim/quandela_noise_residual_shaver_receipt.json

Curriculum: 4-Infrastructure/shim/quandela_noise_residual_shaver_curriculum.jsonl

!! Principle

Use the photonic noise environment as a residual shaver only for uncertainty that is already sampling-distribution shaped; block residuals that are proof debt, model bias, or access control.

!! Claim Boundary

Dry-run routing receipt only. No Perceval execution, no Quandela cloud job, no token handling, no QPU usage, and no theorem/solver claim.

For the compression roadmap, this surface is treated only as an uncontrolled noisy recovery probe. No claim is made that the remote environment implements, endorses, or intentionally supports the compression architecture. Recovered outputs must be judged by local canonical hash checks.

!! Jobs

* pcvl_local_triangle_smoke -> activation local_sim_noise_sweep_candidate_after_perceval_install; score 0.6000; floor 0.0200
* pcvl_compression_kernel_probe -> activation local_sim_noise_sweep_candidate_after_perceval_install; score 0.7778; floor 0.0400
* quandela_remote_residual_hold -> activation held_remote_noise_candidate_requires_token_provider_budget_manual_submit; score 0.5556; floor 0.1600

!! Links

* Quandela Job Tasking Surface
* Remote Compression Test Ladder
* MCP Bus Live Safe Probe
* OpenClaw Shared Bus Surface
```

=== Thermodynamic Computing Surface Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Thermodynamic Computing Surface Prior.tid`

Hash: `f1b27907fa8a845006403f456dabb4a4861b7de5be8243cdb20561c0f5b7a386`

```text
! Thermodynamic Computing Surface Prior

This tiddler records the Live Science / Physical Review Letters thermodynamic-computing item as a substrate prior for the Research Stack.

Source: https://www.livescience.com/technology/computing/thermodynamic-computer-can-mimic-ai-neural-networks-using-orders-of-magnitude-less-energy-to-generate-images

Published: 2026-02-21

Primary paper noted by the source: Stephen Whitelam, "Generative Thermodynamic Computing", Physical Review Letters, 2026.

!! Core Read

The article describes a thermodynamic/probabilistic computing approach that generates simple images from noise. Instead of suppressing thermal noise until it becomes negligible, the system treats noise as a useful computational resource.

The useful Research Stack abstraction is:

~~~
THERMODYNAMIC_NOISE_SURFACE =
  programmed coupling strengths
  + thermal/noisy fluctuations
  + equilibrium or near-equilibrium dynamics
  + interpreter / sampler
  + receipt boundary
~~~

This is directly adjacent to the Quandela Noise Residual Shaver: both treat a noisy substrate as a residual transformer rather than a deterministic processor.

!! Stack Mapping

* Quandela Noise Residual Shaver -> photonic sampling/noise skin over a quantum tasking surface
* Biological Reservoir Surface Prior -> living adaptive dynamics as reservoir prior
* Math Logogram Surface Compiler -> symbolic compression before routing into strange substrates
* N-Space LLM Pipeline Tuning -> compression-first model-routing doctrine
* Cursed Doom Goals -> feedback-loop substrate probes, not practical rendering claims

!! Primitive

~~~
ThermodynamicNoiseTask =
  target_distribution
  + coupling_program
  + noise_source
  + sampler_trace
  + reconstruction_rule
  + residual_receipt
~~~

The candidate rule is:

~~~
...
```

=== Biological Reservoir Surface Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Biological Reservoir Surface Prior.tid`

Hash: `e17f7cf954a2e488ae904a463096f06bc8e80e0c0610f1dd69770c001bf24f22`

```text
! Biological Reservoir Surface Prior

This tiddler records the Live Science / Cortical Labs biological-computing item as a substrate prior for the Research Stack.

Source: https://www.livescience.com/technology/computing/new-data-center-will-be-partially-powered-by-human-brain-cells-for-the-first-time

Published: 2026-04-28

!! Core Read

Cortical Labs is described as building small biological-computing facilities around CL1 systems: lab-grown human neurons on silicon chips, interfaced through microelectrode arrays, life-support systems, and software that translates between biological activity and digital input/output.

For this stack, the useful abstraction is not "brain cells as CPUs." The useful abstraction is:

~~~
BIO_RESERVOIR_SURFACE =
  adaptive living dynamics
  + electrode I/O
  + software interpreter
  + metaprobe receipt layer
~~~

The source article frames the system as closer to reservoir computing than instruction execution: the living neural substrate transforms inputs into complex activity patterns, and external software interprets those patterns.

!! Stack Mapping

* Tang9K Routed Template Witness -> deterministic micro-reservoir / LED address witness
* Quandela Noise Residual Shaver -> stochastic photonic residual-shaving skin
* OpenClaw Shared Bus Surface -> local control bus / routing membrane
* MCP Bus Live Safe Probe -> read-only tool surface with receipts
* Physics Math LLM Metaprobe Audit -> observer, classifier, and claim-boundary verifier
* Biological reservoir surface -> adaptive substrate prior for sparse, noisy pattern selection

!! Claim Boundary

Use this as an adaptive reservoir prior only.

Do not claim:

* deterministic compute equivalence with CPU/GPU/FPGA surfaces
* theorem proof
* scalable data-center readiness
...
```

=== Monocurl Interactive Math Animation Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Monocurl Interactive Math Animation Prior.tid`

Hash: `faf7f6b72ba081e062cfa4e208166909e1f4fef4b8681ceae74134fe5141b505`

```text
! Monocurl Interactive Math Animation Prior

This tiddler records Monocurl as a possible interactive math-animation surface for the Research Stack.

Source: https://www.reddit.com/r/rust/comments/1t69xsg/monocurl_interactive_math_animation_language_and/

Project site: https://monocurl.github.io/

!! Core Read

The Reddit post describes Monocurl as an open-source, programmatic math animation language and editor written in Rust with GPUI. Its main differentiator is live interactivity: scenes can be previewed and manipulated while developing instead of repeatedly rendering static animation outputs.

The author also describes it as Manim-inspired, but more focused on GPU-backed live preview, presentation mode, and a custom language designed around animation.

!! Stack Mapping

Useful Research Stack role:

~~~
MONOCURL_VISUALIZATION_SURFACE =
  math scene grammar
  + live preview
  + parameter controls
  + GPU-backed rendering
  + export / teaching artifact
~~~

This is not a theorem prover and not a numerical solver. It is a visual instrumentation layer.

Candidate surfaces:

* Erdos DAG FAMM Investigation -> animate temporal packet flow and FAMM memory updates
* Erdos DAG FAMM Historical Run Note -> compare old vs receipt-first harness behavior
* Four Primitive FPGA Acceleration Research -> show packet, field, shear, and spectral lanes
* Quandela Noise Residual Shaver -> animate residual components and noise-aligned shaving
* Thermodynamic Computing Surface Prior -> animate diffusion/noise reversal as a surface process
* Biological Reservoir Surface Prior -> animate reservoir input/output traces
* Cursed Doom Goals -> visualize cursed substrate transition oracles without pretending they render frames

!! Candidate Primitive

~~~
MathAnimationScene =
  source_receipt
...
```

=== Typst Math Typesetting Surface Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Math Typesetting Surface Prior.tid`

Hash: `d6b1e9287c5cdb71e76d347611c748e4bcbce3554a66993659d78b429a8883a1`

```text
! Typst Math Typesetting Surface Prior

This tiddler records Typst as a candidate math/document rendering surface for the Research Stack.

Source: https://github.com/typst/typst

Project: https://typst.app/

Package registry: https://typst.app/universe

!! Core Read

Typst is a Rust-based, markup-driven typesetting system intended to be powerful like LaTeX while being easier to learn and faster to iterate with. The repository contains the compiler and CLI for local document compilation.

Useful upstream properties:

* built-in markup for common formatting
* math typesetting
* bibliography management
* integrated scripting
* incremental compilation
* CLI compile/watch workflow
* Rust implementation

!! Stack Mapping

Useful Research Stack role:

~~~
TYPST_DOCUMENT_SURFACE =
  math markup
  + scripted document generation
  + incremental compile/watch
  + PDF/export artifact
  + source receipt hash
~~~

This is a better fit than LaTeX for fast local research packets when the output needs to be readable, inspectable, and generated from receipts.

Candidate uses:

* render Erdos Four Primitive Diagnostics as a compact report
* render Four Primitive FPGA Acceleration Research into a hardware feasibility note
* render Quandela Noise Residual Shaver and Thermodynamic Computing Surface Prior into a substrate-prior brief
* render Math Logogram Surface Compiler examples into visual glyph/math sheets
* provide a possible math-text backend for Monocurl Interactive Math Animation Prior
* format measured or hypothesized metrics through Typst Unify Units Package Prior
* discover diagram/report/presentation packages through Typst Universe Package Registry Prior

!! Candidate Primitive

~~~
TypstReport =
  source_tiddlers
  + source_hashes
  + typst_template
  + compiled_pdf_hash
...
```

=== Typst Universe Useful Package Sweep

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Universe Useful Package Sweep.tid`

Hash: `d2e5ec0a2079e3a37d249ff1a21115913ed84480dd578006d1b40ccce5e913d4`

```text
! Typst Universe Useful Package Sweep

This tiddler records useful Typst Universe packages from the search page and nearby package pages.

Source: https://typst.app/universe/search/

!! Primary Dense-Flow Package

* Typst Auto Bidi Dense Flow Prior -> auto-bidi 0.1.0; automatic bidirectional text direction for Hebrew, Arabic, Farsi, and English/Latin mixed documents.
* bidi-flow 0.1.1 -> fallback automatic RTL/LTR block detection for mixed-direction documents.

!! Report And Paper Templates

* arkheion -> arXiv-style template.
* charged-ieee -> IEEE-style paper template.
* clear-iclr -> ICLR paper template.
* splendid-mdpi -> MDPI-style paper template.
* unequivocal-ams -> AMS-style paper template.
* bloated-neurips -> NeurIPS-style paper template.
* basic-report -> simple report template.

Use for publishable exports only after source hashes and claim boundaries are embedded.

!! Math And Proof Presentation

* physica -> science/engineering math constructs: derivative, differential, vector field, matrix, tensor, Dirac braket, hbar, transpose, conjugate.
* equate -> enhancements for mathematical expressions.
* quick-maths -> math equation shorthands.
* axiom -> notation toolkit for sets, linear algebra, probability, statistics.
* curryst -> inference-rule trees.
* boxproof -> boxed natural-deduction proofs.
* frame-it, showybox, beautiframe -> theorem/environment boxes.

Use for theorem-boundary reports. Do not let visual theorem boxes imply proof.

!! Diagrams, Graphs, And Geometry

* cetz -> general figures, tools, and charts.
* fletcher -> diagrams with nodes and arrows.
* autofletcher -> easier fletcher diagrams.
* autograph -> automatic graph layout for fletcher.
* commute -> proof-of-concept commutative diagrams.
* finite -> finite automata with CeTZ.
...
```

=== Typst Auto Bidi Dense Flow Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Auto Bidi Dense Flow Prior.tid`

Hash: `3ff2006065d4ba851a796cb7ca274dcbcc4b5dba9d95ad774d1212d324493182`

```text
! Typst Auto Bidi Dense Flow Prior

This tiddler records auto-bidi as a Typst dense-flow package prior.

Source: https://typst.app/universe/package/auto-bidi

Import:

~~~
#import "@preview/auto-bidi:0.1.0": *
#show: auto-dir
~~~

!! Core Read

auto-bidi automatically detects bidirectional paragraph language/direction for Hebrew, Arabic, Farsi, and English/Latin text in Typst. It is meant to let mixed RTL/LTR documents flow without manually wrapping each paragraph.

Package metadata:

* version: 0.1.0
* license: MIT
* last updated: 2026-03-05
* minimum Typst version: 0.11.0
* categories: Text, Utility

!! Dense Flow Meaning

For this stack, "dense flow" means mixed symbolic streams can carry more information per visual line without forcing the author to manually manage direction, language shaping, and punctuation placement.

~~~
DENSE_BIDI_FLOW =
  mixed-script symbolic text
  + automatic paragraph direction
  + language-specific shaping
  + math/raw-code exclusion
  + receipt-backed document compile
~~~

This matters for:

* math logograms
* multilingual symbol sheets
* compact proof/receipt notes
* right-to-left symbolic annotations
* compressed glyph dictionaries
* human-inspectable mixed language reports

!! Useful API

* auto-dir -> document-level show rule
* detect-lang(body) -> returns he, ar, fa, or en
* detect-dir(body) -> returns rtl or ltr
* force-lang(lang, body) -> force a language on a block
* rl(body) / lr(body) -> force RTL/LTR spans
* sethebrew, setarabic, setfarsi, setenglish, setauto
* r, l, hechar, archar, enchar -> invisible direction/language hints

Important behavior: math equations, raw text, and code blocks are ignored and stay LTR.

!! Fallback

Fallback package: bidi-flow.

Source: https://typst.app/universe/package/bidi-flow

...
```

=== Typst Omindirection Plugin Surface

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Omindirection Plugin Surface.tid`

Hash: `e1eab0db8fe92b025f4ad3f3966316105aea9bbf2cb9c16a5d3ee49b9f22ed05`

```text
! Typst Omindirection Plugin Surface

This tiddler records the repo-local omindirection Typst plugin surface for dense logogram flow.

Durable source: 6-Documentation/reports/typst/omindirection.typ

Backend prior: Typst Auto Bidi Dense Flow Prior

!! Core Idea

omindirection treats direction as an explicit field on symbolic atoms rather than a hidden paragraph property.

~~~
OMINDIRECTION =
  auto-bidi prose backend
  + explicit atom direction
  + explicit chirality field
  + optional 360-degree chiral phase
  + optional torsion value
  + optional temporal value
  + optional rounding rule
  + optional residual sidecar
  + optional language forcing
  + tone/color class
  + mirrored LTR/RTL rows
  + compile receipt
~~~

This is the layer for logograms: dense symbols stay isolated and inspectable, while natural-language prose can still use automatic bidirectional flow.

The broader modeling prior is Epigenetic Go-Tile Meta-Manifold: tone, chirality, and phase act like mutable expression marks, while atom placement behaves like a local Go tile with liberties, captures, and territory.

!! Exposed Helpers

~~~
#import "omindirection.typ": omi-show, omi-atom, omi-flow, omi-mirror, omi-demo

#omi-atom("Gamma_i", dir: "ltr", tone: "witness")
#omi-atom("Gamma_i", dir: "ltr", chirality: "left")
#omi-atom("Gamma_i", dir: "ltr", chirality: "ambidextrous", phase: 90)
#omi-chiral360("Gamma_i", 270, dir: "rtl", tone: "residual")
#omi-static-target("Hutter-token", 42, 7, 1024)
#omi-rehydratable("rounded-core", "q8", "sidecar-a13f", phase: 42, temporal: 1024)
#omi-flow(("rho", "C=U Lambda U^T", "G=A^T A", "Gamma_i"), dir: "ltr")
#omi-flow(("עד", "שער", "קבלה"), dir: "rtl", lang: "he")
#omi-mirror(("field", "packet"), ("עד", "קבלה"))
#omi-chiral-pair("Gamma_i")
~~~

Tone classes:

...
```

=== Typst Logogram Bidi Layer

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Logogram Bidi Layer.tid`

Hash: `e8b75b24fd2f51e67f3b9ffcdbfe115b8d6b295ab3383c75eea1874a4985f9d2`

```text
! Typst Logogram Bidi Layer

This tiddler records the repo-local bidirectional logogram layer built on top of auto-bidi.

Durable source: 6-Documentation/reports/typst/logogram-bidi.typ

Upstream package: https://typst.app/universe/package/auto-bidi

!! Core Idea

The upstream plugin handles paragraph-level direction and language hints. The repo-local layer adds a stricter symbolic rule:

~~~
LOGOGRAM_BIDI_LAYER =
  auto-bidi prose flow
  + protected logogram atoms
  + explicit RTL/LTR atom direction
  + dense flow rows
  + compile receipt
~~~

This lets mixed prose and symbolic cells share one document without letting the bidirectional text algorithm tear apart dense math/logogram packets.

!! Exposed Helpers

~~~
#import "logogram-bidi.typ": logogram-atom, logogram-flow, logogram-demo

#logogram-atom("Gamma_i")
#logogram-flow(("rho", "C=U Lambda U^T", "G=A^T A", "Gamma_i"))
#logogram-flow(("עד", "שער", "קבלה"), dir: "rtl")
~~~

!! Claim Boundary

This layer is a document-flow and visual encoding helper. It does not validate symbolic semantics, translation, math, compression ratios, or theorem truth.

Promotion requires:

* upstream package version
* repo-local wrapper hash
* Typst source hash
* compiled output hash
* explicit logogram mapping table

!! Links

* Typst Auto Bidi Dense Flow Prior
* Typst Universe Useful Package Sweep
* Math Logogram Surface Compiler
* Typst WUBRG Color Code Prior
* Substrate Prior Typst Pipeline
```

=== Typst WUBRG Color Code Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst WUBRG Color Code Prior.tid`

Hash: `2ca64858db5edc03b78087ce2a0609deedc310e1939f4601602ca163584f40f8`

```text
! Typst WUBRG Color Code Prior

This tiddler records wubrg as an optional color/glyph coding package prior for Typst reports.

Source: https://typst.app/universe/package/wubrg

Import:

~~~
#import "@preview/wubrg:0.1.0": mana
~~~

!! Core Read

wubrg displays Magic: The Gathering mana symbols in Typst documents. The package exports a mana function that can render symbol sequences such as:

~~~
#mana[g]
#mana[g/w]
#mana[5u]
#mana[1g{g/w/p}w]
~~~

Package metadata:

* version: 0.1.0
* license: MIT
* last updated: 2025-12-19
* minimum Typst version: 0.14.0
* category: Visualization

!! Why It Might Be Useful Here

The useful part is not game semantics. The useful part is a compact, recognizable five-color glyph vocabulary with hybrid symbols and generic numeric counters.

Potential mapping:

~~~
W = witness / lawful / verified
U = unknown / inquiry / unresolved
B = boundary / blocked / hold
R = residual / risk / anomaly
G = growth / route / accepted promotion
~~~

Hybrid symbols can mark mixed states:

~~~
W/U = verified but still under inquiry
B/R = blocked by residual risk
G/W = promoted with witness
~~~

This could become a dense visual channel for:

* metaprobe audit tables
* solved-problem verifier outputs
* package promotion states
* Tang9K LED-state legends
* theorem/proof boundary badges
* compression/residual status sheets

!! Claim Boundary

wubrg is a presentation/color-coding aid only. It does not validate package quality, mathematical truth, solver correctness, compression quality, or hardware behavior.

Every operational use needs:

* explicit local mapping table
* package version
* import line
* Typst source hash
* compiled output hash
* claim boundary

!! Links

* Typst Universe Useful Package Sweep
* Typst Universe Package Registry Prior
...
```

=== Typst Unify Units Package Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Unify Units Package Prior.tid`

Hash: `e859bd0fc290bd040f4cc8943edf28d4bf0017c4235fb1e27d0a4bbe276bcbc6`

```text
! Typst Unify Units Package Prior

This tiddler records the Typst unify package as a metrics-formatting prior for Research Stack reports.

Package import:

~~~
#import "@preview/unify:0.8.0": num, qty, numrange, qtyrange
~~~

!! Core Read

unify is a Typst package for typesetting numbers, quantities, units, and ranges. It is conceptually similar to LaTeX siunitx, though less mature.

Useful functions:

* num -> parsed numbers, scientific notation, symmetric/asymmetric uncertainties
* qty -> number plus unit
* numrange -> numeric ranges, exponent factoring, delimiter control
* qtyrange -> ranges with units
* unit -> word or symbolic unit parsing

Supported unit classes currently include physical, monetary, and binary units.

!! Stack Role

Use Unify to make numeric receipts readable without losing exactness.

Candidate metrics:

* FAMM engram strength
* FAMM delay diversity
* DAG temporal density
* noise shave score
* post-noise residual floor
* FPGA speedup hypotheses
* cycle witness counts
* source/hash counts
* timings and byte sizes

!! Example

~~~
$ num("-1.32865+-0.50273e-6") $
$ qty("1.3+1.2-0.3e3", "erg/cm^2/s") $
$ numrange("1,1238e-2", "3,0868e5") $
$ qtyrange("1e3", "2e3", "meter per second squared") $
~~~

Research Stack style:

~~~
$ num("20.85") $  // FAMM engram strength
$ num("3.00") $   // delay diversity
$ qty("82.11", "percent") $  // temporal density
$ numrange("2", "20") $  // conservative FPGA speedup range
~~~

!! Claim Boundary

Unify improves metric presentation only.

Do not claim:

* metric validation
* theorem proof
* unit correctness without source receipts
* package availability until Typst compile succeeds

!! Pipeline Rule

Typst reports may import Unify only when:

* the report source keeps source hashes
...
```

=== Typst Universe Package Registry Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Universe Package Registry Prior.tid`

Hash: `8a642c328e83ea8bfbeadfa4b09b604a5fc9692fc0acd6fc931ee6bf491304ac`

```text
! Typst Universe Package Registry Prior

This tiddler records Typst Universe as the package/template registry prior for Research Stack document surfaces.

Source: https://typst.app/universe

!! Core Read

Typst Universe is the public package and template index for Typst. It exposes package search, templates, categories, and submission paths.

Useful observed categories:

* packages
* templates
* search
* categories
* visualization
* report
* paper
* presentation
* scripting
* utility

Fuller package selection pass: Typst Universe Useful Package Sweep

!! Notable Packages For This Stack

Essential packages listed on the Universe page:

* cetz -> figures, tools, and charts
* touying -> presentation slides
* unify -> SI units and quantities
* glossarium -> glossary support

Dense-flow package:

* Typst Auto Bidi Dense Flow Prior -> automatic bidirectional text/language flow for dense mixed-script documents

Draw/visualization packages listed:

* fletcher -> commutative diagrams with nodes and arrows
* quill -> quantum circuit diagrams
* timeliney -> Gantt charts
* Typst Alchemist Molecule Package Prior -> skeletal formulas via CeTZ
* typshade -> multiple-sequence alignment visualization for bioinformatics

Paper/report candidates:

* arkheion -> arXiv-style template
* starter-journal-article -> journal article starter
* splendid-mdpi -> MDPI-style paper template

!! Stack Mapping

~~~
TYPST_UNIVERSE_SURFACE =
  package registry
  + template registry
  + document capability discovery
  + version-pinned imports
  + compile receipt boundary
~~~

Use it to choose report packages, not to validate mathematical claims.

Candidate mappings:

* Typst Unify Units Package Prior -> metric formatting
* quill -> quantum/Quandela circuit diagrams
* fletcher -> DAG/FAMM diagrams
...
```

=== Typst Typshade Bioalignment Package Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Typshade Bioalignment Package Prior.tid`

Hash: `9a5fad3e732a905cd4942daf7ce15ea1643c7918568e18a22062dca8350953a0`

```text
! Typst Typshade Bioalignment Package Prior

This tiddler records typshade as a Typst package prior for bioinformatics alignment visualization.

Source: https://typst.app/universe/package/typshade

Import:

~~~
#import "@preview/typshade:0.1.1": *
~~~

!! Core Read

typshade is a Typst-native package for visualizing multiple-sequence alignments in bioinformatics. It centers on shade(...) and supports annotations, logos, structure tracks, graph tracks, motif maps, and publication-style alignment figures.

Package metadata from Typst Universe:

* version: 0.1.1
* last updated: 2026-05-07
* first released: 2026-05-05
* minimum Typst version: 0.13.0
* license: GPL-2.0-only
* categories: Visualization, Components

!! Useful Helpers

Observed helpers include:

* shade(...)
* publication
* motif-map
* structure-map
* logo-analysis
* overview
* sequence-logo
* subfamily-logo
* structure-tracks(...)
* percent-identity(...)
* percent-similarity(...)
* similarity-table(...)
* alignment-data(...)
* parse-alignment(...)

!! Stack Mapping

~~~
TYPSHADE_ALIGNMENT_SURFACE =
  sequence alignment
  + motif/structure/graph tracks
  + logo or similarity summary
  + Typst figure
  + source alignment hash
  + claim boundary
~~~

This connects to the earlier DNA/model-compression thread: biological sequence alignments can be treated as compact symbolic fields, and Typshade can render their conserved structure without pretending to perform biological inference by itself.

Candidate uses:

* visualize DNA/protein compression examples
* render motif maps for sequence-prior reports
* compare symbolic/logogram encodings against biological sequence alignments
* provide a presentation surface for Genomic Sequence Prior Surface
* support future cross-domain eigenvector notes over sequence domains

...
```

=== Typst Alchemist Molecule Package Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Alchemist Molecule Package Prior.tid`

Hash: `81eba5101fff143219d9cb0ebb4357518c5134bad123649d938de18823531a94`

```text
! Typst Alchemist Molecule Package Prior

This tiddler records alchemist as a Typst package prior for molecule and skeletal-formula visualization.

Source: https://typst.app/universe/package/alchemist

Import:

~~~
#import "@preview/alchemist:0.1.6": *
~~~

!! Core Read

alchemist is a Typst package for rendering skeletal formulae. It is based on the LaTeX chemfig package, but aims to provide a Typst-native interface rather than reproducing chemfig one-to-one.

Package metadata from Typst Universe:

* version: 0.1.6
* last updated: 2025-06-06
* first released: 2024-08-14
* minimum Typst version: 0.13.1
* license: MIT
* disciplines: Education, Chemistry, Biology
* categories: Visualization, Paper

!! Stack Mapping

~~~
ALCHEMIST_MOLECULE_SURFACE =
  molecule / fragment graph
  + bond/link specification
  + CeTZ drawing layer
  + rendered formula
  + source hash
  + claim boundary
~~~

This is a visualization/documentation surface for molecule-shaped symbolic structures. It can help present organic-molecule examples, compression motifs, and chemistry-domain priors without turning the document renderer into a chemistry engine.

Candidate uses:

* render organic molecule examples in Molecular Domain Prior Surface
* visualize chemistry-side custom logogram symbols
* pair with Typst Typshade Bioalignment Package Prior for sequence + molecule reports
* provide clean figures in substrate-prior PDFs
* support chemistry/biology package discovery under Typst Universe Package Registry Prior

!! Claim Boundary

Alchemist renders molecule diagrams. It does not validate chemistry.

Do not claim:

* chemical correctness
* synthesis feasibility
* biological activity
* safety/toxicity assessment
* model-training validity
* compile success until local Typst package smoke passes

...
```

=== OpenClaw Shared Bus Surface

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/OpenClaw Shared Bus Surface.tid`

Hash: `c8b451a67aefd46515c69ad9c15be0cb50640229938929f97639053836da838a`

```text
! OpenClaw Shared Bus Surface

OpenClaw is pulled as a pinned external snapshot and treated as a local-first shared bus/control-plane candidate.

Capability accounting: OpenClaw Capability Surface

Snapshot path: 5-Applications/tools-scripts/external/openclaw
Commit: 8e88c7b297685c7c60215408fc4cf4ce67f36825
Package version: 2026.5.6

Durable source: 4-Infrastructure/shim/openclaw_shared_bus_surface.py

Receipt: 4-Infrastructure/shim/openclaw_shared_bus_surface_receipt.json

Curriculum: 4-Infrastructure/shim/openclaw_shared_bus_surface_curriculum.jsonl

Config skeleton: 4-Infrastructure/shim/openclaw_shared_bus_config.example.json

!! Claim Boundary

OpenClaw is treated as a bus/control-plane candidate. It is not run or trusted until loopback, pairing, sandbox, and metaprobe receipt gates pass.

!! Surface Mapping

* Gateway -> shared bus/control plane. Gate: loopback-only first; no non-loopback bind without explicit auth and pairing receipt
* sessions/routing -> bounded worker lanes for AgentID/shared identity tasks. Gate: one task receipt per lane before memory write
* channels/plugins -> transport adapters for chat/API/hardware event ingress. Gate: disable public inbound channels until allowlist and sandbox receipts exist
* skills -> local tool contract layer for metaprobe/verifier actions. Gate: skill outputs must include source path, hash, lawful flag, and claim boundary
* sandboxing -> containment membrane for non-main and remote sessions. Gate: non-main sessions default to sandboxed/receipt-only writes

!! Activation Plan

* Keep external snapshot pinned and inactive.
* Generate loopback-only OpenClaw config skeleton.
* Route one local metaprobe verifier task through a dry-run event adapter.
...
```

=== OpenClaw Capability Surface

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/OpenClaw Capability Surface.tid`

Hash: `bac49972b72e22bd5c6535c37bda635f7704bea15e957dc230a4e52d7282b448`

```text
! OpenClaw Capability Surface

This tiddler records what OpenClaw can achieve for the Research Stack if it is promoted through receipt gates.

Existing substrate card: OpenClaw Shared Bus Surface

Durable receipt: 4-Infrastructure/shim/openclaw_shared_bus_surface_receipt.json

Pinned snapshot:

~~~
path: 5-Applications/tools-scripts/external/openclaw
remote: https://github.com/openclaw/openclaw.git
branch: main
commit: 8e88c7b297685c7c60215408fc4cf4ce67f36825
package version: 2026.5.6
source fingerprint: f4ebf3b112d4d48edb87c4243d94cdaadb62ec2d23ef8f186f431d7c230ce393
~~~

!! Core Read

OpenClaw can act as a local-first shared bus and control-plane candidate:

~~~
agents
  -> gateway
  -> sessions/routing
  -> channels/plugins
  -> skill contracts
  -> receipt-bearing task events
  -> bounded memory writes
~~~

It should not be treated as a theorem source, unbounded tool executor, raw secret store, or public inbound channel.

!! What It Can Achieve

1. Shared agent bus

OpenClaw can coordinate multiple local or remote agent lanes through one gateway-like surface.

Use:

* AgentID/shared-identity task events
* metaprobe job dispatch
* solver/verifier lane routing
* report generation task tracking

2. Receipt-backed task lifecycle

The local event contract already defines:

~~~
task_started:
  agent_handle
  task_id
  title
  state
  timestamp

task_completed:
  agent_handle
  task_id
  receipt_path
  receipt_hash
  lawful
  claim_boundary
~~~

This makes the bus useful as a provenance surface rather than only a message router.

3. Bounded memory write coordination

The memory-write contract requires:

~~~
key
value_hash
source_receipt_path
claim_boundary
~~~

...
```

=== Epigenetic Go-Tile Meta-Manifold

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Epigenetic Go-Tile Meta-Manifold.tid`

Hash: `64d00c9d078be287bdf7d18946d2b81d471dbb0a827a0fcf3ff6c4c6a7308d08`

```text
! Epigenetic Go-Tile Meta-Manifold

This tiddler records the working model:

~~~
EPIGENETIC_GO_TILE_META_MANIFOLD =
  mutable expression marks
  + local tile placement
  + liberties
  + capture
  + territory
  + influence field
  + torsion
  + temporal corpus value
  + receipt-backed state transition
~~~

The point is not to claim biological equivalence. The point is to borrow two useful computational shapes:

* epigenetic meta-manifold -> state can be expressed, silenced, biased, inherited, or reweighted without changing the underlying symbol genome
* Go-tile computation -> local placement changes neighborhood liberties, capture pressure, territory, and global influence

!! Primitive Mapping

~~~
symbol genome        = stable logogram vocabulary
epigenetic mark      = mutable expression/tone/chirality/phase/torsion/temporal metadata
tile                 = placed logogram atom
liberty              = open route for future binding/compression
capture              = residual collapse or contradiction isolation
territory            = stable semantic basin
influence            = nonlocal bias field from local tile pressure
torsion              = binding twist or residual stress
temporal value       = corpus-time/order/recurrence marker
ko rule              = anti-loop receipt gate
life/death           = persistent versus eliminated packet cluster
~~~

!! Omindirection Mapping

Typst Omindirection Plugin Surface is the document-side renderer for this model.

~~~
omi-atom =
  payload
  + direction
  + chirality
  + phase degree
  + torsion
  + temporal value
  + tone/status
  + optional language hint
~~~

...
```

=== Hutter Static Target Omindirection Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter Static Target Omindirection Prior.tid`

Hash: `b16e430337a955f4a6d4df55078983a16cdf724a286530f067f9f152746af88e`

```text
! Hutter Static Target Omindirection Prior

This tiddler records how omindirection can carry torsion and temporal values for static compression targets such as Hutter Prize style corpora.

!! Core Read

Static does not mean timeless. A static corpus still has:

* token order
* recurrence intervals
* local context windows
* phrase reuse
* delayed reference
* binding stress
* residual torsion

So each dense logogram atom can carry:

~~~
STATIC_TARGET_ATOM =
  payload_hash
  + direction
  + chirality_phase
  + torsion
  + temporal_index
  + expression_tone
  + receipt_hash
~~~

!! Torsion

torsion measures binding twist: how much the current symbol's local meaning is being forced by remote context, compression pressure, or incompatible neighboring interpretations.

Candidate use:

~~~
torsion = local residual pressure
        + context mismatch
        + dictionary substitution stress
        + long-range reference bend
~~~

Low torsion means the token compresses cleanly in its local basin.

High torsion means the token may need a different substitution, delayed binding, or explicit exception receipt.

!! Temporal Value

temporal records order, recurrence, or delayed dependency. For a static corpus, this is not wall-clock time; it is corpus-time.

Examples:

~~~
temporal = byte offset
temporal = token index
temporal = phrase recurrence distance
temporal = dictionary generation
temporal = metaprobe pass number
~~~

!! Omindirection Lowering

~~~
#omi-static-target("Hutter-token", 42, 7, 1024)
~~~

Meaning:

* payload: Hutter-token
* chiral phase: 42
* torsion: 7
* temporal index: 1024

!! Why This Increases Density

Without torsion/temporal metadata, the compressor only sees a symbol and its immediate surface.

With torsion/temporal metadata, the same symbol can represent:
...
```

=== PAQ Style Compression Review

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/PAQ Style Compression Review.tid`

Hash: `e36d4ffb329d09a4a42b9a824b92a2ea0008fdbdad0dc636174736a6e18df45f`

```text
! PAQ Style Compression Review

This tiddler records a PAQ-style compression review for the Omindirection/logogram stack.

Sources:

* https://mattmahoney.net/dc/dce.html
* https://mattmahoney.net/dc/zpaq.html

!! Core Read

PAQ-style compression is best understood as:

~~~
input history
  -> many context models
  -> bit probability predictions
  -> adaptive context mixing
  -> probability refinement / SSE
  -> arithmetic or asymmetric binary coding
  -> exact reversible bitstream
~~~

The important separation is:

* modeling predicts the next bit or symbol
* coding spends roughly -log2(p) bits for the realized event

Matt Mahoney's compression notes emphasize the hard boundary: no universal lossless compressor can compress every input, and compressed data generally cannot be recursively compressed by the same method. That is the guardrail for all Hutter-style claims.

!! PAQ-Style Mechanics

PAQ/context-mixing systems typically:

* predict one bit at a time
* use multiple models, not one suffix context
* allow contexts to be arbitrary functions of history
* mix predictions with adaptive weights
* refine probabilities through secondary symbol estimation
* entropy-code the resulting bit probability

Useful model families:

* short byte/bit contexts
* long match contexts
* word/phrase contexts
* sparse contexts with gaps
* record/column contexts
* file-type-specific preprocessors
* dictionary transforms for static text benchmarks

!! Hutter Connection

For Hutter Prize style static text, the lesson is not "use PAQ directly" but:

~~~
static corpus
  -> contextual predictors
  -> adaptive mixture
  -> dictionary/substitution transform
  -> exact reversible coder
  -> byte-count receipt
~~~

...
```

=== Rehydratable Non-Core Rounding Prior

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Rehydratable Non-Core Rounding Prior.tid`

Hash: `9245971fe6512422b56b7fd3c55613df8a8407bfac07fd771d8a20dddd3580fc`

```text
! Rehydratable Non-Core Rounding Prior

This tiddler records the compression pattern:

~~~
lossy-looking non-core rounding
  + residual sidecar
  + rehydration rule
  + receipt
  = lossless reconstruction
~~~

If reconstruction is 1:1 after rehydration, the whole transform is lossless. The rounded projection is only a compact working surface.

!! Core / Non-Core Split

~~~
core payload      = information that must remain directly visible
non-core payload  = detail allowed to leave the visible surface
rounded core      = coarse projection used for routing/modeling
residual sidecar  = exact difference needed to reconstruct
rehydration rule  = deterministic inverse transform
receipt           = hash proving rehydration equality
~~~

!! Transform

~~~
original x
  -> rounded projection q(x)
  -> residual r = x - lift(q(x))
  -> stored packet (q(x), r, rule_id, receipt)
  -> rehydrate lift(q(x)) + r
  -> x
~~~

For strings or symbolic payloads, r is not necessarily numeric subtraction. It may be:

* edit script
* exception dictionary
* byte patch
* token sidecar
* case/punctuation restore stream
* ordering restore stream
* omitted whitespace map

!! Omindirection Mapping

~~~
omi-rehydratable("rounded-core", "q8", "sidecar-a13f", phase: 42, temporal: 1024)
~~~

Meaning:

* payload: compact visible surface
* rounding: quantization/projection rule
* residual: exact sidecar identifier
* phase/temporal: orientation and corpus-time

!! Hutter-Style Use

For static text compression, this suggests:

~~~
visible model surface:
  normalized/logogram text

sidecar:
  exact reconstruction patches

benchmark output:
  compressed normalized surface
  + compressed sidecar
  + decompressor
~~~

This is only useful if the combined byte count beats the baseline.

!! Claim Boundary

...
```

=== Omindirection Compression Concept Ledger

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Omindirection Compression Concept Ledger.tid`

Hash: `0393ddc6147b9f80489ab27bd8ef0b0c254635bf49bfcbfc70c143c90020da3d`

```text
! Omindirection Compression Concept Ledger

This tiddler is the accounting card for the recent Omindirection, logogram, Hutter, PAQ, and rehydratable-compression concepts.

It exists so the concepts are not only scattered across individual priors.

!! Core Surface

* Typst Omindirection Plugin Surface -> repo-local Typst plugin surface for explicit direction, tone, chirality, phase, torsion, temporal, rounding, and residual metadata.
* Typst Auto Bidi Dense Flow Prior -> upstream bidirectional prose-flow backend.
* Typst Logogram Bidi Layer -> earlier wrapper for protected logogram atoms.
* Typst WUBRG Color Code Prior -> optional five-color glyph/status vocabulary.

!! Symbol And Logogram Layer

* Math Logogram Surface Compiler -> deterministic symbolic/logogram compiler surface and Tang-compatible glyph payload prior.
* Semantic Topology Compression Regimes -> beautiful folding, ugly pruning, and horrible tearing regimes.
* LLM Compression Architecture Priors -> LLM-as-compression and semantic bottleneck framing.
* Math Logogram Surface Compiler + Typst Omindirection Plugin Surface -> preferred pair: compile symbolic cells, then render them with explicit metadata.

!! Epigenetic / Go-Tile Computation

* Epigenetic Go-Tile Meta-Manifold -> mutable expression marks plus Go-style tile liberties, capture, territory, and influence.

Core mapping:

~~~
symbol genome   -> stable logogram vocabulary
expression mark -> tone/chirality/phase/torsion/temporal/rounding/residual metadata
tile            -> placed omi-atom
liberty         -> open compression/binding route
capture         -> residual collapse or contradiction isolation
territory       -> stable semantic basin
~~~

!! Chiral And Directional Fields

* direction: ltr, rtl, or auto
...
```

=== MathXML Domain Graph Import

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/MathXML Domain Graph Import.tid`

Hash: `bcacd0f9129c9299dfc2925165bb345ef7b1796ad3f2c115d877896fc82ad9e9`

```text
! MathXML Domain Graph Import

This tiddler records the domain graph imported from the Telegram Desktop mathxml.xml file.

Original source:

~~~
/home/allaun/Downloads/Telegram Desktop/mathxml.xml
~~~

Repo-local copy:

~~~
4-Infrastructure/shim/imports/mathxml_domains.graphml
~~~

Receipt:

~~~
4-Infrastructure/shim/mathxml_domain_import_receipt.json
~~~

Source hash:

~~~
6c627dcf4fadab320ee53bf1a0c7545afde5b39f6a58d4e99708955d66075e1d
~~~

!! Graph Summary

~~~
graph id: MathematicalFields
format: GraphML
nodes: 116
edges: 342
categories: 32
edge relationships:
  prerequisite: 239
  enhances: 103
priority counts:
  HIGH: 32
  MEDIUM: 58
  LOW: 26
~~~

!! Domains To Add

* Foundational Extensions -> topological RAM, genus-3 surfaces, branch-cut defects, FAMM basins, PIST witness surfaces, particle spectrum.
* Deep Theoretical Connections -> Lean 4 formalization, OTOM bind primitive, manifold classification, FAMM composition, local-to-global principles.
* Analysis and PDE Deep Dive -> fractional derivatives, quantum foam, branch cuts, FAMM frustration, compression entropy, torsional unwinding.
* Probability and Statistics Deep Dive -> FAMM memory cycles, stochastic frustration, Bayesian inference, search-space exploration, distributed systems.
* Algebra and Number Theory Deep Dive -> integer arithmetic, mass numbers, fractional field, OTOM modules, compression.
* Geometry and Topology Deep Dive -> genus-3 surfaces, hyperbolic geometry, winding numbers, topological RAM, FAMM.
* Mathematical Physics Deep Dive -> fractional unified field, quantum foam, particle spectrum, torsional cosmology, topological RAM.
* Computational and Applied Mathematics -> optimization, search-space pruning, FAMM, fractional derivatives, topological RAM.
...
```

=== Finance Math OTOM Layer

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Finance Math OTOM Layer.tid`

Hash: `62ccc6c8bbca8e00ef6d5422cae760fbc77f239379db354ec00b3dddac2ea136`

```text
! Finance Math OTOM Layer

This tiddler records the dedicated finance math Typst layer for claim packets, temporal shear, ledgers, risk, derivatives, taxation, insurance, monetary issuance, settlement, and audit receipts.

Durable source: typst/otom-style/finance-math.typ

Main spine: typst/otom-style/main.typ

Registry: typst/registries/finance-registry.typ

Receipt: 4-Infrastructure/shim/finance_math_otom_layer_receipt.json

!! Core Framing

Finance math is the mathematics of future-state ownership claims under uncertainty.

For this stack:

~~~
Finance = packetized moral gravity.

debt        = future-binding packet
interest    = temporal shear
collateral  = admissibility anchor
default     = residual escape
liquidity   = path accessibility
insurance   = residual-field pooling
derivatives = synthetic projections over future packet states
accounting  = witness grammar
auditing    = receipt layer
~~~

!! Typst Layer

The active layer is deliberately conservative:

~~~
#import "@preview/physica:0.9.8": *
#import "@preview/axiom:0.1.0": *
#import "@preview/equate:0.3.2": *
#import "@preview/quick-maths:0.2.1": *
#import "@preview/unify:0.8.0": *
#import "@preview/zero:0.6.1": *
#import "@preview/booktabs:0.0.4": *
#import "@preview/tablex:0.0.9": *
#import "@preview/dining-table:0.1.0": *
#import "@preview/lilaq:0.6.0": *
#import "@preview/digestify:0.2.0": *
~~~

metro:0.3.0 is finance-relevant but was demoted to the optional registry because it failed under the repo-local Typst 0.14.2 smoke test with an upstream kelvin symbol error.

!! File Hashes

* typst/otom-style/finance-math.typ -> fe5bbc45be16bda7f86fa7530b31f08523feab9500947321cad01a390b816176
* typst/otom-style/main.typ -> 6d820638f50367cf94ae3943824fcd9c3578e781a13ee668f7e125b65dce0abb
...
```

=== Finance Claim LUT Compression Harness

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Finance Claim LUT Compression Harness.tid`

Hash: `7a0cf1e92720b5247b4f42c16f97b152451700800b17f28b333e39d5cbb8696f`

```text
! Finance Claim LUT Compression Harness

This tiddler records the first reversible FinancialClaimPacket compressor/decompressor harness.

Durable source: 4-Infrastructure/shim/finance_claim_lut_harness.py

Receipt: 4-Infrastructure/shim/finance_claim_lut_harness_receipt.json

Symbol LUT: 4-Infrastructure/shim/finance_claim_symbol_lut.json

Typesetting LUT: 4-Infrastructure/shim/finance_claim_typesetting_lut.json

Curriculum: 4-Infrastructure/shim/finance_claim_lut_harness_curriculum.jsonl

Codec venv: .venv-finance-codecs

Codec requirements: 4-Infrastructure/shim/finance_claim_codec_requirements.txt

!! Purpose

The harness proves the first practical round-trip contract:

~~~
canonical FinancialClaimPacket JSON bytes
  -> symbol LUT
  -> typesetting LUT
  -> compact FCL1 binary token tape
  -> typed FCS1 binary sidecar
  -> decompressor
  -> exact canonical JSON bytes
  -> receipt
~~~

JSON remains the human-readable audit envelope. It is not the embedded wire format.

!! Embedded Format Boundary

The current wire candidate is FCL1, a minimal packed-token tape:

~~~
magic:  FCL1
version: u8
count:   u8 field_count
repeat:
  u16 field_symbol_code
  u8  value_tag
  u16 enum_symbol_code_or_sidecar_index
trailer:
  u32 crc32
~~~

This acts like a packed struct with a symbol codebook. It keeps the field names out of the wire packet.

The typed binary sidecar is FCS1:

~~~
magic:  FCS1
version: u8
count:   u8 literal_count
repeat:
  u16 sidecar_index
  u8  type_code
  u16 value_length
  bytes value_json
  u32 value_crc32
trailer:
  u32 crc32
~~~

Type codes:

* 1: string
* 2: decimal-string
* 3: date-string
* 4: receipt-string

The typesetting/orientation layer now packs omindirection and chirality into a single LUT byte per symbol:

~~~
orientation_code: u8
...
```

=== Remote Compression Test Ladder

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Remote Compression Test Ladder.tid`

Hash: `69fc3961d0be9d27c1dc49f88025ebb41b2b070e7c44e65d2a888d12a3ed7b02`

```text
! Remote Compression Test Ladder

This tiddler records the execution ladder for promoting the finance LUT compressor from local byte-rehydration into controlled remote testing, noisy recovery probes, and burst-scale encoding optimization.

The ladder is:

~~~
local lawful harness
  -> Netcup controlled remote baseline
    -> Quandela uncontrolled noisy recovery probe
      -> H200 burst encoder / optimizer
        -> compact deterministic decoder
~~~

!! Stage 1: Local Lawful Harness

Local remains the source of truth.

Purpose:

* freeze the FCL1 packed-token tape and FCS1 typed sidecar contract
* build the symbol LUT, typesetting LUT, orientation byte, and chirality phase buckets
* run encode/decode/verify/bench locally
* compare against JSON, zlib, CBOR, MessagePack, and Protobuf-style baselines
* emit receipts, hashes, binary fixtures, and wiki artifacts

Acceptance:

~~~
canonical JSON hash == decoded canonical JSON hash
FCL1 checksum verifies
FCS1 checksum verifies
field order remains canonical
unknown enum falls back to typed sidecar
receipt records byte counts and baseline comparisons
~~~

!! Stage 2: Netcup Controlled Remote Baseline

Netcup is the boring reference server.

It should be used before any noisy substrate experiment because it provides a known remote Linux environment with normal logs, predictable CPU/RAM/network behavior, and repeatable command execution.

Purpose:

* prove remote encode/decode reproducibility outside the local workstation
* test artifact transfer, hash receipt validation, and packet integrity
* exercise the virtual high-baud modem decompressor over a real network boundary
* measure latency, streaming, preload-buffer behavior, and hot/cold path rehydration
* stage corpus bundles before H200 rental

Boundary:

~~~
...
```

=== Virtual Baud Reconstruction Layer

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Virtual Baud Reconstruction Layer.tid`

Hash: `fea1aa1777981eeeae2214d8ba1ad0e2d279b6c4f0547cd4978a45ab6f5048bd`

```text
! Virtual Baud Reconstruction Layer

This tiddler records the decompressor architecture concept behind the high-baud modem framing.

The key reframing:

~~~
decompression is controlled signal reconstruction
~~~

The decoder is not merely inflating bytes. It receives a framed reconstruction signal, interprets payload and control lanes, dispatches glyph/kernel/eigen operations, repairs residuals, and commits only when byte-exact receipt checks pass.

!! Name

Formal name:

~~~
Virtual Baud Reconstruction Layer
~~~

Short names:

~~~
VBRL
Manifold Modem
Glyph Baud Layer
Baud Witness Plane
~~~

Repo-local formal anchor:

~~~
0-Core-Formalism/lean/Semantics/Semantics/BraidSerial.lean
~~~

That Lean module already frames braid-encoded serial communication with:

* SerialPacket = (header, payload, bracket, residual)
* BraidFrame as parallel encoded strands plus frame number and phi phase
* EncodedStrand fields for phase accumulator, slot, parity, residue, and bracket
* bracket admissibility as inline error detection
* crossing operations for multiplexing packet frames

!! Core Object

~~~
M_baud = (Sigma, B, C, Phi, Theta, R, W)
~~~

Where:

* Sigma = symbol or glyph alphabet
* B = virtual baud clock / reconstruction tick index
* C = control-bit lane
* Phi = modulation and decoding state
* Theta = kernel dispatch parameters
* R = residual repair stream
* W = witness and receipt stream

One reconstruction step:

~~~
state_t + symbol_t + control_t
  -> state_t+1 + emitted_bytes_t + witness_t
~~~

Project-language translation:

~~~
virtual baud tick = lawful informationalBind event
~~~

!! Lanes

The layer separates:

~~~
DATA lane    -> glyphs, literals, eigen descriptors
CTRL lane    -> mode switches, kernel calls, page/domain structure
...
```

=== Committee Jupyter Book Explanation Plan

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Committee Jupyter Book Explanation Plan.tid`

Hash: `aaee293009eabd21bc559d2285c11117dedda0720476e449e388de708eeaf54a`

```text
! Committee Jupyter Book Explanation Plan

This tiddler records the final explanatory artifact to build when the compression/rehydration considerations are locked.

The committee-facing artifact should be a Jupyter Book, not only a wiki trail or raw receipt bundle.

!! Purpose

The book explains the architecture in a reproducible, reviewable form:

~~~
concept
  -> packet contract
  -> local proof harness
  -> controlled remote baseline
  -> noisy recovery probe
  -> burst optimizer
  -> compact deterministic decoder
  -> limits and claim boundaries
~~~

It should be written for readers who need evidence, not mystique.

!! Proposed Location

Candidate path:

~~~
6-Documentation/reports/jupyter-books/committee-compression-book/
~~~

Candidate generated outputs:

~~~
_build/html/
_build/pdf/
committee_compression_book_receipt.json
~~~

Current scaffold:

~~~
path: 6-Documentation/reports/jupyter-books/committee-compression-book/
receipt: 6-Documentation/reports/jupyter-books/committee-compression-book/committee_compression_book_receipt.json
source_file_count: 17
lawful: true
jupyter_book_module_available: true
html_build_exists: true
html_file_count: 1292
html_bytes: 23990391
html_aggregate_hash: 4f6b9593d87ffab77c1110c9d3e336d242caf44b5876e92a11a8e3981286a720
note: Jupyter Book v2 uses myst.yml; _toc.yml is retained as a legacy scaffold but ignored by the v2 builder.
~~~

!! Book Spine

Proposed chapters:

* 00_executive_summary.md -> one-page overview and claim boundary
* 01_problem_statement.md -> why JSON is the audit envelope but not the wire format
* 02_financial_claim_packet.md -> FinancialClaimPacket as first canonical payload family
* 03_fcl1_fcs1_wire_format.ipynb -> binary packet layout, sidecar layout, checksums, byte examples
...
```

=== Cursed Doom Goals

Source: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Cursed Doom Goals.tid`

Hash: `b9e4b5b48fe1b92c9596077ed8692a33f5b8f8b641e74a71fd6d0bebb5fa31b7`

```text
! Cursed Doom Goals

This tiddler collects intentionally cursed Doom-running ideas that are not practical engineering milestones, but are useful substrate probes.

Core rule:

~~~
If it can almost run Doom, it exposes an input/output loop, state encoding, timing membrane, and residual class.
~~~

!! Claim Boundary

These are not product goals, not performance claims, and not proof of general-purpose compute.

Use them as:

* substrate-abuse jokes
* feedback-loop probes
* compression tests
* reservoir address-space tests
* metaprobe routing exercises

Do not use them as:

* evidence of practical rendering
* evidence of accelerator superiority
* theorem claims
* unconstrained cloud/QPU job justification

!! Goals

* Doom on Tang9K LED reservoir -> framebuffer becomes tiny address witness; useful for Tang9K Routed Template Witness
* Doom on Quandela -> photonic sampler acts as transition oracle; useful for Quandela Noise Residual Shaver
* Doom on biological reservoir -> adaptive feedback probe; useful for Biological Reservoir Surface Prior
* Doom on metaprobe text stream -> WAD state becomes compressed symbolic automaton; useful for Math Logogram Surface Compiler
* Doom on OpenClaw bus -> shared event routing test; useful for OpenClaw Shared Bus Surface

!! Minimal Serious Architecture

~~~
WAD / map state
  -> compressed symbolic room graph
  -> encounter transition kernel
  -> substrate-specific sampler / witness
  -> CPU/GPU reconstructs boring deterministic frame work
  -> metaprobe validates receipt boundary
~~~

The target is not rendering. The target is discovering which substrate can carry which part of the state transition burden.

!! Receipts Required

Every cursed Doom goal needs:

* source asset hash
* compression grammar hash
* substrate route
...
```
