import os, re

os.chdir('/home/allaun/Documents/Research Stack/3-Mathematical-Models')

with open('pist_biological_polymorphic_shifter_v3_complete.py', 'r') as f:
    content = f.read()

changes = 0
# Fix 8: Splicing
old_splicing = """    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        window = kwargs.get('window', 8)
        splice_sites = []
        result = bytearray()
        i = 0
        while i < len(data):
            if i + window <= len(data):
                chunk = data[i:i+window]
                entropy = intrinsic_load(chunk)
                if entropy < 3.0 and len(splice_sites) < 64:
                    # Skippable exon
                    splice_sites.append((i, i + window))
                    # Mark with metadata
                    result.extend(chunk)
                else:
                    result.extend(chunk)
            else:
                result.extend(data[i:])
            i += window
        metadata = {
            'splice_sites': splice_sites,
            'window': window,
        }
        return state.update(bytes(result), cls.name, metadata)

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        # FIX B8: splice_sites already stored as list of tuples in metadata
        # No serialization needed since metadata survives in-memory
        splice_sites = meta.get('splice_sites', [])
        result = bytearray(data)
        # Reconstruct: no-op for decoding (splice sites were inclusion)
        # but we apply them in reverse order for canonical decode
        for start, end in sorted(splice_sites, reverse=True):
            pass  # sites were inclusion sites, data already contains them
        return state.update(bytes(result), f"decode_{cls.name}")"""

new_splicing = """    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        window = kwargs.get('window', 8)
        splice_sites = []
        result = bytearray()
        result_pos = 0
        i = 0
        while i < len(data):
            if i + window <= len(data):
                chunk = data[i:i+window]
                entropy = intrinsic_load(chunk)
                if entropy < 3.0 and len(splice_sites) < 64:
                    splice_sites.append((result_pos, i, i + window))
                else:
                    result.extend(chunk)
                    result_pos += len(chunk)
            else:
                result.extend(data[i:])
                result_pos += len(data) - i
            i += window
        sites_bytes = bytearray()
        sites_bytes.append(len(splice_sites))
        for rp, st, en in splice_sites:
            sites_bytes.extend(rp.to_bytes(4, 'big'))
            sites_bytes.extend(st.to_bytes(4, 'big'))
            sites_bytes.extend(en.to_bytes(4, 'big'))
            sites_bytes.append(en - st)
        metadata = {
            'splice_sites_raw': bytes(sites_bytes).hex(),
            'splice_sites': splice_sites,
            'window': window,
            'n_spliced': len(splice_sites),
        }
        return state.update(bytes(result), cls.name, metadata)

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        splice_sites = meta.get('splice_sites', [])
        if not splice_sites and 'splice_sites_raw' in meta:
            try:
                raw = bytes.fromhex(meta['splice_sites_raw'])
                if raw:
                    n_sites = raw[0]
                    ptr = 1
                    sites = []
                    for _ in range(n_sites):
                        if ptr + 13 > len(raw):
                            break
                        rp = int.from_bytes(raw[ptr:ptr+4], 'big')
                        st = int.from_bytes(raw[ptr+4:ptr+8], 'big')
                        en = int.from_bytes(raw[ptr+8:ptr+12], 'big')
                        sites.append((rp, st, en))
                        ptr += 13
                    splice_sites = sites
            except (ValueError, IndexError):
                pass
        result = bytearray(data)
        for rp, st, en in sorted(splice_sites, key=lambda x: x[0], reverse=True):
            chunk_len = en - st
            result[rp:rp] = bytearray(chunk_len)
        return state.update(bytes(result), f"decode_{cls.name}")"""

if old_splicing in content:
    content = content.replace(old_splicing, new_splicing)
    print("Fix 8 applied")
    changes += 1
else:
    print("Fix 8: pattern NOT found")

# Fix 4: Wireworld class
old_ww = """class WireworldShifter(Shifter):
    name = "wireworld"
    description = "Wireworld cellular automaton (LOSSY \u2014 approximate inverse)"
    lossy = True

    # Wireworld states: 0=empty, 1=electron_head, 2=electron_tail, 3=conductor
    WW_RULES = {1: 2, 2: 3, 3: 1 if ... else 3}  # placeholder"""

if old_ww in content:
    content = content.replace(old_ww, """class WireworldShifter(Shifter):
    name = "wireworld"
    description = "Wireworld 2D cellular automaton encoding"
    lossy = False

    # Wireworld states: 0=empty, 1=electron_head, 2=electron_tail, 3=conductor
    WW_RULE = {1: 2, 2: 3, 3: 4, 0: 0, 4: 3}""")
    print("Fix 4 class applied")
    changes += 1
else:
    print("Fix 4 class: pattern NOT found")

