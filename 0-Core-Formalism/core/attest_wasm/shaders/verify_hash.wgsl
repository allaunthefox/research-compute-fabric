// WebGPU Compute Shader: Parallel SHA-256 Batch Verification
//
// This shader verifies a batch of SHA-256 hashes on the GPU.
// Each workgroup processes one attestation entry.
// Output: 1 if hash matches expected, 0 if mismatch.
//
// Provenance: Adapted for Omnitoken v4 / Sentient Evidence Layer

@group(0) @binding(0) var<storage, read> input_data: array<u32>;
@group(0) @binding(1) var<storage, read> expected_hashes: array<u32>;
@group(0) @binding(2) var<storage, read_write> results: array<u32>;
@group(0) @binding(3) var<uniform> params: vec4<u32>;
// params.x = data_size_bytes
// params.y = num_entries
// params.z = hash_size_bytes (32 for SHA-256)
// params.w = reserved

// SHA-256 constants
const K: array<u32, 64> = array<u32, 64>(
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u,
    0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
    0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u,
    0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
    0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu,
    0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
    0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u,
    0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
    0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u,
    0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
    0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u,
    0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
    0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u,
    0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
    0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u
);

fn rotr(v: u32, n: u32) -> u32 {
    return (v >> n) | (v << (32u - n));
}

fn ch(x: u32, y: u32, z: u32) -> u32 {
    return (x & y) ^ (~x & z);
}

fn maj(x: u32, y: u32, z: u32) -> u32 {
    return (x & y) ^ (x & z) ^ (y & z);
}

fn sigma0(x: u32) -> u32 {
    return rotr(x, 2u) ^ rotr(x, 13u) ^ rotr(x, 22u);
}

fn sigma1(x: u32) -> u32 {
    return rotr(x, 6u) ^ rotr(x, 11u) ^ rotr(x, 25u);
}

fn gamma0(x: u32) -> u32 {
    return rotr(x, 7u) ^ rotr(x, 18u) ^ (x >> 3u);
}

fn gamma1(x: u32) -> u32 {
    return rotr(x, 17u) ^ rotr(x, 19u) ^ (x >> 10u);
}

// Process one 512-bit (64-byte) block
fn sha256_block(state: ptr<function, array<u32, 8>>, block_start: u32) {
    var w: array<u32, 64>;

    // Load and byte-swap first 16 words
    for (var i = 0u; i < 16u; i++) {
        let idx = block_start + i;
        let raw = input_data[idx];
        // Swap bytes (little-endian to big-endian)
        w[i] = ((raw & 0xFFu) << 24u) |
               (((raw >> 8u) & 0xFFu) << 16u) |
               (((raw >> 16u) & 0xFFu) << 8u) |
               ((raw >> 24u) & 0xFFu);
    }

    // Expand message schedule
    for (var i = 16u; i < 64u; i++) {
        w[i] = gamma1(w[i - 2u]) + w[i - 7u] + gamma0(w[i - 15u]) + w[i - 16u];
    }

    // Working variables
    var a = (*state)[0];
    var b = (*state)[1];
    var c = (*state)[2];
    var d = (*state)[3];
    var e = (*state)[4];
    var f = (*state)[5];
    var g = (*state)[6];
    var h = (*state)[7];

    // 64 rounds
    for (var i = 0u; i < 64u; i++) {
        let t1 = h + sigma1(e) + ch(e, f, g) + K[i] + w[i];
        let t2 = sigma0(a) + maj(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }

    (*state)[0] += a;
    (*state)[1] += b;
    (*state)[2] += c;
    (*state)[3] += d;
    (*state)[4] += e;
    (*state)[5] += f;
    (*state)[6] += g;
    (*state)[7] += h;
}

@compute @workgroup_size(1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let entry_idx = gid.x;
    let num_entries = params.y;

    if (entry_idx >= num_entries) {
        return;
    }

    // Each entry is (data_size_bytes / 4) u32 words
    let words_per_entry = (params.x + 3u) / 4u;
    let data_offset = entry_idx * words_per_entry;

    // SHA-256 initial state
    var state = array<u32, 8>(
        0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
        0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u
    );

    // Process data in 64-byte blocks
    let total_words = words_per_entry;
    var block: u32 = 0u;
    while (block * 16u < total_words) {
        sha256_block(&state, data_offset + block * 16u);
        block += 1u;
    }

    // Compare with expected hash
    let hash_offset = entry_idx * 8u; // 8 u32s per SHA-256 hash
    var match: u32 = 1u;
    for (var i = 0u; i < 8u; i++) {
        // Byte-swap state for comparison
        let computed = state[i];
        let expected_raw = expected_hashes[hash_offset + i];
        let expected = ((expected_raw & 0xFFu) << 24u) |
                       (((expected_raw >> 8u) & 0xFFu) << 16u) |
                       (((expected_raw >> 16u) & 0xFFu) << 8u) |
                       ((expected_raw >> 24u) & 0xFFu);
        if (computed != expected) {
            match = 0u;
            break;
        }
    }

    results[entry_idx] = match;
}