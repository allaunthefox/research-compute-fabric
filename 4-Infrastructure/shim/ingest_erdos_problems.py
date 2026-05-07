#!/usr/bin/env python3
"""
Ingest Erdős Problems from External Sources
=========================================
Pull in Erdős problems from external sources and ingest into local research database.
"""

import json
from pathlib import Path
from datetime import datetime

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")
RESEARCH_DIR = RESEARCH_STACK / "shared-data/data/germane/research"


# Erdős problems from Wikipedia and other sources
ERDOS_PROBLEMS = {
    "unsolved_conjectures": [
        {
            "name": "Erdős–Gyárfás conjecture",
            "description": "On cycles with lengths equal to a power of two in graphs with minimum degree 3.",
            "domain": "Graph Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Gy%C3%A1rf%C3%A1s_conjecture"
        },
        {
            "name": "Erdős–Hajnal conjecture",
            "description": "In a family of graphs defined by an excluded induced subgraph, every graph has either a large clique or a large independent set.",
            "domain": "Graph Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Hajnal_conjecture"
        },
        {
            "name": "Erdős–Mollin–Walsh conjecture",
            "description": "On consecutive triples of powerful numbers.",
            "domain": "Number Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Powerful_number"
        },
        {
            "name": "Erdős–Selfridge conjecture",
            "description": "A covering system with distinct moduli contains at least one even modulus.",
            "domain": "Number Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Covering_system"
        },
        {
            "name": "Erdős–Straus conjecture",
            "description": "For every integer n ≥ 2, the equation 4/n = 1/x + 1/y + 1/z has a solution in positive integers x, y, z.",
            "domain": "Diophantine Equations",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Straus_conjecture"
        },
        {
            "name": "Erdős conjecture on arithmetic progressions",
            "description": "If Σ_{a∈A} 1/a diverges, then A contains arbitrarily long arithmetic progressions.",
            "domain": "Additive Number Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s_conjecture_on_arithmetic_progressions"
        },
        {
            "name": "Erdős–Szekeres conjecture",
            "description": "On the number of points needed to ensure that a point set contains a large convex polygon.",
            "domain": "Discrete Geometry",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Szekeres_conjecture"
        },
        {
            "name": "Erdős–Turán conjecture on additive bases",
            "description": "If A is an additive basis of order 2 for the natural numbers, then the sum of reciprocals diverges: Σ_{a∈A} 1/a = ∞.",
            "domain": "Additive Number Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Tur%C3%A1n_conjecture_on_additive_bases"
        },
        {
            "name": "Erdős conjecture on quickly growing integer sequences",
            "description": "On integer sequences with rational reciprocal series (Sylvester's sequence).",
            "domain": "Number Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Sylvester%27s_sequence"
        },
        {
            "name": "Erdős–Oler conjecture on circle packing",
            "description": "On circle packing in an equilateral triangle with a number of circles one less than a triangular number.",
            "domain": "Geometry",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Circle_packing_in_an_equilateral_triangle"
        },
        {
            "name": "Minimum overlap problem",
            "description": "To estimate the limit of M(n).",
            "domain": "Combinatorics",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Minimum_overlap_problem"
        },
        {
            "name": "Erdős conjecture on ternary expansion of 2^n",
            "description": "The ternary expansion of 2^n contains at least one digit 2 for every n > 8.",
            "domain": "Number Theory",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős–Moser equation",
            "description": "The equation 1^k + 2^k + ... + (m-1)^k = m^k has no solutions except 1^1 + 2^1 = 3^1.",
            "domain": "Diophantine Equations",
            "status": "Unsolved",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Moser_equation"
        }
    ],
    "solved_conjectures": [
        {
            "name": "Erdős–Faber–Lovász conjecture",
            "description": "On coloring unions of cliques.",
            "domain": "Graph Theory",
            "status": "Solved (2021)",
            "solved_by": "Dong Yeap Kang, Tom Kelly, Daniela Kühn, Abhishek Methuku, and Deryk Osthus",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Faber%E2%80%93Lov%C3%A1sz_conjecture"
        },
        {
            "name": "Erdős sumset conjecture",
            "description": "On sets.",
            "domain": "Additive Combinatorics",
            "status": "Solved (2018)",
            "solved_by": "Joel Moreira, Florian Karl Richter, Donald Robertson",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s_sumset_conjecture"
        },
        {
            "name": "Burr–Erdős conjecture",
            "description": "On Ramsey numbers of graphs.",
            "domain": "Ramsey Theory",
            "status": "Solved (2015)",
            "solved_by": "Choongbum Lee",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Burr%E2%80%93Erd%C5%91s_conjecture"
        },
        {
            "name": "Erdős conjecture on equitable colorings",
            "description": "Now known as the Hajnal–Szemerédi theorem.",
            "domain": "Graph Theory",
            "status": "Solved (1970)",
            "solved_by": "András Hajnal and Endre Szemerédi",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős–Lovász conjecture on weak/strong delta-systems",
            "description": "On delta-systems.",
            "domain": "Combinatorics",
            "status": "Solved (1974)",
            "solved_by": "Michel Deza",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős–Heilbronn conjecture",
            "description": "In combinatorial number theory on the number of sums of two sets of residues modulo a prime.",
            "domain": "Number Theory",
            "status": "Solved (1994)",
            "solved_by": "Dias da Silva and Hamidoune",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős–Graham conjecture",
            "description": "In combinatorial number theory on monochromatic Egyptian fraction representations of unity.",
            "domain": "Number Theory",
            "status": "Solved (2000)",
            "solved_by": "Ernie Croot",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős–Stewart conjecture",
            "description": "On the Diophantine equation n! + 1 = p^k_a p_{k+1}^b.",
            "domain": "Number Theory",
            "status": "Solved (2001)",
            "solved_by": "Florian Luca",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Cameron–Erdős conjecture",
            "description": "On sum-free sets of integers.",
            "domain": "Number Theory",
            "status": "Solved (2003-2004)",
            "solved_by": "Ben Green and Alexander Sapozhenko",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős–Menger conjecture",
            "description": "On disjoint paths in infinite graphs.",
            "domain": "Graph Theory",
            "status": "Solved (2009)",
            "solved_by": "Ron Aharoni and Eli Berger",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős distinct distances problem",
            "description": "The correct exponent was proved in 2010 by Larry Guth and Nets Katz, but the correct power of log n is still undetermined.",
            "domain": "Discrete Geometry",
            "status": "Partially Solved (2010)",
            "solved_by": "Larry Guth and Nets Katz",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": "https://en.wikipedia.org/wiki/Erd%C5%91s_distinct_distances_problem"
        },
        {
            "name": "Erdős–Rankin conjecture on prime gaps",
            "description": "On prime gaps.",
            "domain": "Number Theory",
            "status": "Solved (2014)",
            "solved_by": "Ford, Green, Konyagin, and Tao",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős discrepancy problem",
            "description": "On partial sums of ±1-sequences.",
            "domain": "Number Theory",
            "status": "Solved (2015)",
            "solved_by": "Terence Tao",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős squarefree conjecture",
            "description": "Central binomial coefficients C(2n, n) are never squarefree for n > 4.",
            "domain": "Number Theory",
            "status": "Solved (1996)",
            "solved_by": "Various",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős primitive set conjecture",
            "description": "The sum Σ_{n∈A} 1/(n log n) for any primitive set A attains its maximum at the set of prime numbers.",
            "domain": "Number Theory",
            "status": "Solved (2022)",
            "solved_by": "Jared Duker Lichtman",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős–Sauer problem",
            "description": "About maximum number of edges an n-vertex graph can have without containing a k-regular subgraph.",
            "domain": "Graph Theory",
            "status": "Solved",
            "solved_by": "Oliver Janzer and Benny Sudakov",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős problem 728",
            "description": "Solved in 2026 using AI assistance.",
            "domain": "Unknown",
            "status": "Solved (2026)",
            "solved_by": "Kevin Barreto and Liam Price with ChatGPT 5.2 and Aristotle Lean API",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős problem 347",
            "description": "On subset sums of sequences with ratio limit 2.",
            "domain": "Combinatorics",
            "status": "Solved (2026)",
            "solved_by": "Enrique Barschkis",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        },
        {
            "name": "Erdős problem 369",
            "description": "Solved in March 2026 by 17-year-old Sky Yang (Yueer Yang).",
            "domain": "Unknown",
            "status": "Solved (2026)",
            "solved_by": "Sky Yang (Yueer Yang)",
            "source": "Wikipedia: List of conjectures by Paul Erdős",
            "url": ""
        }
    ],
    "additional_problems": [
        {
            "name": "Erdős–Ko–Rado theorem",
            "description": "Maximum size of intersecting families of k-subsets of {1,...,n} is C(n-1, k-1) for n ≥ 2k.",
            "domain": "Extremal Set Theory",
            "status": "Solved",
            "source": "Standard theorem",
            "url": ""
        },
        {
            "name": "Erdős–Ginzburg–Ziv theorem",
            "description": "Any 2n-1 integers contain n whose sum is divisible by n.",
            "domain": "Additive Number Theory",
            "status": "Solved",
            "source": "Standard theorem",
            "url": ""
        },
        {
            "name": "Erdős–Stone theorem",
            "description": "For any graph H, ex(n,H) = (1 - 1/χ(H)-1 + o(1))n²/2 where χ(H) is chromatic number.",
            "domain": "Extremal Graph Theory",
            "status": "Solved",
            "source": "Standard theorem",
            "url": ""
        },
        {
            "name": "Erdős–Rényi random graph model",
            "description": "Study properties of G(n,p) random graphs. Threshold phenomena for connectivity, giant component, Hamiltonicity.",
            "domain": "Random Graphs",
            "status": "Standard model",
            "source": "Standard model",
            "url": ""
        },
        {
            "name": "Erdős Hadamard conjecture",
            "description": "There exist Hadamard matrices of order 4k for all k.",
            "domain": "Linear Algebra",
            "status": "Unsolved",
            "source": "Standard conjecture",
            "url": ""
        },
        {
            "name": "Erdős–Moser problem",
            "description": "Find all solutions to 1/a + 1/b + 1/c + 1/d + 1/e = 1 in distinct positive integers.",
            "domain": "Diophantine Equations",
            "status": "Solved (only known solution)",
            "source": "Standard problem",
            "url": ""
        }
    ]
}


