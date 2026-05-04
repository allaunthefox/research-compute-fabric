# Research-Stack (OTOM)
**Ultra-low power, zero-decimal data routing and compression.**

If you just stumbled across this repository, you might see words like "Topological State Machine" and "Manifold Points" and assume this is dense, academic magic. **It isn't.**

This project is actually built on a very simple, grounded idea: **Modern computing is incredibly wasteful.** 

Right now, running AI or compressing massive datasets requires giant, power-hungry GPUs because they rely on *Floating-Point Math* (heavy decimals like `3.14159...`). We prove that you don't need decimals. You can map complex data (like the grammar of the English language) into structural shapes, and navigate them using **only simple integers (whole numbers).**

Because we only use addition, subtraction, multiplication, and modulo, this system can run on a $15 blank-slate microchip (an FPGA) instead of a massive server farm.

## 🛠️ How we know it works (Zero Guesswork)
We do not guess that our integer math works. We prove it.
The core of this project is written in **Lean 4**, a strict mathematical theorem prover. 
If our logic has a flaw, *the code physically will not compile.* We currently have over **3,500 mathematically verified proofs** securing this engine. 

Python, Rust, and Verilog only exist in this repository to act as "dumb pipes" to feed data into our proven mathematical core.

---

## 📁 Repository Structure (By Goal)

Everything is numbered so you know exactly what depends on what. 

| Folder | What it actually is (Plain English) |
| :--- | :--- |
| **`0-Core-Formalism/`** | **The Brain.** Lean 4 code. The mathematically proven integer arithmetic. This is the source of truth. |
| **`1-Distributed-Systems/`** | **The Network.** Code for making multiple computers talk to each other to share the workload. |
| **`2-Search-Space/`** | **The Navigator.** Algorithms that search through our data shapes to find the best routes. |
| **`3-Mathematical-Models/`** | **The Library.** Where we store our databases of equations and compressed English grammar shapes. |
| **`4-Infrastructure/`** | **The Drivers.** Code that physically talks to the hardware, GPUs, and APIs. |
| **`5-Applications/`** | **The Executables.** Python scripts that run the system end-to-end. (These are just shims connecting data to our Lean 4 Brain). |
| **`6-Documentation/`** | **The Manual.** Where you'll find plain-English explanations and our theoretical papers. |
| **`shared-data/`** | Raw data, cache, and exported files. |

---

## 📖 Where to start?
If you are new here, read these two files first:
1. **[Explanation for Humans](6-Documentation/EXPLANATION_FOR_HUMANS.md)** - A translation guide for our technical jargon.
2. **[Calculator-Plain Math](6-Documentation/calculator_plain_math.md)** - Proof that every complex concept we use can be calculated on a high-school graphing calculator.

## 🚀 Quick Start
```bash
# 1. Compile the mathematically proven core (Takes ~1-2 minutes)
cd "0-Core-Formalism/lean/Semantics"
lake build

# 2. Run the English Manifold Builder (Compresses English via grammar shapes)
cd "../../.."
python3 5-Applications/scripts/redpajama_english_manifold.py
```

## ⚖️ The One Rule for Contributors
**Lean is the source of truth.** 
If you add logic, it goes in `0-Core-Formalism/lean/Semantics/` and must be mathematically proven. Python scripts may not contain complex math, branching logic, or cost functions. Python is just the delivery boy for Lean.

---
*Research Stack — All Rights Reserved*
