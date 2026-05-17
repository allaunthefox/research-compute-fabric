# Signal Equation Invariant Roots

These are invariant roots for accessible local signal equations. They are route/control priors and hardware design handles, not external physics proof or compression proof without exact byte receipts.

Root count: 33
Receipt hash: `10ec6bf94808b4517c6e866889d8c9cca02969fbcb43c574b0abd27c3cac3a33`

## Unifying Root

```text
SignalRoute = (coordinate, invariant_root, admissible_transform, receipt_barrier)
```

Every accessible signal equation reduces to a coordinate map plus an invariant root. The invariant root says what can survive rescaling, basis changes, phase shifts, lane permutation, or compression-route projection. Promotion still requires a receipt barrier.

## Roots

### SIGROOT001_spectral_overlap

- Equation: `<s1,s2> = sum_i s1_i s2_i`
- Invariant root: inner-product pairing on aligned spectral coordinates
- Admissible transforms: common bin permutation; orthonormal basis change when both signatures transform together
- Compression use: route similarity, duplicate-island pruning, nearest repair template
- FPGA use: DSP dot-product lane with accumulator and saturation guard

### SIGROOT002_piecewise_merge

- Equation: `merge_i = min(1, left_i + right_i)`
- Invariant root: bounded semilattice occupancy over [0,1]^n
- Admissible transforms: coordinatewise monotone maps that preserve zero, one, and order
- Compression use: safe feature union without unbounded sidecar growth
- FPGA use: saturating add primitive

### SIGROOT003_resonance_degeneracy

- Equation: `deg(left,right) = |support(left) intersect support(right)|`
- Invariant root: support-intersection cardinality
- Admissible transforms: positive amplitude scaling and common support-preserving permutation
- Compression use: overlap score for tokenbook/feature collisions
- FPGA use: bitmask AND plus popcount

### SIGROOT004_wavefront_value

- Equation: `value = (A - gamma*d) * osc(omega*d) for d <= v*t, else 0`
- Invariant root: retarded wavefront cone plus phase class modulo cycle
- Admissible transforms: translations and metric-preserving coordinate changes
- Compression use: event influence radius for local route activation
- FPGA use: distance gate, phase LUT, envelope subtractor

### SIGROOT005_signal_band_policy

- Equation: `band(x) = threshold_partition(x)`
- Invariant root: ordered threshold cell
- Admissible transforms: monotone rescaling with transformed thresholds
- Compression use: route budget scheduler
- FPGA use: comparator ladder

### SIGROOT006_acoustic_gradient

- Equation: `Z_acoustic ~ |grad f|`
- Invariant root: metric norm of field gradient
- Admissible transforms: coordinate changes with explicit metric tensor
- Compression use: manifold steepest-descent route proposal
- FPGA use: finite-difference gradient and norm pipeline

### SIGROOT007_fitness_entropy_compensation

- Equation: `f + alpha*H = f_max`
- Invariant root: affine fitness-entropy conserved total
- Admissible transforms: unit changes that transform alpha coherently
- Compression use: semantic/fitness score must pay entropy cost
- FPGA use: linear score lane with conserved budget comparator

### SIGROOT008_gibbs_free_energy

- Equation: `G = H - T*S`
- Invariant root: Legendre-transformed available-energy potential
- Admissible transforms: thermodynamic coordinate changes preserving conjugate pair T,S
- Compression use: available byte-gain after entropy/side-info cost
- FPGA use: cost potential lane for thermal/energy-aware routing

### SIGROOT009_affine_erasure_permutation

- Equation: `pi(i) = a + s*i mod n`
- Invariant root: cycle structure determined by gcd(s,n)
- Admissible transforms: offset translation and invertible modular scaling
- Compression use: repair stream interleaving with deterministic owner
- FPGA use: modular address generator

### SIGROOT010_genomic_weight

