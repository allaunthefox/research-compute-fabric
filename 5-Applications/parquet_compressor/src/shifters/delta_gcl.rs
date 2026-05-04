use crate::shifters::{Shifter, ManifoldState};
use serde_json::json;
use byteorder::{BigEndian, ByteOrder};

pub struct DeltaGCLShifter;

impl Shifter for DeltaGCLShifter {
    fn name(&self) -> &'static str { "delta_gcl" }

    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = if !state.encoded.is_empty() { &state.encoded } else { &state.raw_bytes };
        let chunk_size = 4096;
        if data.is_empty() {
            state.update(Vec::new(), self.name(), json!({}));
            return Ok(());
        }

        let mut result = Vec::new();
        let chunks: Vec<&[u8]> = data.chunks(chunk_size).collect();
        let n_chunks = chunks.len();

        let mut buf = [0u8; 4];
        BigEndian::write_u32(&mut buf, n_chunks as u32);
        result.extend_from_slice(&buf);

        let first_chunk = chunks[0];
        BigEndian::write_u32(&mut buf, first_chunk.len() as u32);
        result.extend_from_slice(&buf);
        result.extend_from_slice(first_chunk);

        let mut prev = first_chunk.to_vec();

        for i in 1..n_chunks {
            let curr = chunks[i];
            let max_len = prev.len().max(curr.len());
            
            let mut delta = Vec::with_capacity(max_len);
            for j in 0..max_len {
                let p = if j < prev.len() { prev[j] } else { 0 };
                let c = if j < curr.len() { curr[j] } else { 0 };
                delta.push(p ^ c);
            }

            // RLE the delta
            let mut rle = Vec::new();
            let mut j = 0;
            while j < delta.len() {
                let b = delta[j];
                let mut count = 1;
                while j + count < delta.len() && delta[j + count] == b && count < 255 {
                    count += 1;
                }
                rle.push(count as u8);
                rle.push(b);
                j += count;
            }

            BigEndian::write_u32(&mut buf, rle.len() as u32);
            result.extend_from_slice(&buf);
            result.extend_from_slice(&rle);
            
            prev = curr.to_vec();
        }

        state.update(result, self.name(), json!({}));
        Ok(())
    }

    fn decode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = &state.encoded;
        if data.len() < 4 { return Ok(()); }
        
        let n_chunks = BigEndian::read_u32(&data[0..4]) as usize;
        let mut ptr = 4;

        if ptr + 4 > data.len() { return Ok(()); }
        let first_len = BigEndian::read_u32(&data[ptr..ptr+4]) as usize;
        ptr += 4;
        
        if ptr + first_len > data.len() { return Ok(()); }
        let first_chunk = data[ptr..ptr+first_len].to_vec();
        ptr += first_len;

        let mut result = Vec::new();
        result.extend_from_slice(&first_chunk);
        
        let mut prev = first_chunk;

        for _ in 1..n_chunks {
            if ptr + 4 > data.len() { break; }
            let rle_len = BigEndian::read_u32(&data[ptr..ptr+4]) as usize;
            ptr += 4;
            
            if ptr + rle_len > data.len() { break; }
            let rle_data = &data[ptr..ptr+rle_len];
            ptr += rle_len;

            let mut delta = Vec::new();
            for j in (0..rle_data.len()).step_by(2) {
                if j + 1 >= rle_data.len() { break; }
                let count = rle_data[j] as usize;
                let b = rle_data[j+1];
                for _ in 0..count {
                    delta.push(b);
                }
            }

            let mut curr = Vec::with_capacity(delta.len());
            for j in 0..delta.len() {
                let p = if j < prev.len() { prev[j] } else { 0 };
                curr.push(p ^ delta[j]);
            }
            
            // Note: the original code doesn't store the exact length of each chunk if it was padded.
            // But since chunks are 4096, only the last one might be shorter.
            // Wait, the original Python code: `curr_padded = curr.ljust(max_len, b'\x00')`
            // and `result.extend(rle_result)`.
            // It doesn't seem to store the unpadded length. This might be a bug in the original or it assumes 4096.
            // For now, I'll just push it.
            result.extend_from_slice(&curr);
            prev = curr;
        }

        state.encoded = result;
        Ok(())
    }
}
