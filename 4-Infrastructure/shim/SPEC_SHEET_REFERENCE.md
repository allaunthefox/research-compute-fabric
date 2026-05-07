# Component Spec Sheet Reference

**Generated:** 2026-05-06T23:04:52.050840

## Components

### U1_FPGA: GW1NR-LV9QN88PC6/I5

- **Manufacturer:** Gowin Semiconductor
- **Category:** FPGA
- **Datasheet:** https://www.gowinsemi.com/en/support/datasheet/

**Key Parameters:**

- LUTs: 8640
- FFs: 6480
- BRAM: 468Kb (26 × 18Kb blocks)
- DSP: 20 multipliers (16×16)
- PLLs: 2
- IO: 68 user I/O
- Package: QFN88 (10×10mm)
- Core voltage: 1.2V
- IO voltage: 3.3V / 2.5V / 1.8V
- Max frequency: ~200MHz (fabric), 400MHz (PLL out)
- Flash: Embedded 64Mbit SPI
- Programming: JTAG + SPI + UART

**Topological Relevance:**

- 8640 LUTs → partition into 11 agent compute units (785 LUTs each)
- 20 DSP blocks → 20 parallel Q16.16 multiply-accumulate pipelines
- 468Kb BRAM → 256 FAMM cells × 64-bit = 16Kb (fits in 1 BRAM block)
- 2 PLLs → eigenvalue-derived clock distribution (τ ∝ 1/√λ)
- 68 I/O → 8 HDMI + 32 DDR + 8 UART + 20 GPIO for topology sensing

---

### U2_DDR: MT41K128M16JT-125 (typical)

- **Manufacturer:** Micron
- **Category:** Memory
- **Datasheet:** https://www.micron.com/products/dram/ddr3-sdram

**Key Parameters:**

- Density: 2Gb (128M×16)
- Speed: DDR3-1600 (800MHz clock)
- Data rate: 1600 MT/s
- Burst length: 8
- CAS latency: CL=11
- tRCD: 13.75ns
- tRP: 13.75ns
- tRC: 48.75ns
- Voltage: 1.5V (1.35V DDR3L)
- Package: 96-ball FBGA
- Row/Column: 14/10 addressing

**Topological Relevance:**

- 800MHz clock → 1250ps period → trace matching within 50ps = 4% tolerance
- CL=11 → 13.75ns read latency → pipeline 11 stages in FPGA
- Burst=8 → 8×16-bit = 128-bit FAMM data bus width
- 1.5V → separate power plane with <5mΩ target impedance
- tRC=48.75ns → 20.5M random accesses/sec → FAMM preshaping critical

---

### U3_OSC: SG-210STF 100.0000ML3 (typical)

- **Manufacturer:** Epson
- **Category:** Clock
- **Datasheet:** https://www5.epsondevice.com/en/products/crystal_oscillator/

**Key Parameters:**

- Frequency: 100.000 MHz
- Stability: ±50ppm
- Jitter: <1ps RMS (12kHz-20MHz)
- Rise/fall: <3ns
- Output: LVCMOS
- Voltage: 3.3V
- Package: 2.5×2.0mm ceramic
- Phase noise: -135dBc/Hz @ 10kHz offset

**Topological Relevance:**

- 100MHz → 10ns period → eigenvalue clock: λ_1→75ns, λ_16→45ns
- ±50ppm → 5ns drift over 100k cycles → PLL lock required
- <1ps jitter → suitable for Q16.16 timing precision (15ps LSB)
- Phase noise -135dBc → clean enough for manifold clock distribution

---

### U4_REG: AMS1117-3.3 (typical)

- **Manufacturer:** Advanced Monolithic Systems
- **Category:** Power
- **Datasheet:** https://www.advanced-monolithic.com/pdf/ds1117.pdf

**Key Parameters:**

- Output: 3.3V ±1.5%
- Dropout: 1.1V @ 1A
- Max current: 1A
- Line regulation: 0.2% max
- Load regulation: 0.4% max
- Ripple rejection: 60dB @ 120Hz
- Thermal shutdown: 165°C
- Package: SOT-223

**Topological Relevance:**

- 1A max → 3.3W total → thermal topology: place near board edge
- 60dB ripple rejection → 1000× noise reduction → clean analog rails
- 165°C shutdown → thermal vias needed under package
- 1.1V dropout → input must be >4.4V → 5V USB sufficient

---

### J1_HDMI: HDMI-A-19P-SMT (typical)

- **Manufacturer:** Various (Molex, TE, Amphenol)
- **Category:** Connector
- **Datasheet:** https://www.hdmi.org/spec/index

**Key Parameters:**

- Pins: 19
- TMDS pairs: 4 (3 data + 1 clock)
- Impedance: 100Ω differential
- Data rate: Up to 3.4Gbps per lane (HDMI 1.4)
- Bandwidth: 10.2 Gbps total
- DDC: I²C @ 100kHz
- HPD: Hot plug detect (5V tolerant)
- CEC: Consumer Electronics Control
- Voltage: 5V @ 50mA (pin 18)