- Equation: `W = (rho + v + tau + sigma + q) / ((1+kappa^2)*(1+epsilon))`
- Invariant root: dimensionless normalized field-strength ratio
- Admissible transforms: common scale-normalization of numerator terms
- Compression use: adaptive erasure threshold
- FPGA use: fixed-point ratio approximation

### SIGROOT011_pbacs_phi_accumulator

- Equation: `phi_{t+1} = phi_t + c mod 2^32`
- Invariant root: circle rotation orbit class
- Admissible transforms: phase offset; modular conjugacy preserving increment
- Compression use: deterministic phase owner for route symbols
- FPGA use: free-running modular accumulator

### SIGROOT012_pbacs_error_feedback

- Equation: `e_next = v + e - b*theta`
- Invariant root: bounded quantization residual
- Admissible transforms: threshold-preserving fixed-point rescale
- Compression use: exact residual lane for symbol decisions
- FPGA use: sigma-delta style feedback cell

### SIGROOT013_mutual_information_gain

- Equation: `MI = baseline_bpb - actual_bpb`
- Invariant root: byte-per-symbol improvement under one ratio schema
- Admissible transforms: comparisons that keep baseline and actual schema identical
- Compression use: route evidence coordinate
- FPGA use: counter difference after codec run

### SIGROOT014_weighted_mi_prediction

- Equation: `MI_pred = sum_i w_i MI_i S_i / sum_i w_i S_i`
- Invariant root: barycentric coordinate in similarity-weighted evidence simplex
- Admissible transforms: common positive scaling of all weights
- Compression use: nearest-prior route prediction
- FPGA use: weighted accumulator plus reciprocal approximation

### SIGROOT015_surprise_metric

- Equation: `S = log(1 + |delta_MI|)`
- Invariant root: monotone function of absolute prediction residual
- Admissible transforms: monotone reparameterization of residual magnitude
- Compression use: route anomaly detector
- FPGA use: absolute-delta threshold; log optional

### SIGROOT016_structure_yield

- Equation: `rho = MI / (cost + eps)`
- Invariant root: information-per-cost efficiency ratio
- Admissible transforms: unit changes preserving numerator/denominator interpretation
- Compression use: candidate route priority
- FPGA use: score-per-cycle allocator

### SIGROOT017_weighted_feature_distance

- Equation: `d(z1,z2) = sqrt(sum_i w_i*((z1_i-z2_i)/s_i)^2)`
- Invariant root: diagonal metric distance after scale normalization
- Admissible transforms: coordinate rescaling absorbed into s_i and w_i
- Compression use: route family clustering
- FPGA use: scaled L2 distance pipeline

### SIGROOT018_energy_gradient_waveform

- Equation: `wave_E = (|grad E|, omega_gradE, phi_gradE)`
- Invariant root: gradient magnitude and phase trajectory
- Admissible transforms: metric-aware coordinate changes
- Compression use: energy/cost-aware transform scheduling
- FPGA use: gradient magnitude plus phase accumulator

### SIGROOT019_shape_energy_coupling

- Equation: `C_SE = alpha <grad h, grad E>`
- Invariant root: metric inner product of shape and energy gradients
- Admissible transforms: coordinate changes preserving the metric pairing
- Compression use: align geometry witness only when it reduces route cost
- FPGA use: dual-gradient dot-product lane

### SIGROOT020_spectral_field_score

- Equation: `score = mM + pP + <s,F>`
- Invariant root: bilinear pairing between local state and field
- Admissible transforms: paired basis changes that preserve the bilinear form
- Compression use: local route-field compatibility score
- FPGA use: three-term MAC lane

### SIGROOT021_parabolic_j_score

- Equation: `J(k) = 32 - 0.5*(k-22)^2`
- Invariant root: distance from resonant vertex k=22
- Admissible transforms: translation to vertex coordinate u=k-22
- Compression use: resonance-ranked candidate pruning
- FPGA use: subtract-square-threshold circuit

### SIGROOT022_cmyk_frequency_lattice

