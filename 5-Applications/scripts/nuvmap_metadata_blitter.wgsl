// NUVMAP metadata blitter for WebGPU.
//
// One invocation scans one fixed-size metadata record/window and emits:
//   key_buffer[i]     = sortable route key
//   metric_buffer[i]  = packed byte/delta/hash metrics
//
// The shader is intentionally tiny and SIMD-friendly. It does not decompress,
// classify semantic meaning, or claim compression gain. It only turns byte-ish
// metadata windows into deterministic route keys for later sorting/probing.

struct BlitParams {
    record_count: u32,
    words_per_record: u32,
    stride_words: u32,
    source_offset_words: u32,
    route_salt: u32,
    flags: u32,
}

@group(0) @binding(0) var<storage, read> source_words: array<u32>;
@group(0) @binding(1) var<storage, read_write> key_buffer: array<u32>;
@group(0) @binding(2) var<storage, read_write> metric_buffer: array<u32>;
@group(0) @binding(3) var<uniform> params: BlitParams;

const WORDS_HARD_CAP: u32 = 64u;

fn popcount32(v: u32) -> u32 {
    return countOneBits(v);
}

fn byte_class_counts(word: u32) -> vec4<u32> {
    var counts = vec4<u32>(0u, 0u, 0u, 0u);
    for (var lane = 0u; lane < 4u; lane = lane + 1u) {
        let b = (word >> (lane * 8u)) & 0xFFu;
        let cls = b >> 6u;
        if (cls == 0u) {
            counts.x = counts.x + 1u;
        } else if (cls == 1u) {
            counts.y = counts.y + 1u;
        } else if (cls == 2u) {
            counts.z = counts.z + 1u;
        } else {
            counts.w = counts.w + 1u;
        }
    }
    return counts;
}

fn mix32(x: u32) -> u32 {
    var h = x;
    h = h ^ (h >> 16u);
    h = h * 0x7FEB352Du;
    h = h ^ (h >> 15u);
    h = h * 0x846CA68Bu;
    h = h ^ (h >> 16u);
    return h;
}

fn pack_key(hash8: u32, density7: u32, delta7: u32, zero6: u32, flags4: u32) -> u32 {
    return ((hash8 & 0xFFu) << 24u) |
           ((density7 & 0x7Fu) << 17u) |
           ((delta7 & 0x7Fu) << 10u) |
           ((zero6 & 0x3Fu) << 4u) |
           (flags4 & 0xFu);
}

fn pack_metric(class_counts: vec4<u32>, high_bit_share7: u32, words_seen: u32) -> u32 {
    let c0 = min(class_counts.x, 0x3Fu);
    let c1 = min(class_counts.y, 0x3Fu);
    let c2 = min(class_counts.z, 0x3Fu);
    let c3 = min(class_counts.w, 0x3Fu);
    return (c0 << 26u) |
           (c1 << 20u) |
           (c2 << 14u) |
           (c3 << 8u) |
           ((high_bit_share7 & 0x7Fu) << 1u) |
           min(words_seen, 1u);
}

@compute @workgroup_size(256, 1, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let record_index = gid.x;
    if (record_index >= params.record_count) {
        return;
    }

    let words_to_scan = min(params.words_per_record, WORDS_HARD_CAP);
    let base = params.source_offset_words + record_index * params.stride_words;
    var hash_acc = mix32(record_index ^ params.route_salt);
    var one_bits = 0u;
    var zero_bytes = 0u;
    var delta_acc = 0u;
    var class_counts = vec4<u32>(0u, 0u, 0u, 0u);
    var previous = 0u;

    for (var i = 0u; i < words_to_scan; i = i + 1u) {
        let word = source_words[base + i];
        hash_acc = mix32(hash_acc ^ word ^ (i * 0x9E3779B9u));
        one_bits = one_bits + popcount32(word);
        class_counts = class_counts + byte_class_counts(word);

        for (var lane = 0u; lane < 4u; lane = lane + 1u) {
            let b = (word >> (lane * 8u)) & 0xFFu;
            if (b == 0u) {
                zero_bytes = zero_bytes + 1u;
            }
        }

        if (i > 0u) {
            delta_acc = delta_acc + popcount32(word ^ previous);
        }
        previous = word;
    }

    let total_bits = max(words_to_scan * 32u, 1u);
    let total_bytes = max(words_to_scan * 4u, 1u);
    let high_bit_share7 = min((one_bits * 127u) / total_bits, 127u);
    let density7 = high_bit_share7;
    let delta7 = min((delta_acc * 127u) / total_bits, 127u);
    let zero6 = min((zero_bytes * 63u) / total_bytes, 63u);
    let hash8 = hash_acc >> 24u;

    var flags4 = params.flags & 0xFu;
    if (zero6 > 48u) {
        flags4 = flags4 | 0x1u;
    }
    if (delta7 > 96u) {
        flags4 = flags4 | 0x2u;
    }
    if (density7 < 16u || density7 > 112u) {
        flags4 = flags4 | 0x4u;
    }

    key_buffer[record_index] = pack_key(hash8, density7, delta7, zero6, flags4);
    metric_buffer[record_index] = pack_metric(class_counts, high_bit_share7, words_to_scan);
}
