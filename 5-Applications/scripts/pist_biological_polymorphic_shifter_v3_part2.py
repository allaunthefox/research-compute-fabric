# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 1: HACHIMOJI DNA (8-letter encoding)
# ───────────────────────────────────────────────────────────────────────────────
# 8 letters → 3 bits per letter → 2.67x raw byte density
# Letters: A, T, C, G, Z, P, S, B
# ═══════════════════════════════════════════════════════════════════════════════

class HachimojiShifter(Shifter):
    name = "Hachimoji"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Encode bytes as Hachimoji 8-letter DNA sequence."""
        data = state.encoded

        # Map nibbles (4-bit) to Hachimoji letters
        # 16 possible nibble values → 16 Hachimoji "codons" (2-letter pairs)
        letters = list(HACHIMOJI_ALPHABET.keys())

        result = bytearray()
        for b in data:
            # Encode byte as two Hachimoji letters
            hi = (b >> 4) & 0x0F
            lo = b & 0x0F
            # Map nibbles to letters (if > 7, wrap around)
            l1 = letters[min(hi, len(letters) - 1)]
            l2 = letters[min(lo, len(letters) - 1)]
            # Store as ordinal values
            result.append(ord(l1))
            result.append(ord(l2))

        # Compress: RLE on repeated letter pairs
        compressed = bytearray()
        i = 0
        while i < len(result):
            j = i
            while j + 2 <= len(result) and result[j:j+2] == result[i:i+2]:
                j += 2
            run = (j - i) // 2
            if run >= 3:
                compressed.append(0xFE)  # RLE marker
                compressed.append(run)
                compressed.append(result[i])
                compressed.append(result[i+1])
                i = j
            else:
                compressed.append(result[i])
                i += 1

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(compressed), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Decode Hachimoji back to bytes."""
        data = state.encoded
        letters = list(HACHIMOJI_ALPHABET.keys())
        letter_to_idx = {l: i for i, l in enumerate(letters)}

        # Expand RLE
        expanded = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFE and i + 3 < len(data):
                run = data[i+1]
                l1 = chr(data[i+2])
                l2 = chr(data[i+3])
                for _ in range(run):
                    expanded.append(ord(l1))
                    expanded.append(ord(l2))
                i += 4
            else:
                expanded.append(data[i])
                i += 1

        # Decode pairs back to bytes
        result = bytearray()
        for i in range(0, len(expanded) - 1, 2):
            c1 = chr(expanded[i])
            c2 = chr(expanded[i+1])
            if c1 in letter_to_idx and c2 in letter_to_idx:
                hi = min(letter_to_idx[c1], 0x0F)
                lo = min(letter_to_idx[c2], 0x0F)
                result.append((hi << 4) | lo)
            else:
                result.append(expanded[i])

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 2: AEGIS (12+ letter expanded alphabet)
# ───────────────────────────────────────────────────────────────────────────────
# 12+ letters → ~3.585 bits per letter → more information density
# ═══════════════════════════════════════════════════════════════════════════════

class AEGISShifter(Shifter):
    name = "AEGIS"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Encode bytes as AEGIS 12-letter alphabet with base pairing."""
        data = state.encoded
        letters = list(AEGIS_ALPHABET.keys())

        result = bytearray()
        for b in data:
            # Map 8-bit byte to two AEGIS letters
            idx = b
            l1_idx = idx // 12
            l2_idx = idx % 12
            if l1_idx >= len(letters):
                l1_idx = len(letters) - 1
            if l2_idx >= len(letters):
                l2_idx = len(letters) - 1
            result.append(ord(letters[l1_idx]))
            result.append(ord(letters[l2_idx]))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Decode AEGIS back to bytes."""
        data = state.encoded
        letters = list(AEGIS_ALPHABET.keys())
        letter_to_idx = {l: i for i, l in enumerate(letters)}

        result = bytearray()
        for i in range(0, len(data) - 1, 2):
            c1 = chr(data[i])
            c2 = chr(data[i+1])
            idx1 = letter_to_idx.get(c1, 0)
            idx2 = letter_to_idx.get(c2, 0)
            b = idx1 * 12 + idx2
            result.append(min(b, 255))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 3: NATURAL DNA (4-letter alphabet)
# ───────────────────────────────────────────────────────────────────────────────
# 4 bases = 2 bits per base → direct nibble mapping
# ═══════════════════════════════════════════════════════════════════════════════