def create_erdos_problems_document():
    """Create a comprehensive Erdős problems document."""
    timestamp = datetime.now().isoformat()
    
    document = {
        "document_id": "erdos_problems_comprehensive_v1",
        "title": "Comprehensive Erdős Problems Collection",
        "created": timestamp,
        "source": "Wikipedia and other sources",
        "unsolved_conjectures": ERDOS_PROBLEMS["unsolved_conjectures"],
        "solved_conjectures": ERDOS_PROBLEMS["solved_conjectures"],
        "additional_problems": ERDOS_PROBLEMS["additional_problems"],
        "statistics": {
            "total_unsolved": len(ERDOS_PROBLEMS["unsolved_conjectures"]),
            "total_solved": len(ERDOS_PROBLEMS["solved_conjectures"]),
            "total_additional": len(ERDOS_PROBLEMS["additional_problems"]),
            "total_problems": len(ERDOS_PROBLEMS["unsolved_conjectures"]) + len(ERDOS_PROBLEMS["solved_conjectures"]) + len(ERDOS_PROBLEMS["additional_problems"])
        },
        "domains": {
            "Graph Theory": 0,
            "Number Theory": 0,
            "Discrete Geometry": 0,
            "Additive Number Theory": 0,
            "Diophantine Equations": 0,
            "Combinatorics": 0,
            "Extremal Set Theory": 0,
            "Ramsey Theory": 0,
            "Random Graphs": 0,
            "Linear Algebra": 0,
            "Additive Combinatorics": 0,
            "Geometry": 0,
            "Unknown": 0
        }
    }
    
    # Count domains
    all_problems = ERDOS_PROBLEMS["unsolved_conjectures"] + ERDOS_PROBLEMS["solved_conjectures"] + ERDOS_PROBLEMS["additional_problems"]
    for problem in all_problems:
        domain = problem["domain"]
        if domain in document["domains"]:
            document["domains"][domain] += 1
    
    return document