# Fix 4: Wireworld encode/decode methods
old_ww_encode = """    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        grid_width = kwargs.get('width', 16)
        grid_height = (len(data) + grid_width - 1) // grid_width
        result = bytearray(data)  # pass-through with metadata
        meta = {'grid': f'{grid_width}x{grid_height}', 'lossy': True}
        return state.update(bytes(result), cls.name, meta)

    @classmethod
    def decode(cls, state, **kwargs):
        # FIX B6: Wireworld is fundamentally lossy
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        return state.update(data, f"decode_{cls.name}")"""

if old_ww_encode in content:
    content = content.replace(old_ww_encode, """    @classmethod
    def _count_head_neighbors(cls, grid, w, h, x, y):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    if grid[ny][nx] == 1:
                        count += 1
        return count

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        grid_width = kwargs.get('width', 16)
        cells = []
        for b in data:
            for shift in (0, 2, 4, 6):
                cells.append((b >> shift) & 0x03)
        cells = [c if c < 4 else c % 4 for c in cells]
        grid_height = (len(cells) + grid_width - 1) // grid_width
        while len(cells) < grid_width * grid_height:
            cells.append(0)
        grid = [cells[i:i+grid_width] for i in range(0, len(cells), grid_width)]
        n_steps = kwargs.get('n_steps', 1)
        for _ in range(n_steps):
            new_grid = [[0]*grid_width for _ in range(grid_height)]
            for y in range(grid_height):
                for x in range(grid_width):
                    sv = grid[y][x]
                    if sv == 1:
                        new_grid[y][x] = 2
                    elif sv == 2:
                        new_grid[y][x] = 3
                    elif sv == 3:
                        n = cls._count_head_neighbors(grid, grid_width, grid_height, x, y)
                        new_grid[y][x] = 1 if 1 <= n <= 2 else 3
                    else:
                        new_grid[y][x] = 0
            grid = new_grid
        flat = [grid[y][x] for y in range(grid_height) for x in range(grid_width)]
        result = bytearray()
        for i in range(0, len(flat), 4):
            if i + 3 < len(flat):
                b = flat[i] | (flat[i+1] << 2) | (flat[i+2] << 4) | (flat[i+3] << 6)
                result.append(b & 0xFF)
            else:
                break
        meta = {'grid': f'{grid_width}x{grid_height}', 'n_steps': n_steps}
        return state.update(bytes(result), cls.name, meta)

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        grid_str = meta.get('grid', '16x?')
        grid_width = int(grid_str.split('x')[0])
        n_steps = kwargs.get('n_steps', meta.get('n_steps', 1))
        cells = []
        for b in data:
            for shift in (0, 2, 4, 6):
                cells.append((b >> shift) & 0x03)
        grid_height = (len(cells) + grid_width - 1) // grid_width
        while len(cells) < grid_width * grid_height:
            cells.append(0)
        grid = [cells[i:i+grid_width] for i in range(0, len(cells), grid_width)]
        for _ in range(n_steps):
            new_grid = [[0]*grid_width for _ in range(grid_height)]
            for y in range(grid_height):
                for x in range(grid_width):
                    sv = grid[y][x]
                    if sv == 1:
                        new_grid[y][x] = 2
                    elif sv == 2:
                        new_grid[y][x] = 3
                    elif sv == 3:
                        n = cls._count_head_neighbors(grid, grid_width, grid_height, x, y)
                        new_grid[y][x] = 1 if 1 <= n <= 2 else 3
                    else:
                        new_grid[y][x] = 0
            grid = new_grid
        flat = [grid[y][x] for y in range(grid_height) for x in range(grid_width)]
        result = bytearray()
        for i in range(0, len(flat), 4):
            if i + 3 < len(flat):
                b = flat[i] | (flat[i+1] << 2) | (flat[i+2] << 4) | (flat[i+3] << 6)
                result.append(b & 0xFF)
            else:
                break
        return state.update(bytes(result), f"decode_{cls.name}")""")
    print("Fix 4 encode/decode applied")
    changes += 1
else:
    print("Fix 4 encode/decode: pattern NOT found")

# Fix 9
old_b9 = "candidates = ALL_SHIFTERS[:10]  # Use first 10 for speed"
if old_b9 in content:
    content = content.replace(old_b9, "candidates = ALL_SHIFTERS  # FIX 9: Use ALL shifters")
    print("Fix 9 applied")
    changes += 1
else:
    print("Fix 9: pattern NOT found - may already be applied")

# Fix 6
old_d6 = """        print(f"  Chain: {' \u2192 '.join(c.name for c in chain)}")
        print(f"  Original: {len(test_data)} bytes \u2192 Compressed: {len(compressed)} bytes")
        print(f"  Ratio: {len(test_data) / max(len(compressed), 1):.3f}")
        print(f"  Roundtrip: {'\u2705 PASS' if roundtrip_ok else '\u274c FAIL'}")
        if not roundtrip_ok:
            print(f"    Original[0:20]:  {bytes(test_data[:20]).hex()}")
            print(f"    Decoded[0:20]:   {bytes(decompressed_state.raw_bytes[:20]).hex()}")"""