class NaturalDNAShifter(Shifter):
    name = "NaturalDNA"

    DNA_LETTERS = ['A', 'C', 'G', 'T']  # 2 bits each

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Encode bytes as DNA 4-letter sequence."""
        data = state.encoded
        result = bytearray()
        for b in data:
            hi = (b >> 6) & 0x03
            mid_hi = (b >> 4) & 0x03
            mid_lo = (b >> 2) & 0x03
            lo = b & 0x03
            result.append(ord(cls.DNA_LETTERS[hi]))
            result.append(ord(cls.DNA_LETTERS[mid_hi]))
            result.append(ord(cls.DNA_LETTERS[mid_lo]))
            result.append(ord(cls.DNA_LETTERS[lo]))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Decode DNA back to bytes."""
        data = state.encoded
        letter_to_val = {l: i for i, l in enumerate(cls.DNA_LETTERS)}

        result = bytearray()
        for i in range(0, len(data) - 3, 4):
            vals = []
            for j in range(4):
                c = chr(data[i+j])
                vals.append(letter_to_val.get(c, 0))
            b = (vals[0] << 6) | (vals[1] << 4) | (vals[2] << 2) | vals[3]
            result.append(b)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 4: RNA TRANSCRIPTION (DNA→RNA, T→U swap)
# ───────────────────────────────────────────────────────────────────────────────
# Transcription is an amplification step: one DNA → many RNA copies
# ═══════════════════════════════════════════════════════════════════════════════

