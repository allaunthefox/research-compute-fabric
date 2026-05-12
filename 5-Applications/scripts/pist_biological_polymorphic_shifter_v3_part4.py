# ═══════════════════════════════════════════════════════════════════════════════
# PIST Biological Polymorphic Shifter v3.0 — PART 4
# ───────────────────────────────────────────────────────────────────────────────
# Shifters 25–27: miRNA, STDP, Spiegelmer
# Optimizer: BiologicalManifoldOptimizer (genetic search)
# Compressor: BiologicalPolymorphicCompressor (unified API)
# Demo: demonstrate() — test all data types and shifter chains
# ═══════════════════════════════════════════════════════════════════════════════

import hashlib
import math
import random
import struct
from collections import Counter, defaultdict
from copy import deepcopy
from heapq import heappush, heappop

from pist_biological_polymorphic_shifter_v3 import (
    Shifter, ManifoldState, NExponent, intrinsic_load,
    pist_encode, pist_decode, pist_mass, pist_mirror,
    pist_normalized_tension, pist_phase_str, PHI
)


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 25: miRNA (MicroRNA — post-transcriptional regulation)
# ───────────────────────────────────────────────────────────────────────────────
# miRNA silences genes by binding to complementary mRNA.
# Analogy: low-frequency bytes are "silenced" (removed or marked),
# while high-frequency bytes are "expressed" (retained).
# ═══════════════════════════════════════════════════════════════════════════════

