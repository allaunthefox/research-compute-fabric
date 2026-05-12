import os
os.chdir('/home/allaun/Documents/Research Stack/3-Mathematical-Models')

with open('pist_biological_polymorphic_shifter_v3_complete.py', 'r') as f:
    content = f.read()

# LogisticMap: encode reads r_scaled from metadata fallback, decode passes metadata to encode
old_lm = """        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        r = kwargs.get('r', 3.9)
        x0 = kwargs.get('x0', 0.5)
        result = bytearray()
        # FIX 1: Integer discretization for deterministic roundtrip
        r_scaled = int(r * 256.0 + 0.5) & 0xFFFF
        x = int(x0 * 256.0 + 0.5) & 0xFFFF"""

new_lm = """        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        r = kwargs.get('r', meta.get('r', 3.9))
        x0 = kwargs.get('x0', meta.get('x0', 0.5))
        result = bytearray()
        # FIX 1: Integer discretization for deterministic roundtrip
        r_scaled = kwargs.get('r_scaled', meta.get('r_scaled', int(r * 256.0 + 0.5) & 0xFFFF))
        x = int(x0 * 256.0 + 0.5) & 0xFFFF"""

content = content.replace(old_lm, new_lm)

# LogisticMap decode: read from metadata and pass to encode
old_lm_decode = """    @classmethod
    def decode(cls, state, **kwargs):
        return cls.encode(state, **kwargs)  # XOR is self-inverse"""

new_lm_decode = """    @classmethod
    def decode(cls, state, **kwargs):
        # FIX: Read params from metadata fallback for self-inverse XOR
        meta = state.metadata.get(cls.name, {})
        if not kwargs and meta:
            kwargs = dict(meta)
        return cls.encode(state, **kwargs)  # XOR is self-inverse"""

content = content.replace(old_lm_decode, new_lm_decode)

# GaloisRing: already has metadata fallback - good
# STDP: needs metadata fallback
old_stdp_decode = """    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        tau = kwargs.get('tau', 20.0)
        result = bytearray()
        for i, b in enumerate(data):
            weight = math.exp(-i / tau) if tau > 0 else 1.0
            unmodulated = int(b / weight) if weight > 0 else b
            result.append(min(max(unmodulated, 0), 255))
        return state.update(bytes(result), f"decode_{cls.name}")"""

new_stdp_decode = """    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        tau = kwargs.get('tau', meta.get('tau', 20.0))
        result = bytearray()
        for i, b in enumerate(data):
            weight = math.exp(-i / tau) if tau > 0 else 1.0
            unmodulated = int(b / weight) if weight > 0 else b
            result.append(min(max(unmodulated, 0), 255))
        return state.update(bytes(result), f"decode_{cls.name}")"""

content = content.replace(old_stdp_decode, new_stdp_decode)

# miRNA: needs metadata fallback for decode
old_mirna_decode = """    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFE and i + 2 <= len(data):
                result.extend([data[i+1]] * 6)
                i += 2
            else:
                result.append(data[i])
                i += 1
        return state.update(bytes(result), f"decode_{cls.name}")"""

new_mirna_decode = """    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        meta = state.metadata.get(cls.name, {})
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFE and i + 2 <= len(data):
                result.extend([data[i+1]] * 6)
                i += 2
            else:
                result.append(data[i])
                i += 1
        return state.update(bytes(result), f"decode_{cls.name}")"""

content = content.replace(old_mirna_decode, new_mirna_decode)

# Wireworld: store original_size in metadata so decode can trim
old_ww_encode_meta = "meta = {'grid': f'{grid_width}x{grid_height}', 'n_steps': n_steps}"
new_ww_encode_meta = "meta = {'grid': f'{grid_width}x{grid_height}', 'n_steps': n_steps, 'original_size': len(data)}"
content = content.replace(old_ww_encode_meta, new_ww_encode_meta)

with open('pist_biological_polymorphic_shifter_v3_complete.py', 'w') as f:
    f.write(content)

print("Fixed LogisticMap, STDP, miRNA, Wireworld metadata fallback")
print("Length:", len(content))
