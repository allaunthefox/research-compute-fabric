# Execution Substrate Strategy

This document defines how execution substrates should be used to demonstrate that the
codec path is not overfit to one privileged machine shape.

The goal is not to claim access to one provably isolated physical core in every
environment.
That claim is usually too strong, especially under virtualization or emulation.

The narrower and more defensible claim is:

- one declared execution lane
- one deterministic instruction stream
- one serialized trace
- one auditable state transition contract

If multiple very different execution substrates can honor that same contract, the
system is less credibly dismissed as a one-off machine-specific trick.

## Core Claim

The project should prefer substrate diversity over substrate mystique.

That means:

- do not rely on one magic machine shape
- do not require one privileged vendor stack
- do not let the audit story collapse into "trust this one emulator"
- show that the same declared derivation and verification rules survive across several
  execution surfaces

## Single-Lane Execution Contract

The auditable contract is a single-lane execution contract, not a guaranteed statement
about one visible piece of silicon.

The execution surface should therefore expose:

- a single active instruction pointer or equivalent step cursor
- a single declared writable state surface per step
- serialized trace order
- explicit prohibition on undeclared parallel work inside the audited path
- fixed or bounded thread count in the host process
- affinity pinning where the host allows it

If the host cannot prove one physical core, it should still be able to prove one
declared execution lane.

## Why Multipath Matters

Running the same contract through multiple substrates helps demonstrate:

- the math is portable
- the derivation path is not hand-fit to one quirky executor
- the trace model is not dependent on one vendor implementation
- the platform is less likely to be dismissed as a benchmark illusion

This is especially useful when the public story needs to show discipline without
forcing full disclosure of the private search layer.

## Preferred Substrate Set

The current multipath set should include all of the following, even if they are not
implemented at the same time.

### 1. Classical Ternary Core

This is the closest match to the current VM.

Why it matters:

- native fit for `-1 / 0 / +1`
- smallest conceptual gap from the current trinary derivation path
- easiest substrate for explaining subregister-local transitions

Public value:

- strongest baseline for the declared math
- easiest substrate to explain without cultural baggage

### 2. Tiny RISC-Like 64-Bit Core

This is the boring outsider-trust substrate.

Why it matters:

- people understand RISC-like emulation as ordinary code
- mature step-trace and register-trace ideas already exist around simple CPU cores
- easier to explain to reviewers who do not want to reason about ternary-first design

Public value:

- strongest answer to "can this run on a normal auditable machine"
- good bridge substrate for proof systems and deterministic replay

### 3. 65C816-Style / SNES-Family CPU Core

This is not the cleanest engineering choice, but it is useful as a cultural sanity
check.

Why it matters:

- the machine model is historically small and legible
- many people intuitively understand that it is constrained rather than magical
- it helps show the derivation and trace contract are not dependent on modern wide-core
  assumptions

Public value:

- anti-overoptimization signal
- simple-enough legacy surface for demonstration and historical audit
- extra nerd credibility with technically literate reviewers who know the hardware
- a path toward real physical test boards instead of emulator-only trust
- an execution surface that can be inspected on constrained legacy tooling as well as
  modern hosts

This should be treated as a CPU-core path, not as a whole-console requirement.
The project does not need graphics, sound, or console-level noise just to prove a CPU
path.

The practical attraction here is not just style.
If reviewers can run the path on known SNES-family development or test hardware, the
project gains a second trust surface:

- the executor is historically constrained
- the toolchain expectations are narrow
- the hardware itself is legible enough to feel real rather than cloudlike

That does not replace the other substrates.
It complements them by giving the public story a very concrete physical validation
path.

It also helps with a narrower negative claim:

- if the same contract can run on a historically constrained legacy CPU path
- then "secret exploitation of some modern superscalar black box" becomes a weaker
  explanation of the result

That is not absolute proof against cheating.
It is a credibility and interpretability gain.
The point is to reduce the plausibility that the result depends on hidden modern CPU
specialness rather than on the declared execution contract.

There is also a practical trust reason for this posture.
Unusual low-level software can be misread as suspicious, evasive, or malware-like even
when it is behaving legitimately.
If the same declared path can be reproduced on historically constrained or otherwise
legible substrates, then claims that the result depends on hidden host behavior,
anti-analysis tricks, or undeclared modern-platform exploitation become weaker.

### 4. Three-State Circuit / Qutrit-Inspired Core

This should be treated as a classical three-state execution design unless and until a
real quantum path is both necessary and auditable.

Why it matters:

- conceptually matches the trinary logic very well
- gives a route for mapping the math to a minimal three-state circuit story
- preserves the elegance of the ternary state model

Public value:

- shows the trinary model is not merely cosmetic
- may eventually support more direct hardware explanations

Constraint:

- do not make the public audit story depend on genuine quantum behavior
- do not let the phrase `qutrit` replace a plain explanation of the execution rules

## Comparative Posture

These substrates do not need to produce identical performance characteristics.
They need to preserve the same declared contract:

- same input hash
- same derivation rule version
- same executable semantics
- same reconstruction target
- same validation outcome

Performance can differ.
Correctness and trace discipline should not.

## Audit Statement

The public claim should therefore be phrased as:

- this codec path is reproducible across multiple constrained execution substrates
- each substrate exposes one auditable execution lane
- each substrate preserves the same derivation and validation contract
- the result is therefore less likely to be overfit to one privileged implementation
- legacy-core execution further reduces the plausibility that the result depends on
  undeclared modern CPU behavior alone
- legacy-core and other legible substrates also reduce the plausibility of the result
  being an artifact of malware-like, evasive, or anti-analysis execution patterns

That is a much stronger and more honest statement than claiming we can always prove one
physical core under all hosting conditions.

## Scope Limit

This document defines the strategy, not a completed implementation status.

The project does not need every substrate implemented before the strategy is worth
stating.
It does need the public record to be honest about what is already real, what is a
target, and what remains a future executor path.