- Equation: `f_ch(h) = base_ch + delta*h`
- Invariant root: channel-local affine frequency lattice coordinate h
- Admissible transforms: affine frequency calibration preserving delta steps
- Compression use: symbol carrier with exact inverse
- FPGA use: base-plus-shift frequency synthesizer

### SIGROOT023_rydberg_gap

- Equation: `nu_bar = R*(1/n1^2 - 1/n2^2)`
- Invariant root: reciprocal-square quantum gap
- Admissible transforms: unit conversion between wavenumber, wavelength, frequency, and energy
- Compression use: stable physical spectral basis index
- FPGA use: small table of canonical spectral lines

### SIGROOT024_lorentzian_resonance

- Equation: `L(delta) = 1/(1+delta^2)`
- Invariant root: squared detuning from spectral center
- Admissible transforms: sign flip of detuning; normalized wavelength units
- Compression use: nearest spectral-basis assignment
- FPGA use: detuning-square LUT

### SIGROOT025_kmer_base4_index

- Equation: `idx = 16*b1 + 4*b2 + b3`
- Invariant root: base-4 coordinate of codon symbol
- Admissible transforms: base relabeling with explicit inverse map
- Compression use: fixed codon/tokenbook coordinate
- FPGA use: two-bit shift-and-or indexer

### SIGROOT026_dct2_basis

- Equation: `basis_{j,k} = cos(pi/n*(j+1/2)*k)`
- Invariant root: orthogonal cosine projection coefficient
- Admissible transforms: orthogonal transforms preserving coefficient energy
- Compression use: spectral coefficient compaction
- FPGA use: fixed cosine basis or LUT butterfly

### SIGROOT027_qpsk_phase_class

- Equation: `phase in Z_4`
- Invariant root: phase class modulo pi/2
- Admissible transforms: global phase rotation with receiver correction
- Compression use: 2-bit symbol carrier
- FPGA use: quadrant decoder

### SIGROOT028_qam16_constellation

- Equation: `symbol = (a in A4, phase in Z4)`
- Invariant root: finite amplitude-phase lattice point
- Admissible transforms: affine constellation calibration with preserved decision cells
- Compression use: 4-bit symbol carrier / QAM transfer metaphor
- FPGA use: amplitude slicer plus quadrant decoder

### SIGROOT029_dmt_subcarrier_quotient

- Equation: `phase_base = phase_out - offset_i mod cycle`
- Invariant root: phase quotient after subtracting subcarrier offset
- Admissible transforms: subcarrier permutation with receipted offset table
- Compression use: parallel lane carrier with exact demodulation
- FPGA use: per-lane phase subtractor

### SIGROOT030_hann_window_fft_energy

- Equation: `E_bin = avg_{k in bin} |FFT(window*x)_k|`
- Invariant root: windowed spectral-energy distribution
- Admissible transforms: time shift up to phase; amplitude normalization when max-normalized
- Compression use: audio/signal route feature vector
- FPGA use: window multiply, FFT, magnitude, bin accumulator

### SIGROOT031_transient_features

- Equation: `transient = (max dx+, max dx-, zero_crossings/n, peak/rms)`
- Invariant root: edge/impulse morphology of the signal chunk
- Admissible transforms: time-local scaling with normalized crest and ZCR preserved
- Compression use: decide raw vs spectral vs hybrid route
- FPGA use: delta extrema, sign-change counter, RMS/peak lane

### SIGROOT032_predictability_autocorrelation

- Equation: `pred = 0.5*(corr(x_t, x_{t-1}) + 1)`
- Invariant root: normalized temporal correlation
- Admissible transforms: affine amplitude scaling removed by mean/variance normalization
- Compression use: predictor suitability signal
- FPGA use: sliding dot product and norm lane

### SIGROOT033_cosine_similarity

- Equation: `cos(theta)=<a,b>/(||a|| ||b||)`
- Invariant root: projective direction on spectral feature sphere
- Admissible transforms: positive scaling of either vector
- Compression use: chunk reuse / skip decision
- FPGA use: dot product and reciprocal norm threshold
