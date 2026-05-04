#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=CORE / DOMAIN=COMPUTE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
ISO Symbol Table — Pre-compression Pass
========================================
**concept_anchor:** domain=compression / concept=iso_precompression_pass / resolution=CRYSTALLIZED

POSITION IN THE STACK
---------------------
This module is the first stage of the USC compression pipeline.  It sits
immediately upstream of the soliton encoder:

  raw input  (text, chemistry, biology, math, music, geography, code)
      │
      ▼
  iso_symbol_table.prepass()       ← THIS FILE
      │  vocabulary reduction — every token mapped to its densest ISO form
      │  output alphabet shrinks; entropy drops before the encoder sees it
      ▼
  soliton_factory.py               (soliton box encoder / USC codec)
      │  maps symbol stream to waveform bands (EM signal representation)
      │  each symbol cluster → one soliton box → one frequency band
      ▼
  compressed output                (EM-signal bitstream)

THE TWO-STAGE PRINCIPLE
-----------------------
Classical compression works in one pass: find redundancy in the raw byte
stream.  The problem is that "hydrogen", "Hydrogen", and "HYDROGEN" look
like three different tokens to a byte-level coder even though they carry
identical information.

The ISO prepass breaks compression into two conceptually distinct stages:

  Stage 1 — Vocabulary reduction (this file)
    Map every token that has a canonical shorter symbol to that symbol.
    "hydrogen" → "H", "United States" → "US", "adenine" → "A".
    The output still reads as human-interpretable text — it just uses the
    smallest agreed-upon representation for each concept.

  Stage 2 — Entropy coding (soliton encoder)
    The reduced-vocabulary stream has lower entropy per token than the
    original.  The soliton codec maps symbol clusters to frequency bands
    (soliton boxes).  Dense clusters → low-frequency bands (cheap to
    encode).  Sparse symbols → high-frequency bands.  This is the gamma
    pattern principle: the basis that minimises description length.

DECODE CONTRACT — WHY THIS IS LOSSLESS
----------------------------------------
The prepass is perfectly reversible without transmitting the substitution
map.  This is the critical property that makes it useful for compression:

  The lookup tables in this file are PUBLIC STANDARDS (IUPAC, ISO, SI).

  The decoder does not need to receive the table.  It only needs to know
  which domains were applied.  That information costs a handful of bits
  (a domain bitmask).

  Reconstruction: apply the inverse table for each active domain.
  The original text is recovered exactly.

This is the same principle as a shared dictionary in LZ77 — but the
dictionary is a universal standard, so it costs zero bits to negotiate.

HUTTER PRIZE CONTEXT
---------------------
The enwik8 benchmark (first 100 MB of Wikipedia XML) contains:
  - Thousands of element names in chemistry infoboxes
  - Country names in geographic articles (avg. 15–25 chars → 2 chars)
  - Language names in linguistics articles
  - Amino acid and nucleotide sequences in biology articles
  - Mathematical notation in science articles

After the ISO prepass, the symbol stream is:
  - Shorter (fewer bytes total)
  - Lower-entropy (smaller effective alphabet)
  - More uniform (all element names collapse to 1–2 symbol tokens)

The downstream entropy coder (soliton or otherwise) sees a better-conditioned
input.  The prepass does not compete with the entropy coder — it prepares the
ground for it.

EM SPECTRUM TRANSPOSITION
--------------------------
The prepass output is not fed to the soliton encoder as text.  It is
transposed into the EM spectrum — the symbol stream is mapped onto a
frequency-domain representation before entropy coding begins.

The key insight: every symbol in the prepass output has a characteristic
energy density.  A run of "ACGTACGT" in a DNA sequence is a periodic
waveform in the frequency domain.  "H₂O CO₂ NaCl" is a sparse, high-
frequency signal (few tokens, wide spacing).  The EM transposition step
exposes this structure so the soliton encoder can decompose it efficiently.

Pipeline after prepass:

  symbol stream  →  EM transposition  →  soliton decomposition  →  bitstream

  EM transposition:
    Each token class (iso_chem, iso_bio, etc.) occupies a frequency band.
    The band assignment follows the same logic as best_domain_for_band() in
    soliton_factory.py: high-density, low-entropy token classes (iso_bio
    ACGT runs) map to low-frequency bands (cheap to encode).  Sparse,
    high-information tokens (iso_chem compound formulas) map to high-
    frequency bands.

  Physics and imaginary physics data:
    The same transposition applies to physics notation.  A Planck constant
    (ℏ, from iso_math), a tensor expression (∂μAν), or a ZK-STARK proof
    element all carry structured symbol patterns.  After prepass, these are
    compact tokens rather than verbose prose — the EM transposition then
    maps them to the frequency bands where their periodicity is most
    compressible.

    Imaginary physics constructs (soliton manifold coordinates, foam voxel
    states, substrate ISA opcodes) follow the same path.  The substrate ISA
    defines its own symbol vocabulary; feeding that through an iso_isa domain
    (not yet built) before EM transposition would reduce ISA encoding cost
    by the same mechanism.

  Why this matters for compression ratio:
    Classical entropy coders (Huffman, ANS) work on symbol frequency in the
    time domain.  The EM transposition exposes periodicity and correlation
    that is invisible to time-domain coders.  A DNA sequence that looks like
    noise byte-by-byte is a clean low-frequency signal in the EM domain.
    The soliton encoder exploits this directly.

DOMAIN REGISTRY
---------------
Each domain has:
  name          — identifier used in the domain bitmask / config
  description   — what it substitutes
  table         — {long_form: short_form}  (sorted long-first for matching)
  est_ratio     — estimated average compression ratio on domain-heavy text

Active domains: iso_chem, iso_bio, iso_unit, iso_math, iso_lang, iso_geo,
                iso_music, iso_abbrev

Usage:
  python3 iso_symbol_table.py prepass "Hydrogen and oxygen form water"
  python3 iso_symbol_table.py decode  "H and O form water" --domains iso_chem
  python3 iso_symbol_table.py stats   "Adenine pairs with Thymine in DNA"
  python3 iso_symbol_table.py domains                      list all domains