class miRNA_Shifter(Shifter):
    name = "miRNA"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply miRNA-like regulation: silence low-frequency bytes.

        Bytes below a frequency threshold are "silenced" (replaced with
        a marker). The miRNA seed region is the frequency distribution.
        Only "expressed" bytes survive at full fidelity.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        freq = Counter(data)
        total = len(data)
        threshold = max(1, total // 16)  # silence bytes appearing < 6.25%

        result = bytearray()
        silent_map = bytearray()
        for b in data:
            if freq[b] >= threshold:
                result.append(b)  # expressed
            else:
                result.append(0xFB)  # silenced marker
                silent_map.append(b)  # store for recovery

        # Store silent bytes as compressed tail
        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['mirna_threshold'] = threshold
        new_state.metadata['mirna_silent'] = bytes(silent_map)
        new_state.metadata['mirna_freq'] = dict(freq.most_common(16))
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Restore silenced bytes from stored map."""
        data = state.encoded
        silent_bytes = state.metadata.get('mirna_silent', b'')

        result = bytearray()
        si = 0
        for b in data:
            if b == 0xFB and si < len(silent_bytes):
                result.append(silent_bytes[si])
                si += 1
            else:
                result.append(b)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 26: STDP (Spike-Timing-Dependent Plasticity)
# ───────────────────────────────────────────────────────────────────────────────
# STDP: if pre-synaptic spike precedes post-synaptic spike → strengthen.
# If pre follows post → weaken. Long-term potentiation/depression.
# Analogy: byte pairs that appear in a "causal" order (frequent adjacent pairs)
# get strengthened (merged). Rare transitions get weakened (split).
# ═══════════════════════════════════════════════════════════════════════════════

class STDPShifter(Shifter):
    name = "STDP"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply STDP-like learning to byte transitions.

        Frequent adjacent byte pairs = "strengthened" (merged into single byte).
        Rare transitions = "weakened" (marked for splitting).
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # Count adjacent byte pairs
        pairs = Counter()
        for i in range(len(data) - 1):
            pair = (data[i], data[i + 1])
            pairs[pair] += 1

        total_pairs = sum(pairs.values())
        if total_pairs == 0:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # Merge frequent pairs above threshold
        threshold = max(2, total_pairs // 64)
        merge_map = {}
        next_code = 128  # use upper half for merged codes

        for pair, count in pairs.most_common():
            if count < threshold or next_code >= 256:
                break
            merge_map[pair] = next_code
            next_code += 1

        # Apply STDP merging
        result = bytearray()
        i = 0
        while i < len(data):
            if i + 1 < len(data):
                pair = (data[i], data[i + 1])
                if pair in merge_map:
                    result.append(merge_map[pair])
                    i += 2
                    continue
            result.append(data[i])
            i += 1

        # Store inverse mapping
        inv_merge = {}
        for pair, code in merge_map.items():
            inv_merge[code] = pair

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['stdp_merge'] = inv_merge
        new_state.metadata['stdp_threshold'] = threshold
        new_state.metadata['stdp_merged_pairs'] = len(merge_map)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Expand STDP merged pairs back to original bytes."""
        data = state.encoded
        inv_merge = state.metadata.get('stdp_merge', {})

        result = bytearray()
        for b in data:
            if b in inv_merge:
                pair = inv_merge[b]
                result.append(pair[0])
                result.append(pair[1])
            else:
                result.append(b)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 27: SPIEGELMER (L-DNA mirror image)
# ───────────────────────────────────────────────────────────────────────────────
# Spiegelmers are L-DNA mirror images of natural D-DNA.
# They are completely nuclease-resistant because no natural enzyme
# can recognize the mirror-image backbone.
# Analogy: apply a byte-wise mirror transformation that is
# "invisible" to standard decoding algorithms.
# ═══════════════════════════════════════════════════════════════════════════════

class SpiegelmerShifter(Shifter):
    name = "Spiegelmer"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply Spiegelmer mirror transformation.

        Map each byte to its bit-reversed mirror (mirror image).
        L-DNA = D-DNA reflected in mirror.
        """
        data = state.encoded
        result = bytearray()
        for b in data:
            # Bit reversal
            rev = int(format(b, '08b')[::-1], 2)
            result.append(rev)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse Spiegelmer (bit reversal is self-inverse)."""
        # Same as encode (bit reversal is an involution)
        return cls.encode(state)


# ═══════════════════════════════════════════════════════════════════════════════
# BIOLOGICAL MANIFOLD OPTIMIZER
# ───────────────────────────────────────────────────────────────────────────────
# Genetic algorithm that searches the space of ALL possible shifter chains
# to find the optimal combination for a given input.
#
# ANY combination with ANY combination is allowed.
# The optimizer uses:
#   - Beam search: keep top-K chains at each step
#   - Fitness: compression_ratio × computational_efficiency × stability
#   - Crossover: combine best chains
#   - Mutation: add/remove/reorder shifters
# ═══════════════════════════════════════════════════════════════════════════════

class BiologicalManifoldOptimizer:
    """Searches for optimal shifter chains using beam search + evolution."""

    # All available shifters for the optimizer
    ALL_SHIFTERS = [
        # Synthetic DNA
        'Hachimoji', 'AEGIS', 'NaturalDNA',
        # RNA Processing
        'Transcription', 'Translation', 'Splicing', 'miRNA',
        # Backbone XNAs
        'PNA', 'LNA', 'Morpholino', 'Spiegelmer',
        # Prion/Epigenetic
        'Prion',
        # Neuronal
        'SpikeTiming', 'STDP',
        # Mycelial
        'HyphalNet',
        # Chaotic/Galois
        'LogisticMap', 'GaloisRing', 'SBox', 'CellularAutomata',
        # PIST Geometry
        'PIST', 'PISTMirror', 'PISTResonance',
        # Arithmetic
        'DeltaGCL', 'RunLength', 'Huffman',
        # Stochastic Engine
        'DeterministicStochastic',
        # Cellular Automata variants
        'Wireworld',
    ]

    SHIFTER_CLASSES = {
        'Hachimoji': 'HachimojiShifter',
        'AEGIS': 'AEGISShifter',
        'NaturalDNA': 'NaturalDNAShifter',
        'Transcription': 'TranscriptionShifter',
        'Translation': 'TranslationShifter',
        'Splicing': 'SplicingShifter',
        'miRNA': 'miRNA_Shifter',
        'PNA': 'PNAShifter',
        'LNA': 'LNAShifter',
        'Morpholino': 'MorpholinoShifter',
        'Spiegelmer': 'SpiegelmerShifter',
        'Prion': 'PrionShifter',
        'SpikeTiming': 'SpikeTimingShifter',
        'STDP': 'STDPShifter',
        'HyphalNet': 'HyphalNetShifter',
        'LogisticMap': 'LogisticMapShifter',
        'GaloisRing': 'GaloisRingShifter',
        'SBox': 'SBoxShifter',
        'CellularAutomata': 'CellularAutomataShifter',
        'Wireworld': 'WireworldShifter',
        'PIST': 'PISTShifter',
        'PISTMirror': 'PISTMirrorShifter',
        'PISTResonance': 'PISTResonanceShifter',
        'DeltaGCL': 'DeltaGCLShifter',
        'RunLength': 'RunLengthShifter',
        'Huffman': 'HuffmanShifter',
        'DeterministicStochastic': 'DeterministicStochasticEngine',
    }

    def __init__(self, max_chain_length: int = 6, beam_width: int = 8):
        self.max_chain_length = max_chain_length
        self.beam_width = beam_width
        self._imported = False

    def _import_shifters(self):
        """Lazy import of all shifter classes."""
        if self._imported:
            return

        from pist_biological_polymorphic_shifter_v3 import (
                HachimojiShifter, AEGISShifter, NaturalDNAShifter,
                TranscriptionShifter, TranslationShifter, SplicingShifter,
                PNAShifter, LNAShifter, PrionShifter)
        from pist_biological_polymorphic_shifter_v3_part2 import (
                SpikeTimingShifter, HyphalNetShifter, LogisticMapShifter,
                GaloisRingShifter, SBoxShifter, WireworldShifter,
                MorpholinoShifter, PISTShifter, PISTMirrorShifter,
                PISTResonanceShifter, DeltaGCLShifter, RunLengthShifter,
                HuffmanShifter, DeterministicStochasticEngine, CellularAutomataShifter)
        from pist_biological_polymorphic_shifter_v3_part4 import (
                miRNA_Shifter, STDPShifter, SpiegelmerShifter)

        self._class_map = {
            'Hachimoji': HachimojiShifter,
            'AEGIS': AEGISShifter,
            'NaturalDNA': NaturalDNAShifter,
            'Transcription': TranscriptionShifter,
            'Translation': TranslationShifter,
            'Splicing': SplicingShifter,
            'miRNA': miRNA_Shifter,
            'PNA': PNAShifter,
            'LNA': LNAShifter,
            'Morpholino': MorpholinoShifter,
            'Spiegelmer': SpiegelmerShifter,
            'Prion': PrionShifter,
            'SpikeTiming': SpikeTimingShifter,
            'STDP': STDPShifter,
            'HyphalNet': HyphalNetShifter,
            'LogisticMap': LogisticMapShifter,
            'GaloisRing': GaloisRingShifter,
            'SBox': SBoxShifter,
            'CellularAutomata': CellularAutomataShifter,
            'Wireworld': WireworldShifter,
            'PIST': PISTShifter,
            'PISTMirror': PISTMirrorShifter,
            'PISTResonance': PISTResonanceShifter,
            'DeltaGCL': DeltaGCLShifter,
            'RunLength': RunLengthShifter,
            'Huffman': HuffmanShifter,
            'DeterministicStochastic': DeterministicStochasticEngine,
        }
        self._imported = True

    def _get_shifter_class(self, name: str):
        """Get shifter class by name."""
        self._import_shifters()
        return self._class_map.get(name)

    def _evaluate_chain(self, data: bytes, chain: list) -> dict:
        """Evaluate a shifter chain on data. Returns fitness and encoded state."""
        state = ManifoldState(data)

        for shifter_name in chain:
            shifter_cls = self._get_shifter_class(shifter_name)
            if shifter_cls is None:
                continue
            try:
                state = shifter_cls.encode(state)
            except Exception as e:
                # Shifter failed — return zero fitness
                return {
                    'fitness': 0.0,
                    'ratio': 0.0,
                    'entropy': 99.0,
                    'state': state,
                    'chain': chain,
                }

        fitness = state.compute_fitness()
        ratio = len(data) / max(1, len(state.encoded))
        return {
            'fitness': fitness,
            'ratio': ratio,
            'entropy': state.entropy,
            'state': state,
            'chain': chain,
        }

    def optimize(self, data: bytes, max_steps: int = 20) -> dict:
        """Beam search for optimal shifter chain.

        Returns best chain and its evaluation.
        """
        if not data:
            return {'chain': [], 'fitness': 0.0, 'ratio': 1.0}

        # Initialize with single-shifter chains
        candidates = []
        for name in self.ALL_SHIFTERS:
            result = self._evaluate_chain(data, [name])
            heappush(candidates, (-result['fitness'], result))

        # Best overall
        _, best = candidates[0]

        # Expand
        for step in range(max_steps):
            new_candidates = list(candidates)

            # Expand top-K candidates
            top_k = []
            for _ in range(min(self.beam_width, len(candidates))):
                _, result = heappop(candidates)
                top_k.append(result)

            for result in top_k:
                current_chain = result['chain']
                current_state = result['state']

                if len(current_chain) >= self.max_chain_length:
                    continue

                # Try adding each shifter
                for name in self.ALL_SHIFTERS:
                    if name in current_chain:
                        continue  # avoid immediate repeat

                    new_chain = current_chain + [name]
                    new_result = self._evaluate_chain(data, new_chain)
                    heappush(new_candidates, (-new_result['fitness'], new_result))

            # Prune to beam_width
            candidates = []
            for _ in range(min(self.beam_width * 4, len(new_candidates))):
                candidates.append(heappop(new_candidates))

            # Check best
            neg_fit, best_candidate = candidates[0]
            if best_candidate['fitness'] > best['fitness']:
                best = best_candidate

            # Early stop if no improvement
            if step > 2 and best['fitness'] == candidates[0][1]['fitness']:
                break

        return best


# ═══════════════════════════════════════════════════════════════════════════════
# BIOLOGICAL POLYMORPHIC COMPRESSOR
# ───────────────────────────────────────────────────────────────────────────────
# Unified API for the polymorphic shifter system.
# Handles: auto-optimize, encode, decode, verify.
# ═══════════════════════════════════════════════════════════════════════════════

class BiologicalPolymorphicCompressor:
    """Main compression interface. Uses manifold of shifters."""

    def __init__(self, max_chain_length: int = 5, beam_width: int = 6):
        self.max_chain_length = max_chain_length
        self.beam_width = beam_width
        self.optimizer = BiologicalManifoldOptimizer(
            max_chain_length=max_chain_length,
            beam_width=beam_width
        )
        self._current_best = None

    def auto_optimize(self, data: bytes, max_steps: int = 15) -> dict:
        """Automatically find best shifter chain for this data."""
        result = self.optimizer.optimize(data, max_steps=max_steps)
        self._current_best = result
        return result

    def compress(self, data: bytes, chain: list = None) -> bytes:
        """Compress data using given chain (or auto-optimized best).

        Returns:
            bytes: header + encoded data
        """
        if chain is None:
            if self._current_best is None:
                self.auto_optimize(data)
            chain = self._current_best['chain']
            state = self._current_best['state']
        else:
            state = ManifoldState(data)
            for shifter_name in chain:
                shifter_cls = self.optimizer._get_shifter_class(shifter_name)
                if shifter_cls:
                    state = shifter_cls.encode(state)

        # Build compressed output with header
        header = bytearray()
        header.append(len(chain))  # chain length
        for name in chain:
            name_bytes = name.encode('ascii')[:20]
            header.append(len(name_bytes))
            header.extend(name_bytes)

        # Separator
        header.append(0x00)

        compressed = bytes(header) + state.encoded

        self._current_best = {
            'chain': chain,
            'state': state,
            'ratio': len(data) / max(1, len(compressed)),
            'fitness': state.compute_fitness(),
        }

        return compressed

    def decompress(self, compressed: bytes) -> bytes:
        """Decompress by parsing header and reversing shifter chain.

        Returns:
            bytes: original decompressed data
        """
        if not compressed:
            return b''

        # Parse header
        ptr = 0
        chain_len = compressed[ptr]; ptr += 1

        chain = []
        for _ in range(chain_len):
            if ptr >= len(compressed):
                break
            name_len = compressed[ptr]; ptr += 1
            if ptr + name_len > len(compressed):
                break
            name = compressed[ptr:ptr+name_len].decode('ascii', errors='replace')
            ptr += name_len
            chain.append(name)

        # Skip separator
        if ptr < len(compressed) and compressed[ptr] == 0x00:
            ptr += 1

        encoded_data = compressed[ptr:]

        # Decode in reverse
        state = ManifoldState(encoded_data)
        state.encoded = encoded_data

        for shifter_name in reversed(chain):
            shifter_cls = self.optimizer._get_shifter_class(shifter_name)
            if shifter_cls:
                try:
                    state = shifter_cls.decode(state)
                except Exception as e:
                    print(f"  [WARN] Decode failed for {shifter_name}: {e}")
                    break

        return state.encoded

    def verify(self, data: bytes, chain: list = None) -> dict:
        """Compress then decompress, check lossless."""
        compressed = self.compress(data, chain)
        decompressed = self.decompress(compressed)

        lossless = data == decompressed
        ratio = len(data) / max(1, len(compressed))
        entropy = intrinsic_load(compressed)

        if self._current_best:
            fitness = self._current_best.get('fitness', 0.0)
        else:
            fitness = 0.0

        return {
            'lossless': lossless,
            'ratio': ratio,
            'entropy': entropy,
            'fitness': fitness,
            'original_size': len(data),
            'compressed_size': len(compressed),
            'chain': chain or (self._current_best.get('chain', []) if self._current_best else []),
        }

    def analyze(self, data: bytes) -> dict:
        """Analyze data properties for shifter selection."""
        if not data:
            return {}

        freq = Counter(data)
        entropy = intrinsic_load(data)

        # PIST profile
        shells = Counter()
        tensions = []
        masses = []
        for b in data:
            k, t = pist_encode(b)
            shells[k] += 1
            tensions.append(pist_normalized_tension(k, t))
            masses.append(pist_mass(k, t))

        avg_tension = sum(tensions) / len(tensions) if tensions else 0
        avg_mass = sum(masses) / len(masses) if masses else 0
        grounded = sum(1 for m in masses if m == 0)
        seismic = len(masses) - grounded

        # Frequency analysis
        top_bytes = [b for b, _ in freq.most_common(8)]
        unique_count = len(freq)

        return {
            'entropy': entropy,
            'size': len(data),
            'unique_bytes': unique_count,
            'avg_tension': avg_tension,
            'avg_mass': avg_mass,
            'grounded_pct': (grounded / max(1, len(data))) * 100,
            'seismic_pct': (seismic / max(1, len(data))) * 100,
            'top_bytes': top_bytes,
            'recommended_chain': self._recommend_chain(entropy, avg_tension, unique_count),
        }

    def _recommend_chain(self, entropy: float, tension: float, unique: int) -> list:
        """Heuristic chain recommendation based on data profile."""
        chain = []

        if entropy < 3.0:
            # Low entropy = repetitive → RLE + Delta + Mirror
            chain.extend(['RunLength', 'DeltaGCL', 'PISTMirror'])
        elif entropy < 5.0:
            # Medium entropy = structured → Huffman + STDP + Galois
            chain.extend(['Huffman', 'STDP', 'GaloisRing'])
        else:
            # High entropy = random-like → DSE + SBox + PISTResonance
            chain.extend(['DeterministicStochastic', 'SBox', 'PISTResonance'])

        # Add tension-dependent shifters
        if tension > 0.3:
            chain.append('SpikeTiming')
        else:
            chain.append('Morpholino')

        # Limit
        return chain[:self.max_chain_length]


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def print_header(title: str):
    """Print a styled section header."""
    width = 72
    print()
    print("╔" + "═" * width + "╗")
    print("║ " + title.ljust(width - 2) + " ║")
    print("╚" + "═" * width + "╝")


def demonstrate():
    """Run full demonstration of all shifters."""
    print_header("PIST BIOLOGICAL POLYMORPHIC SHIFTER v3.0")
    print("Hyperdimensional manifold compressor with 27+ encoding shifters")
    print()

    # ── Test Data ──
    test_sets = {
        "Short English": b"Hello World! This is a test of the biological polymorphic shifter system.",
        "Repeating": b"AAAAABBBBBCCCCCDDDDDEEEEE" * 10,
        "Binary": bytes(range(256)) * 4,
        "Mixed": b"The quick brown fox jumps over the lazy dog. " * 5 + bytes([0xFF, 0x00, 0xAA, 0x55]) * 10,
        "All Zeros": b"\x00" * 256,
        "Incrementing": bytes(range(256)),
    }

    compressor = BiologicalPolymorphicCompressor(max_chain_length=4, beam_width=4)

    total_original = 0
    total_compressed = 0

    for name, data in test_sets.items():
        print_header(f"TEST: {name} ({len(data)} bytes)")

        # 1. Analyze
        analysis = compressor.analyze(data)
        print(f"  Entropy:       {analysis['entropy']:.2f} bits/byte")
        print(f"  Unique bytes:  {analysis['unique_bytes']}")
        print(f"  Avg tension:   {analysis['avg_tension']:.3f}")
        print(f"  Grounded:      {analysis['grounded_pct']:.1f}%")
        print(f"  Seismic:       {analysis['seismic_pct']:.1f}%")
        print(f"  Recommended:   {analysis['recommended_chain']}")

        # 2. Auto-optimize
        print(f"\n  ▶ Optimizing...")
        best = compressor.auto_optimize(data, max_steps=8)
        print(f"  Best chain:    {best['chain']}")
        print(f"  Fitness:       {best['fitness']:.4f}")
        print(f"  Ratio:         {best['ratio']:.4f}x")

        # 3. Compress + verify
        result = compressor.verify(data, best['chain'])
        print(f"\n  ▶ Compress/Decompress:")
        print(f"  Size:          {result['original_size']} → {result['compressed_size']} bytes")
        print(f"  Ratio:         {result['ratio']:.3f}x")
        print(f"  Entropy:       {result['entropy']:.2f} bpb")
        print(f"  Lossless:      {'✅' if result['lossless'] else '❌'}")
        print(f"  Chain used:    {result['chain']}")

        total_original += result['original_size']
        total_compressed += result['compressed_size']

    # ── Summary ──
    print_header("OVERALL SUMMARY")
    print(f"  Total original:   {total_original} bytes")
    print(f"  Total compressed: {total_compressed} bytes")
    print(f"  Overall ratio:    {total_original / max(1, total_compressed):.3f}x")
    print(f"  Space saved:      {(1 - total_compressed / max(1, total_original)) * 100:.1f}%")
    print()

    # ── Exhaustive Chain Test ──
    print_header("EXHAUSTIVE: ALL SINGLE-SHIFTER CHAINS")
    print("Testing every shifter individually on 'Mixed' data...\n")

    mixed_data = b"The quick brown fox jumps over the lazy dog. " * 5
    results = []

    for name in compressor.optimizer.ALL_SHIFTERS:
        try:
            r = compressor.verify(mixed_data, [name])
            results.append((name, r['ratio'], r['lossless'], r['entropy']))
        except Exception as e:
            results.append((name, 0.0, False, 99.0))

    # Sort by ratio
    results.sort(key=lambda x: -x[1])

    print(f"  {'Shifter':<22} {'Ratio':>8} {'Lossless':>10} {'Entropy':>8}")
    print(f"  {'-'*22} {'-'*8} {'-'*10} {'-'*8}")
    for name, ratio, lossless, entropy in results:
        ll = '✅' if lossless else '❌'
        if ratio > 0:
            print(f"  {name:<22} {ratio:>7.2f}x {ll:>10} {entropy:>7.2f}")

    # ── Best Chains ──
    print_header("TOP 10 SHIFTER CHAINS (Beam Search)")
    print("Testing multi-shifter chains on 'Mixed' data...\n")

    optimizer = BiologicalManifoldOptimizer(max_chain_length=3, beam_width=6)
    best_result = optimizer.optimize(mixed_data, max_steps=10)

    print(f"  Best chain:  {best_result['chain']}")
    print(f"  Fitness:     {best_result['fitness']:.4f}")
    print(f"  Ratio:       {best_result['ratio']:.3f}x")
    print(f"  Entropy:     {best_result['entropy']:.2f} bpb")

    # Extract top chains from beam search candidates
    print(f"\n  Top configurations explored:")
    for neg_fit, candidate in optimizer.optimize.candidates[:10]:
        if isinstance(candidate, dict) and 'chain' in candidate:
            print(f"    - {candidate['chain']}: ratio={candidate.get('ratio', 0):.3f}x, "
                  f"fitness={candidate.get('fitness', 0):.3f}")

    print()
    print_header("DONE")
    print("Biological Polymorphic Shifter v3.0 demonstration complete.")
    print("ANY shifter with ANY shifter — the manifold is your substrate.")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    demonstrate()
