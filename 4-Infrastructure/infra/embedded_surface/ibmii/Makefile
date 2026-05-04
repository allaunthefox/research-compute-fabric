.PHONY: run noisy burst clean

run:
	./ibmii_eth_controller.py --nodes 10 --emit-jsonl 1

noisy:
	./ibmii_eth_controller.py --nodes 10 --bad-fcs 0.15 --wrong-shell 0.10 --bad-lut 0.10 --quorum 5

burst:
	./ibmii_eth_controller.py --nodes 16 --burst 0.80 --quorum 4

# MNN test targets disabled - logic moved to Lean (Semantics.MorphicNeuralNetwork.lean)
# Per AGENTS.md Section 8, Python files that duplicate Lean modules are deleted.
# Use lake build to test the Lean implementation.

clean:
	rm -rf __pycache__
