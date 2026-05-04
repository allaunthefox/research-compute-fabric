#!/usr/bin/env python3
"""
Add PeptideMoE modules to the math_entities database

This script adds the new PeptideMoE Lean modules to the database
so they can be indexed and reviewed by the swarm.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = "/home/allaun/Documents/Research Stack/data/math_entities.db"

def add_peptide_moe_modules():
    """Add PeptideMoE modules to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # PeptideMoE modules to add
    modules = [
        {
            "entity_id": "peptide_moe_001",
            "subject": "PeptideMoE",
            "secondary_subjects": "Mixture-of-Experts,conformational,peptide,thermodynamics",
            "name": "Peptide MoE Core Specification",
            "statement": "φ_peptide = structuralCoherence / (freeEnergy + c0); freeEnergy = E_internal + k_B·T·S_conformational; moeDrift = Σ g_k·(advice_φ,k, advice_ψ,k)",
            "proof_status": "theorems",
            "formal_status": "noncomputable",
            "lean_module": "0-Core-Formalism/lean/Semantics/Semantics/PeptideMoE.lean",
            "dependencies": "Mathlib.Data.Real.Basic,Mathlib.Data.List.Basic",
            "citations": "OTOM v2.0.0-Cambrian-Bind",
            "complexity_score": 85,
            "year": 2026
        },
        {
            "entity_id": "peptide_moe_002",
            "subject": "PeptideMoE",
            "secondary_subjects": "examples,toy,instantiation",
            "name": "Peptide MoE Toy Examples",
            "statement": "Concrete toy instantiation of the abstract peptide-MoE specification with fixed thermodynamic/admissibility parameters, three toy experts, three toy candidate endpoints, and example reports.",
            "proof_status": "definitions",
            "formal_status": "noncomputable",
            "lean_module": "0-Core-Formalism/lean/Semantics/Semantics/PeptideMoEExamples.lean",
            "dependencies": "Semantics.PeptideMoE",
            "citations": "OTOM v2.0.0-Cambrian-Bind",
            "complexity_score": 60,
            "year": 2026
        },
        {
            "entity_id": "peptide_moe_003",
            "subject": "PeptideMoE",
            "secondary_subjects": "failure,injection,pathological",
            "name": "Peptide MoE Failure Scenarios",
            "statement": "Failure-injection scenarios documenting why guardrails matter: c0=0 causes denominator failure, loose steric bounds admit clashing states, negative gates break MoE control, unbounded advice causes pathological drift.",
            "proof_status": "definitions",
            "formal_status": "noncomputable",
            "lean_module": "0-Core-Formalism/lean/Semantics/Semantics/PeptideMoEFailure.lean",
            "dependencies": "Semantics.PeptideMoE,Semantics.PeptideMoEExamples",
            "citations": "OTOM v2.0.0-Cambrian-Bind",
            "complexity_score": 70,
            "year": 2026
        },
        {
            "entity_id": "peptide_moe_004",
            "subject": "PeptideMoE",
            "secondary_subjects": "repair,guardrails,safety",
            "name": "Peptide MoE Repair Theorems",
            "statement": "Repair theorems documenting guardrails that restore safety: positive c0 recovers denominator safety, strict steric bounds reject clashing states, nonnegative gates guarantee unit mass, bounded advice controls drift.",
            "proof_status": "theorems",
            "formal_status": "noncomputable",
            "lean_module": "0-Core-Formalism/lean/Semantics/Semantics/PeptideMoERepair.lean",
            "dependencies": "Semantics.PeptideMoE,Semantics.PeptideMoEExamples,Semantics.PeptideMoEFailure",
            "citations": "OTOM v2.0.0-Cambrian-Bind",
            "complexity_score": 75,
            "year": 2026
        }
    ]
    
    # Insert each module
    for module in modules:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO math_entities
                (entity_id, subject, secondary_subjects, name, statement, proof_status,
                 formal_status, lean_module, dependencies, citations, complexity_score, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                module["entity_id"],
                module["subject"],
                module["secondary_subjects"],
                module["name"],
                module["statement"],
                module["proof_status"],
                module["formal_status"],
                module["lean_module"],
                module["dependencies"],
                module["citations"],
                module["complexity_score"],
                module["year"]
            ))
            print(f"✓ Added: {module['name']}")
        except Exception as e:
            print(f"✗ Error adding {module['name']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\nAdded {len(modules)} PeptideMoE modules to database.")
    print(f"Database: {DB_PATH}")

if __name__ == "__main__":
    add_peptide_moe_modules()