**Topological Relevance:**

- 100Ω differential → trace impedance must match within ±10%
- 3.4Gbps → 294ps bit period → 15ps trace matching (5%)
- 4 TMDS pairs → 4 parallel FAMM delay lines for video stream
- DDC I²C → topology-aware EDID emulation for manifold display
- HPD → topological hot-plug detection for swarm reconfiguration

---

### C1_C2_C4_100nF: GRM188R71H104KA93 (typical)

- **Manufacturer:** Murata
- **Category:** Passive
- **Datasheet:** https://www.murata.com/en-us/products/capacitor/ceramiccapacitor

**Key Parameters:**

- Capacitance: 100nF ±10%
- Dielectric: X7R
- Voltage: 50V
- ESR: <50mΩ @ 100MHz
- ESL: ~0.5nH (0603)
- SRF: ~22MHz
- Package: 0603 (1.6×0.8mm)
- Temp range: -55°C to +125°C

**Topological Relevance:**

- SRF 22MHz → effective decoupling to ~50MHz → covers FPGA core
- ESL 0.5nH → via inductance dominates → minimize via length
- X7R → ±15% over temp → account for in PDN impedance budget

---

### C3_10uF: GRM21BR61A106KE19 (typical)

- **Manufacturer:** Murata
- **Category:** Passive
- **Datasheet:** https://www.murata.com/en-us/products/capacitor/ceramiccapacitor

**Key Parameters:**

- Capacitance: 10µF ±10%
- Dielectric: X5R
- Voltage: 10V
- ESR: <10mΩ @ 1MHz
- ESL: ~0.8nH (0805)
- SRF: ~1.8MHz
- Package: 0805 (2.0×1.25mm)
- DC bias derating: -70% at 3.3V (effective ~3µF)

**Topological Relevance:**

- DC bias derating critical → effective 3µF not 10µF at 3.3V
- SRF 1.8MHz → bulk decoupling below 10MHz → complements 100nF
- ESR 10mΩ → low enough for PDN target <10mΩ with parallel caps

---

### C5_4u7: GRM21BR61C475KA88 (typical)

- **Manufacturer:** Murata
- **Category:** Passive
- **Datasheet:** https://www.murata.com/en-us/products/capacitor/ceramiccapacitor

**Key Parameters:**

- Capacitance: 4.7µF ±10%
- Dielectric: X5R
- Voltage: 16V
- ESR: <20mΩ @ 1MHz
- ESL: ~0.8nH (0805)
- SRF: ~2.6MHz
- Package: 0805

**Topological Relevance:**

- LDO output cap → stability requirement: 4.7µF min for AMS1117
- ESR 20mΩ → within LDO stable region (0.1-10Ω for most LDOs)

---

### PCB_TRACE: Standard 1oz Cu, 0.15mm width

- **Manufacturer:** Generic
- **Category:** PCB
- **Datasheet:** N/A — standard IPC-2221

**Key Parameters:**

- Dielectric: FR-4 (εr=4.5 @ 1GHz)
- Copper: 1oz (35µm)
- Trace width: 0.15mm (6 mil)
- Impedance: ~50Ω (microstrip, layer 1)
- Delay: ~150ps/inch (6ps/mm)
- Capacitance: ~1.1pF/cm
- Inductance: ~3nH/cm
- DC resistance: ~0.3Ω/cm (0.15mm, 1oz)
- Min spacing: 0.15mm (6 mil)

**Topological Relevance:**

- 6ps/mm delay → 25mm trace = 150ps → matches DDR skew budget
- εr=4.5 → impedance varies ±10% with manufacturing → calibrate per board
- 0.3Ω/cm → 60mm power trace = 1.8Ω → unacceptable for PDN → use planes
- FR-4 loss: ~0.02dB/mm @ 1GHz → 50mm = 1dB → negligible for <500MHz

---

### VIA: Standard IPC-2221 Type III

- **Manufacturer:** Generic
- **Category:** PCB
- **Datasheet:** N/A — standard IPC-2221

**Key Parameters:**

- Drill: 0.3mm
- Pad: 0.6mm
- Antipad: 0.8mm
- Inductance: ~0.8nH (1.6mm board)
- Capacitance: ~0.5pF
- Impedance: ~40Ω
- Stub resonance: λ/4 @ ~25GHz for 1.6mm stub
- Current capacity: ~1A (0.3mm, 1oz plating)

**Topological Relevance:**

- 0.8nH per via → 4 vias in PDN path = 3.2nH → limits decoupling above 100MHz
- Stub at 1.6mm → resonance at 25GHz → safe below 5GHz → backdrill for HDMI
- 0.5pF per via → negligible for <1GHz signals

---

