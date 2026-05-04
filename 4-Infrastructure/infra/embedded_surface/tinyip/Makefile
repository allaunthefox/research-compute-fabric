.PHONY: run stress clean

run:
	./tinyip_emulator.py --nodes 10 --loss 0.20 --duplicate 0.10 --reorder 0.10

stress:
	./tinyip_emulator.py --nodes 16 --loss 0.45 --duplicate 0.20 --reorder 0.25 --ticks 400 --quorum 12

clean:
	rm -rf build __pycache__