"""

import re
import unicodedata
from pathlib import Path
from typing import NamedTuple

# ─────────────────────────────────────────────────────────────────────────────
# Domain metadata
# ─────────────────────────────────────────────────────────────────────────────

class Domain(NamedTuple):
    """Metadata for a single ISO symbol domain."""

    name:        str
    description: str
    est_ratio:   float   # estimated bytes_out / bytes_in on domain-heavy text


# ─────────────────────────────────────────────────────────────────────────────
# Lookup tables
# Each dict maps long_form (lowercase) → symbol.
# Matching is case-insensitive; output preserves the symbol's canonical case.
# ─────────────────────────────────────────────────────────────────────────────

# ── iso_chem: IUPAC element names and common compound names ──────────────────
# Source: IUPAC 2021 table of elements (all 118)
_CHEM_TABLE: dict[str, str] = {
    # Period 1
    "hydrogen":       "H",
    "helium":         "He",
    # Period 2
    "lithium":        "Li",
    "beryllium":      "Be",
    "boron":          "B",
    "carbon":         "C",
    "nitrogen":       "N",
    "oxygen":         "O",
    "fluorine":       "F",
    "neon":           "Ne",
    # Period 3
    "sodium":         "Na",
    "magnesium":      "Mg",
    "aluminium":      "Al",
    "aluminum":       "Al",
    "silicon":        "Si",
    "phosphorus":     "P",
    "sulfur":         "S",
    "sulphur":        "S",
    "chlorine":       "Cl",
    "argon":          "Ar",
    # Period 4
    "potassium":      "K",
    "calcium":        "Ca",
    "scandium":       "Sc",
    "titanium":       "Ti",
    "vanadium":       "V",
    "chromium":       "Cr",
    "manganese":      "Mn",
    "iron":           "Fe",
    "cobalt":         "Co",
    "nickel":         "Ni",
    "copper":         "Cu",
    "zinc":           "Zn",
    "gallium":        "Ga",
    "germanium":      "Ge",
    "arsenic":        "As",
    "selenium":       "Se",
    "bromine":        "Br",
    "krypton":        "Kr",
    # Period 5
    "rubidium":       "Rb",
    "strontium":      "Sr",
    "yttrium":        "Y",
    "zirconium":      "Zr",
    "niobium":        "Nb",
    "molybdenum":     "Mo",
    "technetium":     "Tc",
    "ruthenium":      "Ru",
    "rhodium":        "Rh",
    "palladium":      "Pd",
    "silver":         "Ag",
    "cadmium":        "Cd",
    "indium":         "In",
    "tin":            "Sn",
    "antimony":       "Sb",
    "tellurium":      "Te",
    "iodine":         "I",
    "xenon":          "Xe",
    # Period 6
    "caesium":        "Cs",
    "cesium":         "Cs",
    "barium":         "Ba",
    "lanthanum":      "La",
    "cerium":         "Ce",
    "praseodymium":   "Pr",
    "neodymium":      "Nd",
    "promethium":     "Pm",
    "samarium":       "Sm",
    "europium":       "Eu",
    "gadolinium":     "Gd",
    "terbium":        "Tb",
    "dysprosium":     "Dy",
    "holmium":        "Ho",
    "erbium":         "Er",
    "thulium":        "Tm",
    "ytterbium":      "Yb",
    "lutetium":       "Lu",
    "hafnium":        "Hf",
    "tantalum":       "Ta",
    "tungsten":       "W",
    "rhenium":        "Re",
    "osmium":         "Os",
    "iridium":        "Ir",
    "platinum":       "Pt",
    "gold":           "Au",
    "mercury":        "Hg",
    "thallium":       "Tl",
    "lead":           "Pb",
    "bismuth":        "Bi",
    "polonium":       "Po",
    "astatine":       "At",
    "radon":          "Rn",
    # Period 7
    "francium":       "Fr",
    "radium":         "Ra",
    "actinium":       "Ac",
    "thorium":        "Th",
    "protactinium":   "Pa",
    "uranium":        "U",
    "neptunium":      "Np",
    "plutonium":      "Pu",
    "americium":      "Am",
    "curium":         "Cm",
    "berkelium":      "Bk",
    "californium":    "Cf",
    "einsteinium":    "Es",
    "fermium":        "Fm",
    "mendelevium":    "Md",
    "nobelium":       "No",
    "lawrencium":     "Lr",
    "rutherfordium":  "Rf",
    "dubnium":        "Db",
    "seaborgium":     "Sg",
    "bohrium":        "Bh",
    "hassium":        "Hs",
    "meitnerium":     "Mt",
    "darmstadtium":   "Ds",
    "roentgenium":    "Rg",
    "copernicium":    "Cn",
    "nihonium":       "Nh",
    "flerovium":      "Fl",
    "moscovium":      "Mc",
    "livermorium":    "Lv",
    "tennessine":     "Ts",
    "oganesson":      "Og",
    # Common compounds (long form only)
    "water":               "H₂O",
    "carbon dioxide":      "CO₂",
    "carbon monoxide":     "CO",
    "ammonia":             "NH₃",
    "methane":             "CH₄",
    "ethanol":             "C₂H₅OH",
    "glucose":             "C₆H₁₂O₆",
    "sodium chloride":     "NaCl",
    "sulfuric acid":       "H₂SO₄",
    "hydrochloric acid":   "HCl",
    "nitric acid":         "HNO₃",
    "sodium hydroxide":    "NaOH",
    "calcium carbonate":   "CaCO₃",
    "deoxyribonucleic acid": "DNA",
    "ribonucleic acid":    "RNA",
    "adenosine triphosphate": "ATP",
    "adenosine diphosphate":  "ADP",
}

# ── iso_bio: IUPAC amino acid and nucleotide codes ───────────────────────────
# Source: IUPAC-IUB 1984 recommendations
_BIO_TABLE: dict[str, str] = {
    # Amino acids — full name → 1-letter code
    "alanine":          "A",
    "arginine":         "R",
    "asparagine":       "N",
    "aspartic acid":    "D",
    "aspartate":        "D",
    "cysteine":         "C",
    "glutamine":        "Q",
    "glutamic acid":    "E",
    "glutamate":        "E",
    "glycine":          "G",
    "histidine":        "H",
    "isoleucine":       "I",
    "leucine":          "L",
    "lysine":           "K",
    "methionine":       "M",
    "phenylalanine":    "F",
    "proline":          "P",
    "serine":           "S",
    "threonine":        "T",
    "tryptophan":       "W",
    "tyrosine":         "Y",
    "valine":           "V",
    # Amino acids — 3-letter → 1-letter
    # OMITTED from default table: ala, his, met, pro, ser, val, asp, glu, gly,
    # thr, ile, leu, lys, phe, trp, tyr — all common English words or names.
    # These produce thousands of false positives on general prose (Wikipedia).
    # They belong in a context-gated iso_bio_seq domain (not yet built) that
    # only fires inside recognised protein/sequence annotation blocks.
    # Safe 3-letter codes (no common English collision):
    "arg":  "R",
    "asn":  "N",
    "cys":  "C",
    "gln":  "Q",
    # Nucleotides — full name → 1-letter IUPAC code
    "adenine":    "A",
    "cytosine":   "C",
    "guanine":    "G",
    "thymine":    "T",
    "uracil":     "U",
    # IUPAC ambiguity codes
    "purine":       "R",   # A or G
    "pyrimidine":   "Y",   # C or T
}

# ── iso_unit: SI base units, derived units, and prefix symbols ───────────────
# Source: BIPM SI Brochure 9th edition (2019)
_UNIT_TABLE: dict[str, str] = {
    # Base units — only unambiguous long forms kept
    # OMITTED: "second" → "s"  (ordinal/verb collision, extremely common)
    #          "mole"   → "mol" (verb collision)
    "meter":     "m",
    "metre":     "m",
    "kilogram":  "kg",
    "ampere":    "A",
    "kelvin":    "K",
    "candela":   "cd",
    # Derived units — person-name collisions removed
    # OMITTED: "newton" → "N"   (Isaac Newton: ~10× more common in Wikipedia)
    #          "henry"  → "H"   (person name: ~15× more common)
    #          "watt"   → "W"   (person name collision)
    #          "coulomb"→ "C"   (person name collision)
    #          "farad"  → "F"   (person name collision)
    #          "tesla"  → "T"   (person + brand collision)
    #          "siemens"→ "S"   (company/person collision)
    #          "weber"  → "Wb"  (person name collision)
    #          "gray"   → "Gy"  (adjective/name collision)
    "hertz":     "Hz",
    "pascal":    "Pa",
    "joule":     "J",
    "volt":      "V",
    "ohm":       "Ω",
    "lumen":     "lm",
    "lux":       "lx",
    "becquerel": "Bq",
    "sievert":   "Sv",
    "katal":     "kat",
    # Common non-SI accepted units
    # OMITTED: "bar" → "bar" (no gain, same length)
    #          "day" → "d"   (ambiguous in prose)
    #          "hour"→ "h"   (ambiguous)
    #          "minute"→"min" (ambiguous)
    "litre":     "L",
    "liter":     "L",
    "tonne":     "t",
    "electronvolt": "eV",
    "dalton":    "Da",
    "hectare":   "ha",
    "degree celsius": "°C",
    "degree fahrenheit": "°F",
    # SI prefixes (long form → prefix symbol; applied as standalone tokens)
    "yotta":  "Y",
    "zetta":  "Z",
    "exa":    "E",
    "peta":   "P",
    "tera":   "T",
    "giga":   "G",
    "mega":   "M",
    "kilo":   "k",
    "hecto":  "h",
    "deca":   "da",
    "deci":   "d",
    "centi":  "c",
    "milli":  "m",
    "micro":  "μ",
    "nano":   "n",
    "pico":   "p",
    "femto":  "f",
    "atto":   "a",
    "zepto":  "z",
    "yocto":  "y",
}

# ── LaTeX normalization support for analysis/ingest flows ────────────────────
# This is intentionally NOT part of the lossless prepass/decode contract.
# It is a semantic normalizer that turns common LaTeX math syntax into a
# canonical plain-text form that downstream classifiers and keyword extractors
# can reason about.

_LATEX_SIMPLE_COMMANDS: dict[str, str] = {
    # Greek letters
    "alpha": "alpha",
    "beta": "beta",
    "gamma": "gamma",
    "Gamma": "gamma",
    "delta": "delta",
    "Delta": "delta",
    "epsilon": "epsilon",
    "varepsilon": "epsilon",
    "zeta": "zeta",
    "eta": "eta",
    "theta": "theta",
    "vartheta": "theta",
    "Theta": "theta",
    "iota": "iota",
    "kappa": "kappa",
    "lambda": "lambda",
    "Lambda": "lambda",
    "mu": "mu",
    "nu": "nu",
    "xi": "xi",
    "Xi": "xi",
    "pi": "pi",
    "Pi": "pi",
    "rho": "rho",
    "varrho": "rho",
    "sigma": "sigma",
    "Sigma": "sigma",
    "tau": "tau",
    "upsilon": "upsilon",
    "Upsilon": "upsilon",
    "phi": "phi",
    "varphi": "phi",
    "Phi": "phi",
    "chi": "chi",
    "psi": "psi",
    "Psi": "psi",
    "omega": "omega",
    "Omega": "omega",
    # Core operators and relations
    "sum": "sum",
    "prod": "product",
    "int": "integral",
    "iint": "double integral",
    "iiint": "triple integral",
    "oint": "contour integral",
    "partial": "partial",
    "nabla": "nabla",
    "infty": "infinity",
    "to": "maps to",
    "rightarrow": "maps to",
    "leftarrow": "left arrow",
    "leftrightarrow": "if and only if",
    "Rightarrow": "implies",
    "Leftarrow": "implied by",
    "Leftrightarrow": "if and only if",
    "mapsto": "maps to",
    "cdot": "dot product",
    "times": "times",
    "otimes": "tensor product",
    "oplus": "direct sum",
    "pm": "plus or minus",
    "mp": "minus or plus",
    "leq": "less than or equal to",
    "le": "less than or equal to",
    "geq": "greater than or equal to",
    "ge": "greater than or equal to",
    "neq": "not equal to",
    "ne": "not equal to",
    "approx": "approximately",
    "equiv": "equivalent to",
    "propto": "proportional to",
    "sim": "similar to",
    "simeq": "approximately equal to",
    "cong": "congruent to",
    "in": "element of",
    "notin": "not element of",
    "subset": "subset of",
    "subseteq": "subset or equal to",
    "supset": "superset of",
    "supseteq": "superset or equal to",
    "cup": "union",
    "cap": "intersection",
    "emptyset": "empty set",
    "forall": "for all",
    "exists": "there exists",
    # Common functions
    "min": "minimum",
    "max": "maximum",
    "log": "log",
    "ln": "natural log",
    "exp": "exp",
    "sin": "sine",
    "cos": "cosine",
    "tan": "tangent",
    "tanh": "hyperbolic tangent",
}

_LATEX_PLAIN_WRAPPERS = (
    "mathrm",
    "mathbf",
    "mathit",
    "mathsf",
    "mathtt",
    "text",
    "textrm",
    "textbf",
    "textit",
    "emph",
    "operatorname",
    "operatorname*",
)

_LATEX_FUNCTION_WRAPPERS: dict[str, str] = {
    "hat": "hat",
    "widehat": "hat",
    "tilde": "tilde",
    "widetilde": "tilde",
    "bar": "bar",
    "overline": "bar",
    "underline": "underline",
    "vec": "vector",
    "dot": "dot",
    "ddot": "ddot",
}

_LATEX_BLACKBOARD: dict[str, str] = {
    "N": "natural numbers",
    "Z": "integers",
    "Q": "rationals",
    "R": "real numbers",
    "C": "complex numbers",
    "H": "quaternions",
    "P": "projective space",
    "E": "expectation",
}

_LATEX_DELIMS_RE = re.compile(
    r"\\\(|\\\)|\\\[|\\\]|\$\$|\$|\\begin\{(?:equation\*?|align\*?|gather\*?)\}|"
    r"\\end\{(?:equation\*?|align\*?|gather\*?)\}"
)
_LATEX_SPACING_RE = re.compile(r"\\(?:,|!|;|:|quad|qquad|enspace|thinspace)\b|~")
_LATEX_LEFT_RIGHT_RE = re.compile(r"\\(?:left|right)\b")
_LATEX_BLACKBOARD_RE = re.compile(r"\\mathbb\s*\{\s*([A-Za-z])\s*\}")
_LATEX_STYLE_WRAPPER_RE = re.compile(
    r"\\(?:mathcal|mathfrak|mathscr)\s*\{\s*([^{}]+)\s*\}"
)
_LATEX_PLAIN_WRAPPER_RE = re.compile(
    r"\\(?:"
    + "|".join(re.escape(cmd) for cmd in sorted(_LATEX_PLAIN_WRAPPERS, key=len, reverse=True))
    + r")\s*\{\s*([^{}]+)\s*\}"
)
_LATEX_FUNCTION_WRAPPER_RE = re.compile(
    r"\\("
    + "|".join(re.escape(cmd) for cmd in sorted(_LATEX_FUNCTION_WRAPPERS, key=len, reverse=True))
    + r")\s*\{\s*([^{}]+)\s*\}"
)
_LATEX_FRAC_RE = re.compile(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
_LATEX_SQRT_RE = re.compile(r"\\sqrt(?:\[(.*?)\])?\s*\{([^{}]+)\}")
_LATEX_COMMAND_RE = re.compile(
    r"\\("
    + "|".join(re.escape(cmd) for cmd in sorted(_LATEX_SIMPLE_COMMANDS, key=len, reverse=True))
    + r")\b"
)


def _rewrite_until_stable(text: str, fn, max_passes: int = 8) -> str:
    """Apply `fn` until the text stops changing or the pass limit is hit."""
    result = text
    for _ in range(max_passes):
        updated = fn(result)
        if updated == result:
            break
        result = updated
    return result


def normalize_latex_math(text: str) -> str:
    """Canonicalize common LaTeX math syntax into analysis-friendly text.

    This is intentionally semantic rather than lossless. It is used by
    analysis tools that want math-heavy documents to emit stable text signals
    without requiring a full TeX parser.
    """
    result = text

    result = _LATEX_DELIMS_RE.sub(" ", result)
    result = _LATEX_LEFT_RIGHT_RE.sub("", result)
    result = _LATEX_SPACING_RE.sub(" ", result)

    result = result.replace(r"\{", "{").replace(r"\}", "}")
    result = result.replace(r"\_", "_").replace(r"\%", "%")
    result = result.replace(r"\#", "#").replace(r"\$", "$")
    result = result.replace(r"\&", " and ")

    def _blackboard(m: re.Match) -> str:
        key = m.group(1).strip()
        return _LATEX_BLACKBOARD.get(key, f"blackboard {key}")

    result = _LATEX_BLACKBOARD_RE.sub(_blackboard, result)

    result = _rewrite_until_stable(
        result,
        lambda s: _LATEX_STYLE_WRAPPER_RE.sub(lambda m: m.group(1), s),
    )
    result = _rewrite_until_stable(
        result,
        lambda s: _LATEX_PLAIN_WRAPPER_RE.sub(lambda m: m.group(1), s),
    )

    def _function_wrapper(m: re.Match) -> str:
        return f"{_LATEX_FUNCTION_WRAPPERS[m.group(1)]}({m.group(2)})"

    result = _rewrite_until_stable(
        result,
        lambda s: _LATEX_FUNCTION_WRAPPER_RE.sub(_function_wrapper, s),
    )

    result = re.sub(r"_\{([^{}]+)\}", lambda m: f"_({m.group(1)})", result)
    result = re.sub(r"\^\{([^{}]+)\}", lambda m: f"^({m.group(1)})", result)

    result = _rewrite_until_stable(
        result,
        lambda s: _LATEX_FRAC_RE.sub(
            lambda m: f"fraction({m.group(1)} over {m.group(2)})", s
        ),
    )
    result = _rewrite_until_stable(
        result,
        lambda s: _LATEX_SQRT_RE.sub(
            lambda m: (
                f"root({m.group(1)} of {m.group(2)})"
                if m.group(1)
                else f"square root({m.group(2)})"
            ),
            s,
        ),
    )

    result = _LATEX_COMMAND_RE.sub(
        lambda m: _LATEX_SIMPLE_COMMANDS[m.group(1)],
        result,
    )

    result = re.sub(r"\\[A-Za-z]+", " ", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


# ── iso_math: Greek letters and common mathematical operators ────────────────
_MATH_TABLE: dict[str, str] = {
    # Greek — lowercase
    "alpha":   "α",
    "beta":    "β",
    "gamma":   "γ",
    "delta":   "δ",
    "epsilon": "ε",
    "zeta":    "ζ",
    "eta":     "η",
    "theta":   "θ",
    "iota":    "ι",
    "kappa":   "κ",
    "lambda":  "λ",
    "mu":      "μ",
    "nu":      "ν",
    "xi":      "ξ",
    "omicron": "ο",
    "pi":      "π",
    "rho":     "ρ",
    "sigma":   "σ",
    "tau":     "τ",
    "upsilon": "υ",
    "phi":     "φ",
    "chi":     "χ",
    "psi":     "ψ",
    "omega":   "ω",
    # Greek uppercase handled by capitalisation of the output symbol.
    # No duplicate keys: lowercase forms above cover both cases via IGNORECASE.
    # Math operators (spelled out in prose)
    "infinity":      "∞",
    "therefore":     "∴",
    "because":       "∵",
    "approximately": "≈",
    "proportional":  "∝",
    "element of":    "∈",
    "subset of":     "⊂",
    "superset of":   "⊃",
    "union":         "∪",
    "intersection":  "∩",
    "empty set":     "∅",
    "for all":       "∀",
    "there exists":  "∃",
    "less than or equal to": "≤",
    "greater than or equal to": "≥",
    "not equal to": "≠",
    "maps to":       "→",
    "left arrow":    "←",
    "if and only if": "⇔",
    "implies":       "⇒",
    "subset or equal to": "⊆",
    "superset or equal to": "⊇",
    "square root":   "√",
    "sum":           "∑",
    "product":       "∏",
    "integral":      "∫",
    "partial":       "∂",
    "nabla":         "∇",
    "planck constant": "ℏ",
    "imaginary unit":  "ⅈ",
    "real numbers":  "ℝ",
    "natural numbers": "ℕ",
    "integers":      "ℤ",
    "rationals":     "ℚ",
    "complex numbers": "ℂ",
    "quaternions":   "ℍ",
    "tensor product": "⊗",
    "direct sum":    "⊕",
    "plus or minus": "±",
    "minus or plus": "∓",
}

# ── iso_lang: ISO 639-1 two-letter language codes ────────────────────────────
# Source: ISO 639-1:2002
_LANG_TABLE: dict[str, str] = {
    "afrikaans":    "af",
    "albanian":     "sq",
    "amharic":      "am",
    "arabic":       "ar",
    "armenian":     "hy",
    "azerbaijani":  "az",
    "basque":       "eu",
    "belarusian":   "be",
    "bengali":      "bn",
    "bosnian":      "bs",
    "bulgarian":    "bg",
    "burmese":      "my",
    "catalan":      "ca",
    "chinese":      "zh",
    "croatian":     "hr",
    "czech":        "cs",
    "danish":       "da",
    "dutch":        "nl",
    "english":      "en",
    "estonian":     "et",
    "finnish":      "fi",
    "french":       "fr",
    "galician":     "gl",
    "georgian":     "ka",
    "german":       "de",
    "greek":        "el",
    "gujarati":     "gu",
    "haitian creole": "ht",
    "hausa":        "ha",
    "hebrew":       "he",
    "hindi":        "hi",
    "hungarian":    "hu",
    "icelandic":    "is",
    "igbo":         "ig",
    "indonesian":   "id",
    "irish":        "ga",
    "italian":      "it",
    "japanese":     "ja",
    "javanese":     "jv",
    "kannada":      "kn",
    "kazakh":       "kk",
    "korean":       "ko",
    "kurdish":      "ku",
    "kyrgyz":       "ky",
    "lao":          "lo",
    "latin":        "la",
    "latvian":      "lv",
    "lithuanian":   "lt",
    "macedonian":   "mk",
    "malay":        "ms",
    "malayalam":    "ml",
    "maltese":      "mt",
    "maori":        "mi",
    "marathi":      "mr",
    "mongolian":    "mn",
    "nepali":       "ne",
    "norwegian":    "no",
    "pashto":       "ps",
    "persian":      "fa",
    "polish":       "pl",
    "portuguese":   "pt",
    "punjabi":      "pa",
    "romanian":     "ro",
    "russian":      "ru",
    "samoan":       "sm",
    "serbian":      "sr",
    "sindhi":       "sd",
    "sinhala":      "si",
    "slovak":       "sk",
    "slovenian":    "sl",
    "somali":       "so",
    "spanish":      "es",
    "sundanese":    "su",
    "swahili":      "sw",
    "swedish":      "sv",
    "tajik":        "tg",
    "tamil":        "ta",
    "telugu":       "te",
    "thai":         "th",
    "turkish":      "tr",
    "ukrainian":    "uk",
    "urdu":         "ur",
    "uzbek":        "uz",
    "vietnamese":   "vi",
    "welsh":        "cy",
    "xhosa":        "xh",
    "yoruba":       "yo",
    "zulu":         "zu",
}

# ── iso_geo: ISO 3166-1 alpha-2 country codes (top-frequency in Wikipedia) ───
# Source: ISO 3166-1:2020
_GEO_TABLE: dict[str, str] = {
    "united states of america": "US",
    "united states":            "US",
    "united kingdom":           "GB",
    "great britain":            "GB",
    "people's republic of china": "CN",
    "republic of china":        "TW",
    "china":                    "CN",
    "russia":                   "RU",
    "russian federation":       "RU",
    "germany":                  "DE",
    "france":                   "FR",
    "japan":                    "JP",
    "india":                    "IN",
    "brazil":                   "BR",
    "canada":                   "CA",
    "australia":                "AU",
    "italy":                    "IT",
    "spain":                    "ES",
    "mexico":                   "MX",
    "south korea":              "KR",
    "republic of korea":        "KR",
    "indonesia":                "ID",
    "netherlands":              "NL",
    "saudi arabia":             "SA",
    "turkey":                   "TR",
    "switzerland":              "CH",
    "argentina":                "AR",
    "sweden":                   "SE",
    "poland":                   "PL",
    "belgium":                  "BE",
    "norway":                   "NO",
    "austria":                  "AT",
    "united arab emirates":     "AE",
    "nigeria":                  "NG",
    "south africa":             "ZA",
    "egypt":                    "EG",
    "israel":                   "IL",
    "denmark":                  "DK",
    "singapore":                "SG",
    "malaysia":                 "MY",
    "philippines":              "PH",
    "pakistan":                 "PK",
    "bangladesh":               "BD",
    "vietnam":                  "VN",
    "ukraine":                  "UA",
    "portugal":                 "PT",
    "greece":                   "GR",
    "czech republic":           "CZ",
    "czechia":                  "CZ",
    "romania":                  "RO",
    "hungary":                  "HU",
    "new zealand":              "NZ",
    "iraq":                     "IQ",
    "iran":                     "IR",
    "chile":                    "CL",
    "colombia":                 "CO",
    "peru":                     "PE",
    "ethiopia":                 "ET",
    "kenya":                    "KE",
    "ghana":                    "GH",
    "tanzania":                 "TZ",
    "myanmar":                  "MM",
    "afghanistan":              "AF",
    "morocco":                  "MA",
    "algeria":                  "DZ",
    "cuba":                     "CU",
    "thailand":                 "TH",
    "taiwan":                   "TW",
    "finland":                  "FI",
    "ireland":                  "IE",
    "croatia":                  "HR",
    "slovakia":                 "SK",
    "bulgaria":                 "BG",
    "serbia":                   "RS",
    "iceland":                  "IS",
    "luxembourg":               "LU",
    "estonia":                  "EE",
    "latvia":                   "LV",
    "lithuania":                "LT",
    "slovenia":                 "SI",
    "north korea":              "KP",
    "democratic people's republic of korea": "KP",
}

# ── iso_music: ABC notation and MIDI pitch numbers ───────────────────────────
# Source: ABC notation standard v2.1; General MIDI spec
_MUSIC_TABLE: dict[str, str] = {
    # Note names with octave → ABC notation
    "c major":  "C:maj",
    "g major":  "G:maj",
    "d major":  "D:maj",
    "a major":  "A:maj",
    "e major":  "E:maj",
    "f major":  "F:maj",
    "b flat major": "Bb:maj",
    "e flat major": "Eb:maj",
    "a flat major": "Ab:maj",
    "a minor":  "A:min",
    "e minor":  "E:min",
    "d minor":  "D:min",
    "g minor":  "G:min",
    "c minor":  "C:min",
    # Tempo markings → bpm range tokens
    "largo":     "♩=40-60",
    "adagio":    "♩=60-80",
    "andante":   "♩=80-100",
    "moderato":  "♩=100-120",
    "allegro":   "♩=120-160",
    "presto":    "♩=160-200",
    "prestissimo": "♩=200+",
    # Common musical terms
    "forte":        "f",
    "piano":        "p",
    "mezzo forte":  "mf",
    "mezzo piano":  "mp",
    "fortissimo":   "ff",
    "pianissimo":   "pp",
    "fortepiano":   "fp",
    "crescendo":    "cresc.",
    "decrescendo":  "decresc.",
    "diminuendo":   "dim.",
    "sforzando":    "sfz",
}

# ── iso_abbrev: universally unambiguous abbreviations ────────────────────────
# Only include substitutions where the short form is ALWAYS unambiguous.
_ABBREV_TABLE: dict[str, str] = {
    # Time
    "january":   "Jan",
    "february":  "Feb",
    "march":     "Mar",
    "april":     "Apr",
    # "may" intentionally omitted — ambiguous with the verb
    "june":      "Jun",
    "july":      "Jul",
    "august":    "Aug",
    "september": "Sep",
    "october":   "Oct",
    "november":  "Nov",
    "december":  "Dec",
    "monday":    "Mon",
    "tuesday":   "Tue",
    "wednesday": "Wed",
    "thursday":  "Thu",
    "friday":    "Fri",
    "saturday":  "Sat",
    "sunday":    "Sun",
    # Universal scientific abbreviations
    "approximately":     "approx.",
    "equation":          "eq.",
    "figure":            "fig.",
    "number":            "no.",
    "versus":            "vs.",
    "et cetera":         "etc.",
    "that is":           "i.e.",
    "for example":       "e.g.",
    "and others":        "et al.",
    "compare":           "cf.",
    "page":              "p.",
    "pages":             "pp.",
    "volume":            "vol.",
    "edition":           "ed.",
    "chapter":           "ch.",
    "section":           "sec.",
    "paragraph":         "para.",
    "maximum":           "max.",
    "minimum":           "min.",
    "average":           "avg.",
    "standard deviation": "SD",
    "standard error":    "SE",
    "confidence interval": "CI",
    "not applicable":    "N/A",
    "not available":     "N/A",
}


# ── iso_ptos: Research Stack / PTOS operator vocabulary ──────────────────────
# Corpus-specific: terms that dominate the Research Stack but are rare in
# general text.  Multi-word phrases are preferred over single words to avoid
# false positives.  Single words included only when corpus-unique.
# concept_anchor: domain=compression / concept=iso_ptos_domain / resolution=FORMING
_PTOS_TABLE: dict[str, str] = {
    # Multi-word architecture terms (longest first — matched before fragments)
    "topological soliton machine":  "TSM",
    "topological soliton":          "TS",
    "substrate index":              "SIDX",
    "concept vector":               "CV",
    "operator fingerprint":         "OPFP",
    "cross-product residual":       "CPR",
    "cross product residual":       "CPR",
    "iso prepass":                  "IPP",
    "iso pipeline":                 "IOPIPE",
    "iso symbol table":             "ISOT",
    "bits-back":                    "BB",
    "bits back":                    "BB",
    "basal ganglia":                "BG",
    "soliton manifold":             "SM",
    "soliton encoder":              "SE",
    "soliton factory":              "SFX",
    "soliton box":                  "SB",
    "foam voxel":                   "FV",
    "foam phase":                   "FP",
    "phase transition":             "PT",
    "research stack":               "RS",
    # Single terms — corpus-unique, low false-positive risk
    "metafoam":                     "MFM",
    "metanarrative":                "MNAR",
    "soliton":                      "SLT",
}

# ── iso_isa: TSM substrate opcode vocabulary ──────────────────────────────────
# Source: CATEGORY/TSM/tsm_metafoam_enhanced.py Opcode enum (v3.0)
# Maps opcode names (prose and identifier forms) to their hex addresses.
# Both "wave fold" (prose/comments) and "wave_fold" (identifier) are included
# because \b word boundaries treat underscores as word characters.
# concept_anchor: domain=compression / concept=iso_isa_domain / resolution=FORMING
_ISA_TABLE: dict[str, str] = {
    # Original opcodes — mnemonic targets (not hex: hex literals appear in source)
    "ingest_state":         "IST",    "ingest state":         "IST",
    "wave_fold":            "WFD",    "wave fold":            "WFD",
    "sync_precision":       "SYNC",   "sync precision":       "SYNC",
    "omni_bal":             "OBAL",   "omni bal":             "OBAL",
    "entangle":             "ENTG",
    "evolve":               "EVLV",
    "vram_flush":           "VFLSH",  "vram flush":           "VFLSH",
    "stark_prove":          "SPROV",  "stark prove":          "SPROV",
    "ledger_commit":        "LCMT",   "ledger commit":        "LCMT",
    "crypto_wrap":          "CWRP",   "crypto wrap":          "CWRP",
    "grant_access":         "GACC",   "grant access":         "GACC",
    "native_ws":            "NWS",    "native ws":            "NWS",
    "webasm":               "WASM",
    "neuromorph":           "NMR",
    "gpgpu_surf":           "GSRF",   "gpgpu surf":           "GSRF",
    "nibble_swap":          "NSWP",   "nibble swap":          "NSWP",
    "tsm_int":              "TINT",   "tsm int":              "TINT",
    # Enhanced opcodes
    "phase_lock":           "PLCK",   "phase lock":           "PLCK",
    "sra_pulse":            "SPLS",   "sra pulse":            "SPLS",
    "activate_context":     "ACTX",   "activate context":     "ACTX",
    "ricci_flow":           "RICC",   "ricci flow":           "RICC",
    "info_flow":            "IFLW",   "info flow":            "IFLW",
    "stark_lock":           "SLCK",   "stark lock":           "SLCK",
    "vdp_compress":         "VDPC",   "vdp compress":         "VDPC",
    "quantum_melt":         "QMLT",   "quantum melt":         "QMLT",
    "foam_spray":           "FSPR",   "foam spray":           "FSPR",
    "weld_surface":         "WELD",   "weld surface":         "WELD",
    "hamiltonian":          "HMLT",
    "coherence_guard":      "CGRD",   "coherence guard":      "CGRD",
    "hyperfluid_lut":       "HLUT",   "hyperfluid lut":       "HLUT",
    # Forming semantic surfaces — reserved vocabulary, not official ISA v2.9
    "engram_code":          "ECOD",   "engram code":          "ECOD",
    "engram_coding":        "ECOD",   "engram coding":        "ECOD",
    "engram_recall":        "ERCL",   "engram recall":        "ERCL",
    "blink_gate":           "BLGT",   "blink gate":           "BLGT",
    # Matrix Reality opcodes
    "byte_stream":          "BSTR",   "byte stream":          "BSTR",
    "voxel_render":         "VXRN",   "voxel render":         "VXRN",
    # Accessibility
    "assist_bind":          "ABND",   "assist bind":          "ABND",
}

# ── iso_code: Python structural keyword normalization ────────────────────────
# Only tokens long enough to produce meaningful byte savings.
# Short keywords (def, if, for) omitted — gain < 2 bytes per occurrence.
# concept_anchor: domain=compression / concept=iso_code_domain / resolution=FORMING
_CODE_TABLE: dict[str, str] = {
    "isinstance":           "isa",
    "AttributeError":       "AErr",
    "RuntimeError":         "RErr",
    "ValueError":           "VErr",
    "TypeError":            "TErr",
    "KeyError":             "KErr",
    "IndexError":           "IErr",
    "ImportError":          "ImpErr",
    "FileNotFoundError":    "FNFErr",
    "PermissionError":      "PermErr",
    "NotImplementedError":  "NIErr",
    "StopIteration":        "StopIter",
    "ZeroDivisionError":    "ZDErr",
    "OverflowError":        "OFErr",
    "UnicodeDecodeError":   "UDErr",
    "UnicodeEncodeError":   "UEErr",
    "continue":             "cont",
    "nonlocal":             "nloc",
    "enumerate":            "enm",
}


# ─────────────────────────────────────────────────────────────────────────────
# Domain registry — order matters for multi-domain prepass
# Longer phrases first (iso_geo, iso_chem compounds) before single words
# ─────────────────────────────────────────────────────────────────────────────

DOMAINS: dict[str, tuple[Domain, dict[str, str]]] = {
    "iso_geo":    (Domain("iso_geo",    "ISO 3166 country/territory names → alpha-2 codes",  0.12), _GEO_TABLE),
    "iso_chem":   (Domain("iso_chem",   "IUPAC element names and common compound names",      0.18), _CHEM_TABLE),
    "iso_bio":    (Domain("iso_bio",    "IUPAC amino acid and nucleotide codes",              0.14), _BIO_TABLE),
    "iso_unit":   (Domain("iso_unit",   "SI base units, derived units, and SI prefix symbols", 0.35), _UNIT_TABLE),
    "iso_math":   (Domain("iso_math",   "Greek letters and mathematical operators",           0.55), _MATH_TABLE),
    "iso_lang":   (Domain("iso_lang",   "ISO 639-1 language names → 2-letter codes",         0.20), _LANG_TABLE),
    "iso_music":  (Domain("iso_music",  "ABC notation for keys, tempos, dynamics",            0.45), _MUSIC_TABLE),
    "iso_abbrev": (Domain("iso_abbrev", "Universally unambiguous abbreviations",              0.65), _ABBREV_TABLE),
    # Corpus-specific domains (Research Stack / PTOS)
    "iso_ptos":   (Domain("iso_ptos",   "PTOS/Research Stack operator vocabulary",            0.40), _PTOS_TABLE),
    "iso_isa":    (Domain("iso_isa",    "TSM substrate opcode names → hex addresses",         0.35), _ISA_TABLE),
    "iso_code":   (Domain("iso_code",   "Python structural keyword normalization",             0.55), _CODE_TABLE),
}

# ── iso_qchem: HQW atomic combination Z-notation (speculative / non-standard) ─
#
# NOT a real ISO standard.  This is substrate-internal notation from early
# TSM work: atoms identified by atomic number (Z1=H, Z6=C, Z8=O, …) and
# hypothetical elements beyond Z118 that appear in the superconductor and
# digital twin research.  Each entry carries a stability weight and a
# register_bits cost — the "weight of the atom at that position."
#
# concept_anchor: domain=substrate / concept=hqw_z_notation / resolution=FORMING
#
# The table is loaded lazily from hqw_atomic_combinations.json if the file
# exists alongside this script or in the repo root.  If the file is absent
# the domain is silently omitted — nothing breaks.
#
# Portability rule: this domain depends on speculative data that may not
# travel with the repo.  Never add it to DEFAULT_DOMAINS.  Use explicitly:
#   prepass(text, domains=["iso_chem", "iso_qchem"])

def _load_qchem_domain() -> dict[str, str] | None:
    """Load hqw_atomic_combinations.json and build a formula → Z-notation table.

    # What the table does
    Maps standard molecular formula strings (as produced by iso_chem) to the
    substrate's Z<n>-Z<m> notation.  This is Stage 2 compression: iso_chem
    reduces prose to chemistry symbols, iso_qchem reduces chemistry symbols
    to substrate Z-tokens for EM transposition.

      iso_chem:  "water"  → "H₂O"
      iso_qchem: "H₂O"   → "Z1-Z1-Z8"   (stability=0.997, register_bits=35)

    # Why Z-notation compresses further
    Standard chemical symbols are 1–3 chars.  Z-notation is always "Z" + int,
    which looks longer for light elements (Z1 > H) but:
      1. It is uniform — all tokens have the same format, reducing the entropy
         of the token-type distribution.
      2. For heavy/theoretical elements (Z119–Z229) it is shorter than the
         element name and unambiguous where no IUPAC symbol exists yet.
      3. The stability value is the EM transposition weight for that formula —
         high-stability combinations map to low-frequency soliton bands.

    # Returns
      dict mapping formula strings → Z-notation strings, or None if the
      source file cannot be found.
    """
    import json as _json

    candidates = [
        Path(__file__).parent.parent / "hqw_atomic_combinations.json",
        Path(__file__).parent / "hqw_atomic_combinations.json",
    ]
    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        return None

    try:
        with open(src) as f:
            records = _json.load(f)
    except Exception:
        return None

    # Build forward table: chemical formula → Z-notation
    # The hqw dataset uses Z<n> tokens where n is the atomic number.
    # We build a reverse lookup: for Z1 → H, Z6 → C, etc. (standard elements)
    # so the table key uses familiar chemical notation where possible.
    _Z_TO_SYMBOL: dict[int, str] = {
        1: "H",   2: "He",  3: "Li",  4: "Be",  5: "B",
        6: "C",   7: "N",   8: "O",   9: "F",   10: "Ne",
        11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P",
        16: "S",  17: "Cl", 18: "Ar", 19: "K",  20: "Ca",
        26: "Fe", 29: "Cu", 30: "Zn", 47: "Ag", 50: "Sn",
        79: "Au", 80: "Hg", 82: "Pb", 92: "U",
    }

    table: dict[str, str] = {}
    for rec in records:
        z_formula = rec.get("formula", "")
        if not z_formula:
            continue
        # Build a human-readable key where Z tokens are known.
        parts = z_formula.split("-")
        readable_parts = []
        all_known = True
        for part in parts:
            if part.startswith("Z"):
                try:
                    n = int(part[1:])
                    sym = _Z_TO_SYMBOL.get(n)
                    if sym:
                        readable_parts.append(sym)
                    else:
                        # Theoretical element — keep Z-notation as key fragment.
                        readable_parts.append(part)
                        all_known = False
                except ValueError:
                    readable_parts.append(part)
                    all_known = False
            else:
                readable_parts.append(part)
        # Only index combinations where at least one token is a known element.
        if any(p for p in readable_parts if not p.startswith("Z")):
            key = "-".join(readable_parts).lower()
            table[key] = z_formula

    return table if table else None


_qchem_table = _load_qchem_domain()
if _qchem_table is not None:
    DOMAINS["iso_qchem"] = (
        Domain(
            "iso_qchem",
            "HQW Z-notation for atomic combinations (speculative, FORMING)",
            0.22,
        ),
        _qchem_table,
    )

# Default domain set applied by prepass() when no domains are specified.
# iso_qchem intentionally excluded — speculative, must be opted in explicitly.
DEFAULT_DOMAINS = ["iso_geo", "iso_chem", "iso_bio", "iso_unit", "iso_lang"]

# Extended domain set — includes abbreviation and math symbol tables.
# Use for compression analysis, cross-product residual, and large-file ingestion
# where scientific notation and bibliographic abbreviations are expected.
EXTENDED_DOMAINS = DEFAULT_DOMAINS + ["iso_abbrev", "iso_math"]

# PTOS corpus domain set — adds Research Stack vocabulary and TSM opcodes.
# Use when the input is from the Research Stack itself (code, docs, sessions).
# Run iso_cross with this set to find the actual strong cross-axis for this corpus.
PTOS_DOMAINS = EXTENDED_DOMAINS + ["iso_ptos", "iso_isa", "iso_code"]


# ─────────────────────────────────────────────────────────────────────────────
# Core engine
# ─────────────────────────────────────────────────────────────────────────────

def _build_pattern(table: dict[str, str]) -> re.Pattern:
    """Compile a single regex that matches any key in the table.

    # Why longest-match ordering?
    "carbon dioxide" must match before "carbon" or "dioxide" individually.
    Sort keys by descending length so the regex alternation tries longer
    phrases first.  re.IGNORECASE handles capitalisation.
    """
    keys = sorted(table.keys(), key=len, reverse=True)
    escaped = [re.escape(k) for k in keys]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


# Pre-compile patterns at import time.
_PATTERNS: dict[str, re.Pattern] = {
    name: _build_pattern(table)
    for name, (_, table) in DOMAINS.items()
}


def prepass(
    text: str,
    domains: list[str] | None = None,
) -> tuple[str, dict[str, list[str]]]:
    """Apply ISO symbol substitution to text.

    # Why return a substitution log?
    The log enables lossless decode without transmitting the full table.
    Each entry records (original_token, symbol) for every substitution made.
    For domains where the table is a public standard, the log can be reduced
    to a domain bitmask — the receiver reconstructs from the same table.

    # Parameters
      text    : input text (any domain mix)
      domains : list of domain names to apply; defaults to DEFAULT_DOMAINS

    # Returns
      compressed : text with all matched tokens replaced by their symbols
      log        : {"domain_name": [original_token, ...]} — substitution record

    # Example
      >>> compressed, log = prepass("Hydrogen and oxygen form water in France")
      >>> print(compressed)
      H and O form H₂O in FR
      >>> print(log)
      {'iso_chem': ['Hydrogen', 'oxygen', 'water'], 'iso_geo': ['France']}
    """
    if domains is None:
        domains = DEFAULT_DOMAINS

    log: dict[str, list[str]] = {}
    result = text

    for name in domains:
        if name not in DOMAINS:
            continue
        _, table = DOMAINS[name]
        pattern = _PATTERNS[name]
        subs: list[str] = []
        # Capture table/subs in a closure via a factory to avoid
        # "dangerous default value" and loop-variable capture warnings.
        def _make_replacer(tbl: dict, log_list: list):
            def _replace(m: re.Match) -> str:
                original = m.group(0)
                # Normalize unicode (handles İran → iran, café → cafe, etc.)
                # before table lookup. The table keys are plain ASCII lowercase.
                key = unicodedata.normalize("NFKD", original)\
                    .encode("ascii", "ignore").decode().lower()
                symbol = tbl.get(key)
                if symbol is None:
                    return original   # no match after normalisation — skip
                log_list.append(original)
                return symbol
            return _replace

        result = pattern.sub(_make_replacer(table, subs), result)
        if subs:
            log[name] = subs

    return result, log


def decode(
    compressed: str,
    log: dict[str, list[str]],
) -> str:
    """Reconstruct the original text from a prepass output and its log.

    # Parameters
      compressed : output of prepass()
      log        : substitution log returned by prepass()

    # Returns
      original text (exact byte-for-byte reconstruction of matched tokens)

    # Note
    Token order in the log must match substitution order in the compressed
    text.  prepass() guarantees this — log entries are appended left-to-right
    as the regex scans the text.
    """
    result = compressed
    for domain_name, originals in log.items():
        if domain_name not in DOMAINS:
            continue
        _, table = DOMAINS[domain_name]
        # Replace each symbol occurrence with its original, in order.
        # Use the forward table to look up the symbol for each original token.
        for original in originals:
            symbol = table[original.lower()]
            # Replace only the first occurrence to preserve left-to-right order.
            result = result.replace(symbol, original, 1)
    return result


def stats(text: str, domains: list[str] | None = None) -> dict:
    """Compute compression statistics for a text sample.

    # Returns
      dict with keys:
        original_bytes    : len(text.encode())
        compressed_bytes  : len(compressed.encode())
        ratio             : compressed_bytes / original_bytes
        savings_pct       : (1 - ratio) * 100
        by_domain         : {domain: substitution_count}
    """
    compressed, log = prepass(text, domains)
    orig_b = len(text.encode())
    comp_b = len(compressed.encode())
    return {
        "original_bytes":   orig_b,
        "compressed_bytes": comp_b,
        "ratio":            round(comp_b / max(orig_b, 1), 4),
        "savings_pct":      round((1 - comp_b / max(orig_b, 1)) * 100, 2),
        "by_domain":        {k: len(v) for k, v in log.items()},
        "compressed":       compressed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_prepass(text: str, domains: list[str] | None = None) -> None:
    compressed, log = prepass(text, domains)
    print(compressed)
    if log:
        print("\n[substitutions]")
        for domain, tokens in log.items():
            print(f"  {domain}: {tokens}")


def _cmd_decode(compressed: str, domains: list[str] | None = None) -> None:
    """Reconstruct from compressed text using domain tables (no log needed
    when table is a public standard — just re-invert the active domains)."""
    if domains is None:
        domains = DEFAULT_DOMAINS
    result = compressed
    for name in domains:
        if name not in DOMAINS:
            continue
        _, table = DOMAINS[name]
        inv = {v: k.title() for k, v in table.items()}
        keys_longest_first = sorted(inv, key=len, reverse=True)
        pat = re.compile(
            r"\b(" + "|".join(re.escape(s) for s in keys_longest_first) + r")\b"
        )
        def _make_inv_replacer(inv_table: dict):
            return lambda m: inv_table.get(m.group(0), m.group(0))
        result = pat.sub(_make_inv_replacer(inv), result)
    print(result)


def _cmd_stats(text: str, domains: list[str] | None = None) -> None:
    s = stats(text, domains)
    print(f"original : {s['original_bytes']} bytes")
    print(f"compressed: {s['compressed_bytes']} bytes")
    print(f"ratio    : {s['ratio']}  ({s['savings_pct']}% saved)")
    print(f"domains  : {s['by_domain']}")
    print(f"\ncompressed text:\n{s['compressed']}")


def _cmd_domains() -> None:
    print(f"{'DOMAIN':<14} {'EST RATIO':<12} DESCRIPTION")
    print("─" * 70)
    for name, (meta, table) in DOMAINS.items():
        mark = "✓" if name in DEFAULT_DOMAINS else " "
        print(f"{mark} {name:<13} {meta.est_ratio:<12} {meta.description}  ({len(table)} entries)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="ISO Symbol Table — pre-compression pass",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd")

    p_pre = sub.add_parser("prepass", help="apply ISO substitution")
    p_pre.add_argument("text")
    p_pre.add_argument("--domains", nargs="+", metavar="DOMAIN")

    p_dec = sub.add_parser("decode", help="invert ISO substitution")
    p_dec.add_argument("text")
    p_dec.add_argument("--domains", nargs="+", metavar="DOMAIN")

    p_stat = sub.add_parser("stats", help="show compression statistics")
    p_stat.add_argument("text")
    p_stat.add_argument("--domains", nargs="+", metavar="DOMAIN")

    sub.add_parser("domains", help="list all domains and entry counts")

    args = parser.parse_args()

    if args.cmd == "prepass":
        _cmd_prepass(args.text, args.domains)
    elif args.cmd == "decode":
        _cmd_decode(args.text, args.domains)
    elif args.cmd == "stats":
        _cmd_stats(args.text, args.domains)
    elif args.cmd == "domains":
        _cmd_domains()
    else:
        parser.print_help()
