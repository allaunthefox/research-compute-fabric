import perceval as pcvl

token = ""
with open("/home/allaun/Documents/Research Stack/.env", "r") as f:
    for line in f:
        if line.startswith("QUANDELA_API_KEY"):
            token = line.split("=")[1].strip()

rp = pcvl.RemoteProcessor("sim:ascella", token)
circuit = pcvl.Circuit(12)
circuit.add((0, 1), pcvl.BS())
rp.set_circuit(circuit)
input_state = pcvl.BasicState([1, 1, 1] + [0]*9)
rp.with_input(input_state)
rp.min_detected_photons_filter(3)

sampler = pcvl.algorithm.Sampler(rp, max_shots_per_call=10)
res = sampler.sample_count(10)
print(res)
