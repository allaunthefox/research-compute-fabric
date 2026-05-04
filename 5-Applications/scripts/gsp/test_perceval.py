import perceval as pcvl

M = 6
circuit = pcvl.Circuit(M)
for i in range(3):
    circuit.add(i, pcvl.PS(0.1))
for i in range(M - 1):
    circuit.add((i, i+1), pcvl.BS())

input_state = pcvl.BasicState([1, 1, 1, 0, 0, 0])
processor = pcvl.Processor("SLOS", circuit)
processor.with_input(input_state)

sampler = pcvl.algorithm.Sampler(processor)
samples = sampler.sample_count(10)
print(samples["results"])
