.PHONY: demo jsonl mev-pressure sequence ms3c route known clean

demo:
	./dynamic_lut_slotter.py --demo

jsonl:
	./dynamic_lut_slotter.py --demo --jsonl

mev-pressure:
	./dynamic_lut_slotter.py --shell onion --workload crypto_mev_research --pressure 95

sequence:
	./sequence_surface_lut.py --surface hachimoji --sequence ACGTZPSBACGTZPSB --complement

ms3c:
	./matroska_s3c_reduction_gear.py 12345

route:
	./unified_compression_route.py "ACGTACGTACGTACGT"

known:
	./possibility_space_probe.py --known-only --top 24

clean:
	rm -rf __pycache__
