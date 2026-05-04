import os
os.chdir('/home/allaun/Documents/Research Stack/3-Mathematical-Models')

with open('pist_biological_polymorphic_shifter_v3_complete.py', 'r') as f:
    content = f.read()

# Fix: Compressor.compress serializes state.metadata, decompress restores it
old_compress = """        # Build header — FIX 10: include shifter_kwargs for decompress
        # Serialize only serializable kwargs (no lambdas, no complex objects)
        serializable_kwargs = {}
        for sname, kwdict in shifter_kwargs.items():
            clean = {}
            for k, v in kwdict.items():
                if isinstance(v, (str, int, float, bool, list, dict, tuple, type(None))):
                    clean[k] = v
            if clean:
                serializable_kwargs[sname] = clean
        
        header = {
            'chain': [s.name for s in shifter_chain],
            'n_factor': current_state.n_factor,
            'original_size': len(data),
            'shifter_kwargs': serializable_kwargs,
        }"""

new_compress = """        # Build header — FIX 10: include shifter_kwargs AND metadata for decompress
        # Serialize only serializable kwargs
        serializable_kwargs = {}
        for sname, kwdict in shifter_kwargs.items():
            clean = {}
            for k, v in kwdict.items():
                if isinstance(v, (str, int, float, bool, list, dict, tuple, type(None))):
                    clean[k] = v
            if clean:
                serializable_kwargs[sname] = clean
        
        # Serialize metadata that encode() auto-generated
        serialized_metadata = {}
        for sname, md in current_state.metadata.items():
            clean = {}
            for k, v in md.items():
                if isinstance(v, (str, int, float, bool, list, dict, tuple, type(None))):
                    clean[k] = v
            if clean:
                serialized_metadata[sname] = clean
        
        header = {
            'chain': [s.name for s in shifter_chain],
            'n_factor': current_state.n_factor,
            'original_size': len(data),
            'shifter_kwargs': serializable_kwargs,
            'restore_metadata': serialized_metadata,
        }"""

if old_compress in content:
    content = content.replace(old_compress, new_compress)
    print("Compress: metadata serialized")
else:
    print("Compress pattern NOT FOUND!")
    # Try shorter match
    if "serializable_kwargs = {}" in content:
        print("  But serializable_kwargs found")
    # Just the header dict
    old_h = """        header = {
            'chain': [s.name for s in shifter_chain],
            'n_factor': current_state.n_factor,
            'original_size': len(data),
            'shifter_kwargs': serializable_kwargs,
        }"""
    new_h = """        header = {
            'chain': [s.name for s in shifter_chain],
            'n_factor': current_state.n_factor,
            'original_size': len(data),
            'shifter_kwargs': serializable_kwargs,
            'restore_metadata': serialized_metadata,
        }"""
    if old_h in content:
        content = content.replace(old_h, new_h)
        print("Header pattern fixed")

# Fix decompress to restore metadata
old_decomp = """        header = json.loads(header_bytes.decode('utf-8'))
        chain_names = header['chain']
        # FIX 10: Extract shifter_kwargs from header
        shifter_kwargs = header.get('shifter_kwargs', {})

        # Reconstruct shifter chain
        shifter_chain = []
        for name in chain_names:
            if name in SHIFTER_MAP:
                shifter_chain.append(SHIFTER_MAP[name])
            else:
                raise ValueError(f"Unknown shifter: {name}")

        # Apply decoders in reverse order — FIX 10: pass kwargs
        state = ManifoldState()
        state.encoded = bytearray(encoded_data)
        for sc in reversed(shifter_chain):
            kw = shifter_kwargs.get(sc.name, {})
            state = sc.decode(state, **kw)"""

new_decomp = """        header = json.loads(header_bytes.decode('utf-8'))
        chain_names = header['chain']
        # FIX 10: Extract shifter_kwargs from header
        shifter_kwargs = header.get('shifter_kwargs', {})
        # Restore encode-generated metadata so decoders can read it
        restore_metadata = header.get('restore_metadata', {})

        # Reconstruct shifter chain
        shifter_chain = []
        for name in chain_names:
            if name in SHIFTER_MAP:
                shifter_chain.append(SHIFTER_MAP[name])
            else:
                raise ValueError(f"Unknown shifter: {name}")

        # Apply decoders in reverse order — FIX 10: pass kwargs + restore metadata
        state = ManifoldState()
        state.encoded = bytearray(encoded_data)
        state.metadata = restore_metadata  # Restore encode-generated metadata
        for sc in reversed(shifter_chain):
            kw = shifter_kwargs.get(sc.name, {})
            state = sc.decode(state, **kw)"""

if old_decomp in content:
    content = content.replace(old_decomp, new_decomp)
    print("Decompress: metadata restored")
else:
    print("Decompress pattern NOT FOUND!")

with open('pist_biological_polymorphic_shifter_v3_complete.py', 'w') as f:
    f.write(content)

print("Done! Length:", len(content))
