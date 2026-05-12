#!/usr/bin/env python3
"""Build a receipt-backed registry of language-set density-marker candidates.

This intentionally stores density markers, category geometry, and source
boundaries, not copied lexicons or protected glyph sets.  RRC can use these
packets as language-set shape candidates while keeping whole-language promotion
conservative.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "language_set_manifold_graph"
REGISTRY_JSONL = OUT_DIR / "language_set_registry.jsonl"
NODES_CSV = OUT_DIR / "language_set_graph_nodes.csv"
EDGES_CSV = OUT_DIR / "language_set_graph_edges.csv"
RECEIPT_JSON = OUT_DIR / "language_set_registry_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


LANGUAGE_SETS: list[dict[str, Any]] = [
    {
        "language_set_id": "LANG.ITHKUIL.DESIGN_PRECEDENT.0001",
        "name": "Ithkuil",
        "family": "constructed philosophical language",
        "source_urls": [
            "https://www.ithkuil.net/00_intro.html",
            "https://ithkuil.net/02_morpho-phonology.html",
            "https://ithkuil.net/03_morphology.html",
            "https://ithkuil.net/11_script.htm",
        ],
        "license_boundary": "Extract category geometry and morpho-phonemic design only; do not copy lexicon or script identity as payload.",
        "scale_band": "official grammar documentation scope, 2026-05-08 snapshot",
        "category_axes": [
            "root",
            "stem",
            "formative",
            "adjunct",
            "configuration",
            "affiliation",
            "perspective",
            "case",
            "validation",
            "bias",
            "tone",
            "stress",
        ],
        "density_markers": [
            "multi-axis_morphology",
            "semantic_category_portmanteau",
            "morpho_phonemic_surface",
            "prosodic_metadata",
        ],
        "compression_read": "semantic category portmanteau over dense morphology",
    },
    {
        "language_set_id": "LANG.KLINGON.FICTIONAL.0001",
        "name": "Klingon",
        "family": "fictional constructed language",
        "source_urls": [
            "https://www.kli.org/muz_Segh/grammar/",
            "https://en.wikipedia.org/wiki/Klingon_language",
        ],
        "license_boundary": "Use grammar-shape metadata and public reference pointers only; do not copy protected franchise lexicon as payload.",
        "scale_band": "KLI grammar pages plus public encyclopedia overview",
        "category_axes": [
            "phoneme_inventory",
            "affix_order",
            "noun_suffix_class",
            "verb_suffix_class",
            "object_verb_subject_order",
            "evidential_or_attitude_marking",
        ],
        "density_markers": [
            "strict_affix_slotting",
            "unusual_phonotactic_profile",
            "object_verb_subject_order",
        ],
        "compression_read": "strict affix slots and unusual phonotactic profile as typed route surface",
    },
    {
        "language_set_id": "LANG.DOTHRAKI.FICTIONAL.0001",
        "name": "Dothraki",
        "family": "fictional constructed language",
        "source_urls": [
            "https://en.wikipedia.org/wiki/Dothraki_language",
            "https://dothraki.com/dl/dothraki101.pdf",
        ],
        "license_boundary": "Use typological and grammar-shape metadata only; Dothraki language material is HBO-associated and remains non-payload.",
        "scale_band": "public overview and introductory PDF metadata only",
        "category_axes": [
            "naturalistic_phonology",
            "nominal_case",
            "verb_conjugation",
            "animacy_or_cultural_domain",
            "word_order",
        ],
        "density_markers": [
            "naturalistic_morphology",
            "domain_biased_lexical_field",
            "case_and_verb_inflection",
        ],
        "compression_read": "naturalistic conlang morphology and domain-biased lexicon as HOLD-only prior",
    },
    {
        "language_set_id": "LANG.HIGH_VALYRIAN.FICTIONAL.0001",
        "name": "High Valyrian",
        "family": "fictional constructed language",
        "source_urls": [
            "https://en.wikipedia.org/wiki/Valyrian_languages",
            "https://wiki.languageinvention.com/index.php?title=High_Valyrian",
        ],
        "license_boundary": "Use grammar category metadata only; franchise lexicon and examples are not payload.",
        "scale_band": "public overview metadata only",
        "category_axes": [
            "noun_class",
            "case",
            "number",
            "gender",
            "verb_inflection",
            "derivational_family",
        ],
        "density_markers": [
            "inflectional_bundle",
            "noun_class_case_number",
            "derivational_family",
        ],
        "compression_read": "large inflectional category bundle as language graph prior",
    },
    {
        "language_set_id": "LANG.NAVI.FICTIONAL.0001",
        "name": "Na'vi",
        "family": "fictional constructed language",
        "source_urls": [
            "https://learnnavi.org/",
            "https://kelutral.org/linguistics",
            "https://en.wikipedia.org/wiki/Na%CA%BCvi_language",
        ],
        "license_boundary": "Use grammar topology and source pointers only; do not copy lexicon as payload.",
        "scale_band": "public grammar-reference pointers and overview metadata",
        "category_axes": [
            "case_marking",
            "free_word_order",
            "singular_dual_trial_plural",
            "infix_position",
            "ejectives",
            "alienness_profile",
        ],
        "density_markers": [
            "case_rich_alignment",
            "number_distinction_ladder",
            "infix_position_marker",
        ],
        "compression_read": "case-rich, number-rich grammar as typed manifold candidate",
    },
    {
        "language_set_id": "LANG.QUENYA.TOLKIEN.0001",
        "name": "Quenya",
        "family": "Tolkienian Elvish language",
        "source_urls": [
            "https://www.elvish.org/resources.html",
            "https://eldamo.org/",
            "https://tolkiengateway.net/wiki/Elvish",
        ],
        "license_boundary": "Use scholarly reference metadata and category geometry; Tolkien lexicon/glyph identity is not internal payload.",
        "scale_band": "reference index metadata only, not vocabulary ingestion",
        "category_axes": [
            "case",
            "number",
            "declension",
            "phonological_history",
            "script_view",
            "neo_language_uncertainty",
        ],
        "density_markers": [
            "diachronic_layering",
            "inflectional_case_system",
            "script_view_separation",
        ],
        "compression_read": "diachronic philological layers and inflectional axes as graph topology",
    },
    {
        "language_set_id": "LANG.SINDARIN.TOLKIEN.0001",
        "name": "Sindarin",
        "family": "Tolkienian Elvish language",
        "source_urls": [
            "https://www.elvish.org/resources.html",
            "https://eldamo.org/",
            "https://tolkiengateway.net/wiki/Elvish",
        ],
        "license_boundary": "Use scholarly reference metadata and mutation/category geometry only; do not copy lexicon/glyph identity as payload.",
        "scale_band": "reference index metadata only, not vocabulary ingestion",
        "category_axes": [
            "initial_mutation",
            "case_or_relation_marking",
            "number",
            "phonological_history",
            "script_view",
            "neo_language_uncertainty",
        ],
        "density_markers": [
            "initial_mutation_edge",
            "phonological_history_layer",
            "script_view_separation",
        ],
        "compression_read": "mutation edges as manifold torsion and repair evidence",
    },
    {
        "language_set_id": "LANG.LOJBAN.LOGICAL.0001",
        "name": "Lojban",
        "family": "logical constructed language",
        "source_urls": [
            "https://lojban.github.io/cll/",
            "https://lojban.org/publications/level0/brochure-utf/grammar.html",
        ],
        "license_boundary": "Use published grammar and parser-shape metadata; quote/copy only under source license when explicitly allowed.",
        "scale_band": "Complete Lojban Language reference and level-0 grammar overview",
        "category_axes": [
            "predicate_logic",
            "unambiguous_parse",
            "selmaho",
            "bridi",
            "sumti",
            "cmavo",
            "rafsi",
        ],
        "density_markers": [
            "unambiguous_parse",
            "predicate_argument_frame",
            "machine_grammar_table",
        ],
        "compression_read": "machine-parseable logic grammar as high-proof-readiness language graph",
    },
    {
        "language_set_id": "LANG.TOKIPONA.MINIMAL.0001",
        "name": "Toki Pona",
        "family": "minimal constructed language",
        "source_urls": [
            "https://www.tokipona.org/",
            "https://sona.pona.la/wiki/Grammar",
        ],
        "license_boundary": "Use minimal-grammar metadata and source pointers; official book contents are not payload.",
        "scale_band": "official site plus descriptive grammar page",
        "category_axes": [
            "small_lexicon",
            "analytic_grammar",
            "particle_frame",
            "modifier_chain",
            "semantic_broadening",
            "proper_name_adaptation",
        ],
        "density_markers": [
            "minimal_lexicon",
            "particle_frame",
            "context_residual_pressure",
        ],
        "compression_read": "minimal lexicon plus high context residual as compression negative/control pair",
    },
    {
        "language_set_id": "LANG.ESPERANTO.AUX.0001",
        "name": "Esperanto",
        "family": "international auxiliary language",
        "source_urls": [
            "https://en.wikipedia.org/wiki/Esperanto",
            "https://lernu.net/gramatiko",
        ],
        "license_boundary": "Use grammar-category metadata and source pointers; no bulk corpus ingestion in this registry.",
        "scale_band": "public grammar overview metadata",
        "category_axes": [
            "regular_affixation",
            "part_of_speech_suffix",
            "accusative_marker",
            "correlative_table",
            "agglutination",
        ],
        "density_markers": [
            "regular_affixation",
            "part_of_speech_suffix",
            "correlative_table",
        ],
        "compression_read": "regular derivational morphology as reusable category graph",
    },
    {
        "language_set_id": "LANG.BLISSYMBOLICS.AAC.0001",
        "name": "Blissymbolics",
        "family": "constructed semantic symbol system",
        "source_urls": [
            "https://www.blissymbolics.org/",
            "https://en.wikipedia.org/wiki/Blissymbols",
        ],
        "license_boundary": "Use compositional-symbol design grammar only; symbol glyphs and vocabulary require explicit permission/licensing.",
        "scale_band": "public organizational overview metadata",
        "category_axes": [
            "basic_character",
            "compound_symbol",
            "semantic_modifier",
            "pictograph",
            "ideograph",
            "aac_context",
        ],
        "density_markers": [
            "semantic_radical_composition",
            "compound_symbol_law",
            "modifier_relation_table",
        ],
        "compression_read": "compositional semantic radicals as logogram graph precedent",
    },
    {
        "language_set_id": "CODE.APL.ARRAY.0001",
        "name": "APL",
        "family": "array programming language",
        "source_urls": [
            "https://aplwiki.com/wiki/APL",
            "https://en.wikipedia.org/wiki/APL_(programming_language)",
        ],
        "license_boundary": "Use language-density markers and operator-family metadata only; do not copy manuals or proprietary glyph tables.",
        "scale_band": "public language overview metadata",
        "category_axes": ["array_rank", "primitive_function", "operator_modifier", "tacit_composition", "shape_polymorphism"],
        "density_markers": ["single_glyph_high_rank_operator", "array_wide_transform", "implicit_iteration", "rank_polymorphic_surface"],
        "compression_read": "one glyph or opcode can imply an array-scale transform",
    },
    {
        "language_set_id": "CODE.J.ARRAY.0001",
        "name": "J",
        "family": "array programming language",
        "source_urls": [
            "https://www.jsoftware.com/help/dictionary/contents.htm",
            "https://en.wikipedia.org/wiki/J_(programming_language)",
        ],
        "license_boundary": "Use ASCII-density and operator-family markers only; do not copy dictionary text as payload.",
        "scale_band": "public dictionary and overview metadata",
        "category_axes": ["verb", "adverb", "conjunction", "rank", "fork_hook_train"],
        "density_markers": ["ascii_symbol_modifier", "tacit_train", "rank_annotation", "operator_family_digraph"],
        "compression_read": "ASCII-safe dense operator families as byte-native logogram precedent",
    },
    {
        "language_set_id": "CODE.BQN.ARRAY.0001",
        "name": "BQN",
        "family": "array programming language",
        "source_urls": [
            "https://mlochbaum.github.io/BQN/",
            "https://mlochbaum.github.io/BQN/doc/index.html",
        ],
        "license_boundary": "Use public design/category markers only; do not copy documentation examples as payload.",
        "scale_band": "public language documentation metadata",
        "category_axes": ["function", "modifier", "array_shape", "block", "train"],
        "density_markers": ["modern_apl_glyph_density", "modifier_scope", "array_shape_carrier", "tacit_composition"],
        "compression_read": "modern array glyph density with explicit modifier scope",
    },
    {
        "language_set_id": "CODE.UIUA.ARRAY_STACK.0001",
        "name": "Uiua",
        "family": "stack-based array programming language",
        "source_urls": ["https://www.uiua.org/", "https://www.uiua.org/docs"],
        "license_boundary": "Use operator-density and stack/array design markers only; do not copy docs/examples as payload.",
        "scale_band": "public language documentation metadata",
        "category_axes": ["stack_effect", "array_shape", "glyph_primitive", "modifier", "formatter_view"],
        "density_markers": ["stack_effect_as_type", "glyph_primitive", "array_stack_fusion", "formatter_as_surface_view"],
        "compression_read": "stack effects and array glyphs expose compact executable shape",
    },
    {
        "language_set_id": "CODE.FORTH.CONCATENATIVE.0001",
        "name": "Forth",
        "family": "concatenative stack programming language",
        "source_urls": ["https://forth-standard.org/", "https://en.wikipedia.org/wiki/Forth_(programming_language)"],
        "license_boundary": "Use standard stack-effect and word-composition markers only; source texts remain external.",
        "scale_band": "public standard and overview metadata",
        "category_axes": ["word", "stack_effect", "dictionary", "immediate_word", "threaded_code"],
        "density_markers": ["stack_effect_signature", "dictionary_extensibility", "concatenative_composition", "threaded_code_density"],
        "compression_read": "word dictionaries plus stack effects as executable manifold graph",
    },
    {
        "language_set_id": "CODE.PROLOG.LOGIC.0001",
        "name": "Prolog",
        "family": "logic programming language",
        "source_urls": ["https://www.swi-prolog.org/", "https://en.wikipedia.org/wiki/Prolog"],
        "license_boundary": "Use logic-programming density markers only; no corpus or library ingestion in registry.",
        "scale_band": "public language overview metadata",
        "category_axes": ["fact", "rule", "unification", "backtracking", "predicate_arity"],
        "density_markers": ["unification_as_control_flow", "implicit_search_tree", "predicate_arity_type", "backtracking_surface"],
        "compression_read": "implicit search/control encoded by facts and unification",
    },
    {
        "language_set_id": "CODE.HASKELL.FUNCTIONAL.0001",
        "name": "Haskell",
        "family": "typed functional programming language",
        "source_urls": ["https://www.haskell.org/", "https://www.haskell.org/onlinereport/haskell2010/"],
        "license_boundary": "Use type-system and laziness markers only; no library/code ingestion in registry.",
        "scale_band": "public language report and overview metadata",
        "category_axes": ["typeclass", "higher_kind", "lazy_evaluation", "monad", "algebraic_data_type"],
        "density_markers": ["typeclass_dictionary", "higher_kinded_abstraction", "lazy_thunk_graph", "monadic_effect_marker"],
        "compression_read": "type-level structure and laziness create dense deferred computation graph",
    },
    {
        "language_set_id": "CODE.LEAN.PROOF.0001",
        "name": "Lean",
        "family": "dependent type theorem proving language",
        "source_urls": ["https://lean-lang.org/", "https://leanprover.github.io/theorem_proving_in_lean4/"],
        "license_boundary": "Use proof-language density markers and local module metadata only; no external code ingestion.",
        "scale_band": "public Lean 4 documentation plus local Research Stack usage",
        "category_axes": ["dependent_type", "inductive_type", "theorem", "tactic", "kernel_check"],
        "density_markers": ["proof_term_compression", "dependent_type_payload", "tactic_script_as_generator", "kernel_check_receipt"],
        "compression_read": "proof terms and tactics separate generator from checked payload",
    },
    {
        "language_set_id": "CODE.RUST.SYSTEMS.0001",
        "name": "Rust",
        "family": "systems programming language",
        "source_urls": ["https://www.rust-lang.org/", "https://doc.rust-lang.org/book/"],
        "license_boundary": "Use ownership/type-system density markers only; no crate/code ingestion in registry.",
        "scale_band": "public book and overview metadata",
        "category_axes": ["ownership", "borrow", "lifetime", "trait", "sum_type"],
        "density_markers": ["ownership_as_static_resource_graph", "lifetime_region_marker", "trait_bound_surface", "enum_match_partition"],
        "compression_read": "ownership and trait bounds encode resource topology statically",
    },
    {
        "language_set_id": "CODE.REGEX.FORMAL.0001",
        "name": "Regular Expressions",
        "family": "formal pattern language",
        "source_urls": ["https://en.wikipedia.org/wiki/Regular_expression", "https://www.regular-expressions.info/"],
        "license_boundary": "Use formal pattern-density markers only; no pattern corpus ingestion.",
        "scale_band": "public formal-language overview metadata",
        "category_axes": ["concatenation", "alternation", "quantifier", "character_class", "capture_group"],
        "density_markers": ["finite_automaton_surface", "quantifier_compression", "character_class_set_collapse", "capture_reference_edge"],
        "compression_read": "small pattern string expands to large accepted-language set",
    },
    {
        "language_set_id": "CODE.BRAINFUCK.ESOLANG.0001",
        "name": "Brainfuck",
        "family": "esoteric programming language",
        "source_urls": ["https://esolangs.org/wiki/Brainfuck", "https://en.wikipedia.org/wiki/Brainfuck"],
        "license_boundary": "Use instruction-set density markers only; no program corpus ingestion.",
        "scale_band": "public esolang overview metadata",
        "category_axes": ["data_pointer", "cell_increment", "loop_bracket", "io_instruction", "tape_state"],
        "density_markers": ["minimal_opcode_set", "tape_machine_surface", "loop_bracket_control", "extreme_context_residual"],
        "compression_read": "tiny opcode alphabet shifts complexity into tape/context residual",
    },
    {
        "language_set_id": "CODE.MALBOLGE.ESOLANG.0001",
        "name": "Malbolge",
        "family": "esoteric programming language",
        "source_urls": ["https://esolangs.org/wiki/Malbolge", "https://en.wikipedia.org/wiki/Malbolge"],
        "license_boundary": "Use weird-encoding density markers only; no program corpus ingestion.",
        "scale_band": "public esolang overview metadata",
        "category_axes": ["self_modification", "ternary_memory", "instruction_encryption", "crazy_operation", "control_transfer"],
        "density_markers": ["self_modifying_code", "encrypted_instruction_surface", "ternary_memory_model", "brain_hurt_density_marker"],
        "compression_read": "deliberate cognitive friction exposes weird encoding axes",
    },
    {
        "language_set_id": "CODE.WHITESPACE.ESOLANG.0001",
        "name": "Whitespace",
        "family": "esoteric programming language",
        "source_urls": ["https://esolangs.org/wiki/Whitespace", "https://en.wikipedia.org/wiki/Whitespace_(programming_language)"],
        "license_boundary": "Use invisible-token density markers only; no program corpus ingestion.",
        "scale_band": "public esolang overview metadata",
        "category_axes": ["space_tab_lf_token", "stack_instruction", "heap_access", "label_control", "io_instruction"],
        "density_markers": ["invisible_token_channel", "layout_as_opcode", "stack_machine_surface", "source_view_mismatch"],
        "compression_read": "presentation-invisible token stream proves payload/view separation",
    },
]


LANGCHAIN_SPLITTER_TARGETS: list[dict[str, Any]] = [
    {
        "code": "PYTHON",
        "name": "Python",
        "family": "indentation-sensitive programming language",
        "axes": ["indentation_block", "function", "class", "decorator", "import_graph"],
        "markers": ["indentation_as_block_boundary", "decorator_metadata_channel", "dunder_protocol_surface"],
    },
    {
        "code": "JAVA",
        "name": "Java",
        "family": "class-oriented programming language",
        "axes": ["class", "method", "annotation", "interface", "package"],
        "markers": ["annotation_metadata_channel", "nominal_type_hierarchy", "brace_block_boundary"],
    },
    {
        "code": "JS",
        "name": "JavaScript",
        "family": "prototype-based scripting language",
        "axes": ["function", "closure", "prototype", "async_boundary", "module"],
        "markers": ["closure_context_capture", "prototype_chain_surface", "async_callback_density"],
    },
    {
        "code": "TS",
        "name": "TypeScript",
        "family": "typed JavaScript language",
        "axes": ["type_annotation", "interface", "generic", "union_type", "module"],
        "markers": ["type_overlay_on_runtime_language", "structural_type_surface", "union_narrowing_marker"],
    },
    {
        "code": "GO",
        "name": "Go",
        "family": "concurrent systems language",
        "axes": ["goroutine", "channel", "interface", "package", "defer"],
        "markers": ["channel_concurrency_surface", "defer_control_marker", "structural_interface_density"],
    },
    {
        "code": "CPP",
        "name": "C++",
        "family": "multi-paradigm systems language",
        "axes": ["template", "namespace", "class", "pointer_reference", "preprocessor"],
        "markers": ["template_metaprogramming_surface", "preprocessor_dual_language", "ownership_implicit_residual"],
    },
    {
        "code": "C",
        "name": "C",
        "family": "systems programming language",
        "axes": ["function", "pointer", "struct", "macro", "translation_unit"],
        "markers": ["pointer_arithmetic_surface", "macro_preprocessor_channel", "manual_memory_context"],
    },
    {
        "code": "CSHARP",
        "name": "C#",
        "family": "managed typed programming language",
        "axes": ["class", "attribute", "generic", "linq_query", "async_task"],
        "markers": ["attribute_metadata_channel", "linq_query_surface", "managed_runtime_type_graph"],
    },
    {
        "code": "KOTLIN",
        "name": "Kotlin",
        "family": "null-safe JVM language",
        "axes": ["nullability", "extension_function", "data_class", "coroutine", "sealed_class"],
        "markers": ["nullability_type_marker", "extension_function_surface", "coroutine_suspension_marker"],
    },
    {
        "code": "SCALA",
        "name": "Scala",
        "family": "typed functional/object language",
        "axes": ["trait", "implicit", "case_class", "pattern_match", "higher_kind"],
        "markers": ["implicit_resolution_surface", "case_class_deconstruction", "typelevel_functional_density"],
    },
    {
        "code": "SWIFT",
        "name": "Swift",
        "family": "protocol-oriented programming language",
        "axes": ["protocol", "optional", "extension", "enum_associated_value", "async"],
        "markers": ["protocol_extension_surface", "optional_type_marker", "associated_value_enum"],
    },
    {
        "code": "RUBY",
        "name": "Ruby",
        "family": "dynamic object language",
        "axes": ["block", "module", "mixin", "method_missing", "dsl_surface"],
        "markers": ["block_closure_surface", "mixin_linearization", "dsl_by_metaprogramming"],
    },
    {
        "code": "PHP",
        "name": "PHP",
        "family": "template-oriented web language",
        "axes": ["php_block", "html_interleave", "namespace", "class", "array_shape"],
        "markers": ["template_code_interleave", "request_context_surface", "array_shape_overload"],
    },
    {
        "code": "PROTO",
        "name": "Protocol Buffers",
        "family": "schema/interface definition language",
        "axes": ["message", "field_number", "service", "enum", "wire_type"],
        "markers": ["field_number_wire_contract", "schema_as_codec_surface", "service_rpc_shape"],
    },
    {
        "code": "SOL",
        "name": "Solidity",
        "family": "smart-contract language",
        "axes": ["contract", "modifier", "event", "storage_slot", "payable"],
        "markers": ["modifier_as_gate_surface", "storage_layout_contract", "event_log_channel"],
    },
    {
        "code": "COBOL",
        "name": "COBOL",
        "family": "business record programming language",
        "axes": ["division", "paragraph", "record_layout", "picture_clause", "data_division"],
        "markers": ["record_layout_surface", "picture_clause_density", "division_section_boundary"],
    },
    {
        "code": "MARKDOWN",
        "name": "Markdown",
        "family": "lightweight markup language",
        "axes": ["heading", "code_fence", "list", "link", "frontmatter"],
        "markers": ["heading_hierarchy_surface", "code_fence_language_channel", "whitespace_formatting_residual"],
    },
    {
        "code": "LATEX",
        "name": "LaTeX",
        "family": "document and math markup language",
        "axes": ["command", "environment", "math_mode", "section", "macro"],
        "markers": ["macro_expansion_surface", "math_mode_channel", "environment_scope_boundary"],
    },
    {
        "code": "HTML",
        "name": "HTML",
        "family": "structured document markup language",
        "axes": ["tag", "attribute", "heading", "section", "dom_tree"],
        "markers": ["dom_tree_surface", "attribute_metadata_channel", "heading_section_boundary"],
    },
]


_existing_language_ids = {entry["language_set_id"] for entry in LANGUAGE_SETS}
for target in LANGCHAIN_SPLITTER_TARGETS:
    lang_id = f"CODE.{target['code']}.LANGCHAIN_SPLITTER.0001"
    if lang_id in _existing_language_ids:
        continue
    LANGUAGE_SETS.append(
        {
            "language_set_id": lang_id,
            "name": target["name"],
            "family": target["family"],
            "source_urls": [
                "https://api.python.langchain.com/en/latest/text_splitters/",
                "https://api.python.langchain.com/en/v0.0.354/text_splitter/langchain.text_splitter.Language.html",
            ],
            "license_boundary": (
                "Derived from LangChain language-aware splitter targets as density-marker metadata only; "
                "do not copy source programs, manuals, or syntax examples as payload."
            ),
            "scale_band": "LangChain text splitter language enum and splitter documentation metadata",
            "category_axes": target["axes"],
            "density_markers": target["markers"] + ["langchain_language_aware_split_boundary"],
            "compression_read": "language-aware splitting marks syntax boundaries that likely carry dense structure",
        }
    )


def build_packet(entry: dict[str, Any]) -> dict[str, Any]:
    node_types = ["root", "category", "density_marker", "surface", "portmanteau", "residual", "witness"]
    edge_types = ["realizes", "scopes", "mutates", "omits", "repairs", "contrasts", "projects_to"]
    nodes = [
        {"id": f"{entry['language_set_id']}:language", "type": "root", "label": entry["name"]},
        {"id": f"{entry['language_set_id']}:surface", "type": "surface", "label": "surface_views"},
        {"id": f"{entry['language_set_id']}:residual", "type": "residual", "label": "residual_policy"},
        {"id": f"{entry['language_set_id']}:witness", "type": "witness", "label": "source_and_scale_witness"},
    ]
    nodes.extend(
        {
            "id": f"{entry['language_set_id']}:category:{axis}",
            "type": "category",
            "label": axis,
        }
        for axis in entry["category_axes"]
    )
    nodes.extend(
        {
            "id": f"{entry['language_set_id']}:density:{marker}",
            "type": "density_marker",
            "label": marker,
        }
        for marker in entry["density_markers"]
    )
    edges = []
    for axis in entry["category_axes"]:
        edges.append(
            {
                "source": f"{entry['language_set_id']}:language",
                "target": f"{entry['language_set_id']}:category:{axis}",
                "type": "scopes",
            }
        )
        edges.append(
            {
                "source": f"{entry['language_set_id']}:category:{axis}",
                "target": f"{entry['language_set_id']}:surface",
                "type": "realizes",
            }
        )
    for marker in entry["density_markers"]:
        edges.append(
            {
                "source": f"{entry['language_set_id']}:language",
                "target": f"{entry['language_set_id']}:density:{marker}",
                "type": "scopes",
            }
        )
        edges.append(
            {
                "source": f"{entry['language_set_id']}:density:{marker}",
                "target": f"{entry['language_set_id']}:surface",
                "type": "realizes",
            }
        )
    edges.extend(
        [
            {
                "source": f"{entry['language_set_id']}:surface",
                "target": f"{entry['language_set_id']}:residual",
                "type": "omits",
            },
            {
                "source": f"{entry['language_set_id']}:residual",
                "target": f"{entry['language_set_id']}:surface",
                "type": "repairs",
            },
            {
                "source": f"{entry['language_set_id']}:witness",
                "target": f"{entry['language_set_id']}:language",
                "type": "contrasts",
            },
            {
                "source": f"{entry['language_set_id']}:language",
                "target": "RRCShape:LanguageSetManifoldGraph",
                "type": "projects_to",
            },
        ]
    )
    status = "CANDIDATE" if entry.get("scale_band") and "metadata" not in entry["scale_band"].lower() else "HOLD"
    packet = {
        "schema": "language_set_manifold_graph_v1",
        "rrc_shape": "LanguageSetManifoldGraph",
        "status": status,
        "admission_note": "CANDIDATE requires declared bounded scale band and replay evidence; HOLD entries are source/category/density-marker priors only.",
        "node_types": node_types,
        "edge_types": edge_types,
        **entry,
        "nodes": nodes,
        "edges": edges,
    }
    packet["packet_hash"] = sha256_text(stable_json(packet))
    return packet


def csv_escape(value: Any) -> str:
    text = str(value).replace('"', '""')
    return f'"{text}"'


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = [build_packet(entry) for entry in LANGUAGE_SETS]
    REGISTRY_JSONL.write_text("\n".join(stable_json(packet) for packet in packets) + "\n", encoding="utf-8")

    node_lines = ["language_set_id,node_id,node_type,label,status,packet_hash"]
    edge_lines = ["language_set_id,source,target,edge_type,status,packet_hash"]
    for packet in packets:
        for node in packet["nodes"]:
            node_lines.append(
                ",".join(
                    [
                        csv_escape(packet["language_set_id"]),
                        csv_escape(node["id"]),
                        csv_escape(node["type"]),
                        csv_escape(node["label"]),
                        csv_escape(packet["status"]),
                        csv_escape(packet["packet_hash"]),
                    ]
                )
            )
        for edge in packet["edges"]:
            edge_lines.append(
                ",".join(
                    [
                        csv_escape(packet["language_set_id"]),
                        csv_escape(edge["source"]),
                        csv_escape(edge["target"]),
                        csv_escape(edge["type"]),
                        csv_escape(packet["status"]),
                        csv_escape(packet["packet_hash"]),
                    ]
                )
            )
    NODES_CSV.write_text("\n".join(node_lines) + "\n", encoding="utf-8")
    EDGES_CSV.write_text("\n".join(edge_lines) + "\n", encoding="utf-8")

    status_counts: dict[str, int] = {}
    for packet in packets:
        status_counts[packet["status"]] = status_counts.get(packet["status"], 0) + 1

    receipt = {
        "schema": "language_set_manifold_registry_receipt_v1",
        "claim_boundary": "Registry records density markers and source/category graph priors only; it does not ingest protected lexicons, copy glyphs, or prove translation quality.",
        "rrc_shape": "LanguageSetManifoldGraph",
        "packet_count": len(packets),
        "status_counts": status_counts,
        "registry_jsonl": str(REGISTRY_JSONL.relative_to(REPO)),
        "nodes_csv": str(NODES_CSV.relative_to(REPO)),
        "edges_csv": str(EDGES_CSV.relative_to(REPO)),
        "language_set_ids": [packet["language_set_id"] for packet in packets],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT_JSON.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
