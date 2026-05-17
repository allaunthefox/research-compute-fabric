use crate::shifters::{ManifoldState, Shifter};
use divsufsort::sort_in_place;
use serde_json::json;

pub struct BWTShifter;

impl Shifter for BWTShifter {
    fn name(&self) -> &'static str {
        "bwt"
    }

    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = if !state.encoded.is_empty() {
            &state.encoded
        } else {
            &state.raw_bytes
        };
        if data.is_empty() {
            state.update(Vec::new(), self.name(), json!({"primary_index": 0}));
            return Ok(());
        }

        let n = data.len();
        // divsufsort computes the suffix array SA
        // The BWT L is defined as: L[i] = data[SA[i] - 1] (with wrap around)
        // And we need the primary_index such that SA[primary_index] == 0.

        let mut sa = vec![0i32; n];
        sort_in_place(data, &mut sa);

        let mut primary_index = 0;
        let mut result = Vec::with_capacity(n);

        for i in 0..n {
            let s_idx = sa[i] as usize;
            if s_idx == 0 {
                primary_index = i;
                result.push(data[n - 1]);
            } else {
                result.push(data[s_idx - 1]);
            }
        }

        state.update(result, self.name(), json!({"primary_index": primary_index}));
        Ok(())
    }

    fn decode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = &state.encoded;
        if data.is_empty() {
            return Ok(());
        }

        let meta = state
            .metadata
            .get(self.name())
            .cloned()
            .unwrap_or(json!({}));
        let primary_index = meta
            .get("primary_index")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as usize;

        let n = data.len();

        // Decoding BWT:
        // 1. Count occurrences of each byte
        let mut counts = [0usize; 256];
        for &b in data {
            counts[b as usize] += 1;
        }

        // 2. Compute starting positions in sorted order
        let mut start_pos = [0usize; 256];
        let mut sum = 0;
        for i in 0..256 {
            start_pos[i] = sum;
            sum += counts[i];
        }

        // 3. Compute LF mapping
        let mut lf = vec![0usize; n];
        let mut current_counts = [0usize; 256];
        for i in 0..n {
            let b = data[i] as usize;
            lf[i] = start_pos[b] + current_counts[b];
            current_counts[b] += 1;
        }

        // 4. Reconstruct string
        let mut result = vec![0u8; n];
        let mut curr = primary_index;
        for i in (0..n).rev() {
            result[i] = data[curr];
            curr = lf[curr];
        }

        state.encoded = result;
        Ok(())
    }
}