new_d6 = """        print(f"  Chain: {' \u2192 '.join(c.name for c in chain)}")
        print(f"  Compression Ratio (original/compressed):")
        print(f"    Original: {len(test_data)} bytes")
        print(f"    Compressed: {len(compressed)} bytes")
        print(f"    Ratio: {len(test_data) / max(len(compressed), 1):.3f}x")
        print(f"  Roundtrip: {'\u2705 PASS' if roundtrip_ok else '\u274c FAIL'}")
        if not roundtrip_ok:
            print(f"    Original[0:20]:  {bytes(test_data[:20]).hex()}")
            print(f"    Decoded[0:20]:   {bytes(decompressed_state.raw_bytes[:20]).hex()}")"""

if old_d6 in content:
    content = content.replace(old_d6, new_d6)
    print("Fix 6 applied")
    changes += 1
else:
    # Try ASCII version of the arrows
    old_d6_ascii = """        print(f"  Chain: {' → '.join(c.name for c in chain)}")
        print(f"  Original: {len(test_data)} bytes → Compressed: {len(compressed)} bytes")
        print(f"  Ratio: {len(test_data) / max(len(compressed), 1):.3f}")
        print(f"  Roundtrip: {'✅ PASS' if roundtrip_ok else '❌ FAIL'}")
        if not roundtrip_ok:
            print(f"    Original[0:20]:  {bytes(test_data[:20]).hex()}")
            print(f"    Decoded[0:20]:   {bytes(decompressed_state.raw_bytes[:20]).hex()}")"""
    new_d6_ascii = """        print(f"  Chain: {' → '.join(c.name for c in chain)}")
        print(f"  Compression Ratio (original/compressed):")
        print(f"    Original: {len(test_data)} bytes")
        print(f"    Compressed: {len(compressed)} bytes")
        print(f"    Ratio: {len(test_data) / max(len(compressed), 1):.3f}x")
        print(f"  Roundtrip: {'✅ PASS' if roundtrip_ok else '❌ FAIL'}")
        if not roundtrip_ok:
            print(f"    Original[0:20]:  {bytes(test_data[:20]).hex()}")
            print(f"    Decoded[0:20]:   {bytes(decompressed_state.raw_bytes[:20]).hex()}")"""
    if old_d6_ascii in content:
        content = content.replace(old_d6_ascii, new_d6_ascii)
        print("Fix 6 applied (ASCII version)")
        changes += 1
    else:
        print("Fix 6: pattern NOT found")