def main():
    print("=" * 70)
    print("  INGESTING ERDŐS PROBLEMS INTO LOCAL RESEARCH DATABASE")
    print("=" * 70)
    
    # Create document
    document = create_erdos_problems_document()
    
    print(f"\nStatistics:")
    print(f"  Total unsolved: {document['statistics']['total_unsolved']}")
    print(f"  Total solved: {document['statistics']['total_solved']}")
    print(f"  Total additional: {document['statistics']['total_additional']}")
    print(f"  Total problems: {document['statistics']['total_problems']}")
    
    print(f"\nDomain distribution:")
    for domain, count in document["domains"].items():
        if count > 0:
            print(f"  {domain}: {count}")
    
    # Save to research directory
    output_file = RESEARCH_DIR / "erdos_problems_comprehensive_v1.json"
    with open(output_file, 'w') as f:
        json.dump(document, f, indent=2)
    
    print(f"\n✓ Erdős problems saved to: {output_file}")
    
    # Update research ingestion index
    index_file = RESEARCH_DIR / "research_ingestion_index.json"
    
    if index_file.exists():
        with open(index_file, 'r') as f:
            index = json.load(f)
    else:
        index = []
    
    # Add new entry
    new_entry = {
        "id": "erdos-problems-comprehensive-v1",
        "title": "Comprehensive Erdős Problems Collection",
        "date": datetime.now().isoformat(),
        "source": "Wikipedia and other sources",
        "ingested_at": datetime.now().timestamp(),
        "tags": ["erdos", "conjectures", "problems", "graph-theory", "number-theory", "combinatorics"]
    }
    
    index.append(new_entry)
    
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"✓ Research ingestion index updated")
    
    return document


if __name__ == "__main__":
    main()
