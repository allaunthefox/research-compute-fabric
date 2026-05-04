use crate::shifters::{Shifter, ManifoldState};
use serde_json::json;

pub struct RunLengthShifter;

impl Shifter for RunLengthShifter {
    fn name(&self) -> &'static str { "run_length" }

    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = if !state.encoded.is_empty() { &state.encoded } else { &state.raw_bytes };
        let mut result = Vec::new();
        let mut i = 0;
        while i < data.len() {
            let b = data[i];
            let mut count = 1;
            while i + count < data.len() && data[i + count] == b && count < 255 {
                count += 1;
            }
            result.push(count as u8);
            result.push(b);
            i += count;
        }

        let ratio = data.len() as f64 / result.len().max(1) as f64;
        state.update(result, self.name(), json!({"original": data.len(), "ratio": ratio}));
        Ok(())
    }

    fn decode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = &state.encoded;
        let mut result = Vec::new();
        for i in (0..data.len()).step_by(2) {
            if i + 1 >= data.len() { break; }
            let count = data[i] as usize;
            let b = data[i+1];
            for _ in 0..count {
                result.push(b);
            }
        }
        state.encoded = result;
        Ok(())
    }
}