class TranscriptionShifter(Shifter):
    name = "Transcription"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """
        Transcription: replace T→U, then amplify repeated sequence.
        The amplification factor represents multiple RNA copies.
        """
        data = state.encoded
        result = bytearray()

        # T→U conversion (ASCII: T=84→U=85, t=116→u=117)
        for b in data:
            if b == ord('T'):
                result.append(ord('U'))
            elif b == ord('t'):
                result.append(ord('u'))
            else:
                result.append(b)

        # Amplification: repeat 2x to represent multiple transcripts
        amplified = result * 2

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(amplified), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse transcription: U→T, halve length."""
        data = state.encoded
        # Halve (remove amplification)
        half = bytes(data[:len(data)//2]) if len(data) > 1 else data

        result = bytearray()
        for b in half:
            if b == ord('U'):
                result.append(ord('T'))
            elif b == ord('u'):
                result.append(ord('t'))
            else:
                result.append(b)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 5: TRANSLATION (RNA codons → amino acid peptide)
# ───────────────────────────────────────────────────────────────────────────────
# 3 nucleotides → 1 amino acid → 3:1 compression ratio
# ═══════════════════════════════════════════════════════════════════════════════

class TranslationShifter(Shifter):
    name = "Translation"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Translate RNA→Peptide. Groups bytes into codons, maps to amino acids."""
        rna_data = state.encoded

        # Convert bytes to RNA letters (A=65, C=67, G=71, U=85)
        rna_str = ''.join(chr(b) for b in rna_data if chr(b) in 'ACGUacgu')
        rna_str = rna_str.upper()

        # Pad to multiple of 3
        while len(rna_str) % 3 != 0:
            rna_str += 'A'

        # Translate
        peptide = []
        for i in range(0, len(rna_str), 3):
            codon = rna_str[i:i+3].replace('T', 'U')
            if codon in STANDARD_CODON_TABLE:
                aa = STANDARD_CODON_TABLE[codon]
                peptide.append(ord(aa[0]))  # Store amino acid as ASCII
            else:
                peptide.append(ord('X'))  # Unknown

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(peptide), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse translation: amino acid → most likely codon → RNA."""
        data = state.encoded

        result = []
        for b in data:
            aa = chr(b)
            if aa in AMINO_CODONS:
                # Pick first available codon
                codon = AMINO_CODONS[aa][0]
                result.extend(ord(c) for c in codon)
            else:
                result.extend([ord('N'), ord('N'), ord('N')])  # Unknown

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 6: PNA (Peptide Nucleic Acid — peptide backbone)
# ───────────────────────────────────────────────────────────────────────────────
# Neutral backbone, tighter binding. Treat as structural variant.
# ═══════════════════════════════════════════════════════════════════════════════

class PNAShifter(Shifter):
    name = "PNA"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """PNA encoding: peptide backbone modification.
        The neutral backbone allows stronger binding = more stable encoding.
        We represent this as an error-correcting code.
        """
        data = state.encoded
        # PNA can handle higher density: add parity nibbles
        result = bytearray()
        for b in data:
            result.append(b)
            # Add parity nibble as error correction (PNA stability bonus)
            parity = (b ^ (b >> 4)) & 0x0F
            result.append(0x50 | parity)  # PNA marker + parity

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """PNA decoding: strip parity, error correct."""
        data = state.encoded
        result = bytearray()
        for i in range(0, len(data) - 1, 2):
            byte_val = data[i]
            parity_marker = data[i+1]
            expected_parity = (byte_val ^ (byte_val >> 4)) & 0x0F
            actual_parity = parity_marker & 0x0F
            # If parity mismatch, try to correct
            if expected_parity != actual_parity:
                # Simple correction: flip bits until parity matches
                corrected = byte_val
                for bit in range(8):
                    test = byte_val ^ (1 << bit)
                    if ((test ^ (test >> 4)) & 0x0F) == actual_parity:
                        corrected = test
                        break
                result.append(corrected)
            else:
                result.append(byte_val)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 7: LNA (Locked Nucleic Acid — thermally stable)
# ───────────────────────────────────────────────────────────────────────────────
# Locked ribose = rigid structure = higher thermal stability threshold
# Represent as temperature-gated encoding
# ═══════════════════════════════════════════════════════════════════════════════

class LNAShifter(Shifter):
    name = "LNA"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """LNA encoding: lock byte positions for thermal stability.
        Represents as a stable temperature-invariant compressed form.
        """
        data = state.encoded

        # LNA "locks" the structure — store as delta from mean
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        mean = sum(data) / len(data)
        result = bytearray()
        for b in data:
            # Encode as deviation from mean (smaller = more stable)
            dev = b - int(mean)
            dk, dt = pist_encode(abs(dev))
            result.append(dk)
            result.append(dt if dev >= 0 else dt | 0x80)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """LNA decoding."""
        data = state.encoded
        result = bytearray()
        for i in range(0, len(data) - 1, 2):
            dk = data[i]
            dt = data[i+1] & 0x7F
            negative = (data[i+1] & 0x80) != 0
            abs_val = dk * dk + dt if dk >= 0 else 0
            if negative:
                result.append(128 - min(abs_val, 128))
            else:
                result.append(128 + min(abs_val, 127))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 8: RNA SPLICING (intron removal → compression)
# ───────────────────────────────────────────────────────────────────────────────
# Splicing removes introns (non-coding regions) and joins exons.
# Analogy: remove redundant/low-signal bytes, keep high-signal.
# ═══════════════════════════════════════════════════════════════════════════════

class SplicingShifter(Shifter):
    name = "Splicing"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Splicing: remove non-informative bytes based on PIST tension.
        Low-tension bytes are "introns" → spliced out.
        High-tension bytes are "exons" → retained.
        """
        data = state.encoded

        # Compute PIST tension for each byte
        exons = bytearray()
        splice_sites = []  # (start, end) of retained regions

        i = 0
        while i < len(data):
            k, t = pist_encode(data[i])
            mass = pist_mass(k, t)
            tension = t / max(1, 2 * k + 1)

            # Exon if tension > 0.3 (seismic half) or repeating pattern
            if mass > 0 or (i > 0 and data[i] == data[i-1]):
                exons.append(data[i])
                if not splice_sites or splice_sites[-1][1] < i:
                    splice_sites.append((i, i+1))
                else:
                    splice_sites[-1] = (splice_sites[-1][0], i+1)
            i += 1

        # Store exon data + splice site mapping
        result = bytearray()
        result.extend(struct.pack('>H', len(splice_sites)))
        for start, end in splice_sites[:255]:
            result.append(min(start, 255))
            result.append(min(end - start, 255))
        result.extend(exons)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['splice_sites'] = splice_sites
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse splicing. Reconstruct original positions."""
        data = state.encoded
        if len(data) < 2:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        num_sites = struct.unpack('>H', data[0:2])[0]
        ptr = 2
        splice_sites = []
        for _ in range(min(num_sites, len(data[ptr:]) // 2)):
            if ptr + 1 < len(data):
                start = data[ptr]
                length = data[ptr+1]
                splice_sites.append((start, start + length))
                ptr += 2

        exons = data[ptr:]

        # Reconstruct with zeros at un-spliced positions
        result = bytearray()
        exon_idx = 0
        for start, end in splice_sites:
            while exon_idx < start and exon_idx < len(exons):
                result.append(exons[exon_idx])
                exon_idx += 1
            for _ in range(end - start):
                if exon_idx < len(exons):
                    result.append(exons[exon_idx])
                    exon_idx += 1
                else:
                    result.append(0)

        # Append remaining
        while exon_idx < len(exons):
            result.append(exons[exon_idx])
            exon_idx += 1

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 9: PRION (self-propagating conformational shift)
# ───────────────────────────────────────────────────────────────────────────────
# Prions are self-propagating: once a conformation exists, it spreads.
# Analogy: repeating patterns amplify themselves exponentially.
# ═══════════════════════════════════════════════════════════════════════════════

class PrionShifter(Shifter):
    name = "Prion"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Prion encoding: self-propagating conformational pattern.

        Find dominant byte pattern and propagate it as a "prion strain."
        The pattern then converts all similar bytes to the strain conformation.
        Result: massive compression via conformational collapse.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # Find dominant byte (+ nearest neighbors as "prion seed")
        counts = Counter(data)
        prion_seed = counts.most_common(1)[0][0]

        # Find all occurrences within Hamming distance 1 of prion seed
        converted = bytearray()
        conversion_map = {}  # byte → prion conformer

        for b in data:
            if b == prion_seed or abs(b - prion_seed) <= 1:
                # Convert to prion conformation (compact form)
                converted.append(prion_seed)
                conversion_map[b] = 1  # converted
            else:
                # Different prion strain or resistant
                converted.append(b)
                conversion_map[b] = 0  # resistant

        # Separate into prion domain and resistant domain
        prion_domain = bytearray()
        resistant_domain = bytearray()
        resistant_positions = []

        for i, b in enumerate(converted):
            if b == prion_seed:
                prion_domain.append(b)
            else:
                resistant_domain.append(b)
                resistant_positions.append(i)

        # Store: prion_seed, ratio_of_conversion, prion_domain, resistant_mapping
        result = bytearray()
        result.append(prion_seed)
        conversion_ratio = len(prion_domain) / max(1, len(converted))
        result.append(min(255, int(conversion_ratio * 255)))

        # Prion domain (RLE compressed — prions are repetitive!)
        rle_prion = bytearray()
        i = 0
        while i < len(prion_domain):
            j = i
            while j < len(prion_domain) and prion_domain[j] == prion_domain[i]:
                j += 1
            run = j - i
            if run >= 3:
                rle_prion.append(0xFD)
                rle_prion.append(prion_domain[i])
                rle_prion.append(min(255, run))
            else:
                for _ in range(run):
                    rle_prion.append(prion_domain[i])
            i = j

        result.extend(struct.pack('>I', len(rle_prion)))
        result.extend(rle_prion)

        # Resistant domain
        result.extend(struct.pack('>I', len(resistant_domain)))
        result.extend(resistant_domain)
        for pos in resistant_positions[:255]:
            result.append(min(pos, 255))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['prion_seed'] = prion_seed
        new_state.metadata['conversion_ratio'] = conversion_ratio
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse prion propagation."""
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        ptr = 0
        prion_seed = data[ptr]; ptr += 1
        conversion_ratio = data[ptr] / 255.0 if data[ptr] > 0 else 0; ptr += 1

        # Read prion domain length
        if ptr + 4 > len(data):
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state
        prion_len = struct.unpack('>I', data[ptr:ptr+4])[0]; ptr += 4

        # Expand RLE prion domain
        prion_domain = bytearray()
        prion_end = min(ptr + prion_len, len(data))
        i = ptr
        while i < prion_end:
            if data[i] == 0xFD and i + 3 <= prion_end:
                val = data[i+1]
                run = data[i+2]
                prion_domain.extend([val] * run)
                i += 3
            else:
                prion_domain.append(data[i])
                i += 1
        ptr = prion_end

        # Read resistant domain
        if ptr + 4 > len(data):
            new_state = deepcopy(state)
            new_state.update_encoded(bytes(prion_domain), f"decode_{cls.name}")
            return new_state
        resist_len = struct.unpack('>I', data[ptr:ptr+4])[0]; ptr += 4
        resist_end = min(ptr + resist_len, len(data))
        resistant_domain = data[ptr:resist_end]
        ptr = resist_end

        # Read positions (best effort)
        positions = list(data[ptr:])

        # Interleave: prion domain + resistant domain at specified positions
        result = bytearray()
        prion_idx = 0
        resist_idx = 0

        total_len = len(prion_domain) + len(resistant_domain)
        for pos in range(total_len):
            if pos in positions and resist_idx < len(resistant_domain):
                result.append(resistant_domain[resist_idx])
                resist_idx += 1
            elif prion_idx < len(prion_domain):
                result.append(prion_domain[prion_idx])
                prion_idx += 1
            else:
                break

        # Re-expand prion conformers
        prion_val = prion_seed
        final = bytearray()
        for b in result:
            if b == prion_val:
                final.append(b)
            else:
                final.append(b)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(final), f"decode_{cls.name}")
        return new_state