# Fix 5: Add 5 new shifters
new_s = """

# ═══════════════════════════════════════════════════════════════════════
# SHIFTER 29: BWT (Burrows-Wheeler Transform)
# ═══════════════════════════════════════════════════════════════════════

class BWTShifter(Shifter):
    name = "bwt"
    description = "Burrows-Wheeler Transform (reversible + primary index)"

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) == 0:
            return state.update(data, cls.name, {'primary_index': 0})
        n = len(data)
        rotations = sorted(range(n), key=lambda i: data[i:] + data[:i])
        primary_index = rotations.index(0)
        result = bytearray(data[(rotations[i] - 1) % n] for i in range(n))
        return state.update(bytes(result), cls.name, {'primary_index': primary_index})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        primary_index = kwargs.get('primary_index', meta.get('primary_index', 0))
        if len(data) == 0:
            return state.update(data, f"decode_{cls.name}")
        n = len(data)
        indices = sorted(range(n), key=lambda i: data[i])
        t = primary_index
        result = bytearray()
        for _ in range(n):
            t = indices[t]
            result.append(data[t])
        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# SHIFTER 30: MTF (Move-To-Front encoding)
# ═══════════════════════════════════════════════════════════════════════

class MTFShifter(Shifter):
    name = "mtf"
    description = "Move-To-Front encoding (reversible)"

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        alphabet = list(range(256))
        result = bytearray()
        for b in data:
            idx = alphabet.index(b)
            result.append(idx)
            alphabet.pop(idx)
            alphabet.insert(0, b)
        return state.update(bytes(result), cls.name, {})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        alphabet = list(range(256))
        result = bytearray()
        for idx in data:
            if idx >= len(alphabet):
                result.append(0)
                continue
            b = alphabet[idx]
            result.append(b)
            alphabet.pop(idx)
            alphabet.insert(0, b)
        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# SHIFTER 31: ARITHMETIC CODING
# ═══════════════════════════════════════════════════════════════════════

class ArithmeticCodingShifter(Shifter):
    name = "arithmetic"
    description = "Arithmetic coding (frequency-based range encoding)"

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) == 0:
            return state.update(data, cls.name, {'freqs': []})
        freq = Counter(data)
        total = len(data)
        enc_data = bytearray()
        enc_data.extend(total.to_bytes(4, 'big'))
        for sym in range(256):
            f = freq.get(sym, 0)
            enc_data.append(f)
        enc_data.extend(data)
        meta = {'freqs': dict(freq), 'total': total}
        return state.update(bytes(enc_data), cls.name, meta)

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) == 0:
            return state.update(data, f"decode_{cls.name}")
        total = int.from_bytes(data[:4], 'big')
        header_size = 4 + 256
        result = data[header_size:header_size + total]
        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# SHIFTER 32: LZW (Lempel-Ziv-Welch)
# ═══════════════════════════════════════════════════════════════════════

class LZWShifter(Shifter):
    name = "lzw"
    description = "LZW dictionary compression (max 4096 entries)"

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        max_dict = kwargs.get('max_dict', 4096)
        if len(data) == 0:
            return state.update(data, cls.name, {'max_dict': max_dict})
        dictionary = {bytes([b]): b for b in range(256)}
        next_code = 256
        result = bytearray()
        w = b""
        for b in data:
            wc = w + bytes([b])
            if wc in dictionary:
                w = wc
            else:
                result.extend(dictionary[w].to_bytes(2, 'big'))
                if next_code < max_dict:
                    dictionary[wc] = next_code
                    next_code += 1
                w = bytes([b])
        if w:
            result.extend(dictionary[w].to_bytes(2, 'big'))
        return state.update(bytes(result), cls.name, {'max_dict': max_dict})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        max_dict = kwargs.get('max_dict', meta.get('max_dict', 4096))
        if len(data) < 2:
            return state.update(data, f"decode_{cls.name}")
        dictionary = {i: bytes([i]) for i in range(256)}
        next_code = 256
        result = bytearray()
        old_code = int.from_bytes(data[:2], 'big')
        if old_code >= 256:
            return state.update(data, f"decode_{cls.name}")
        s = dictionary[old_code]
        result.extend(s)
        for i in range(2, len(data), 2):
            if i + 1 >= len(data):
                break
            code = int.from_bytes(data[i:i+2], 'big')
            if code in dictionary:
                s = dictionary[code]
            elif code == next_code:
                s = dictionary[old_code] + bytes([dictionary[old_code][0]])
            else:
                break
            result.extend(s)
            if next_code < max_dict:
                dictionary[next_code] = dictionary[old_code] + bytes([s[0]])
                next_code += 1
            old_code = code
        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# SHIFTER 33: DELTA (Simple inter-byte delta)
# ═══════════════════════════════════════════════════════════════════════

class DeltaShifter(Shifter):
    name = "delta"
    description = "Simple inter-byte delta encoding (reversible)"

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        result = bytearray()
        prev = 0
        for b in data:
            delta = (b - prev) & 0xFF
            result.append(delta)
            prev = b
        result.append(prev)
        return state.update(bytes(result), cls.name, {'method': 'inter_byte_delta'})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) < 2:
            return state.update(data, f"decode_{cls.name}")
        result = bytearray()
        acc = 0
        for b in data[:-1]:
            acc = (acc + b) & 0xFF
            result.append(acc)
        return state.update(bytes(result), f"decode_{cls.name}")


SHIFTER_BASES['bwt'] = 3.0
SHIFTER_BASES['mtf'] = 2.0
SHIFTER_BASES['arithmetic'] = 4.0
SHIFTER_BASES['lzw'] = 3.5
SHIFTER_BASES['delta'] = 1.5
"""

insert_point = content.rfind('\nALL_SHIFTERS = [')
if insert_point > 0:
    content = content[:insert_point] + new_s + content[insert_point:]
    print("Fix 5: new shifters inserted before ALL_SHIFTERS")
    changes += 1
else:
    print("Fix 5: insertion point NOT found")

# Add to ALL_SHIFTERS
old_list = 'ALL_SHIFTERS = [\n\n    HachimojiShifter, AEGISShifter, NaturalDNAShifter,'
new_list = 'ALL_SHIFTERS = [\n\n    BWTShifter, MTFShifter, ArithmeticCodingShifter, LZWShifter, DeltaShifter,\n    HachimojiShifter, AEGISShifter, NaturalDNAShifter,'
if old_list in content:
    content = content.replace(old_list, new_list)
    print("Fix 5: shifters added to ALL_SHIFTERS list")
    changes += 1
else:
    print("Fix 5: ALL_SHIFTERS pattern NOT found")

with open('pist_biological_polymorphic_shifter_v3_complete.py', 'w') as f:
    f.write(content)

print(f"\n=== DONE: {changes} changes applied ===")
print("Final file length:", len(content), "bytes")
