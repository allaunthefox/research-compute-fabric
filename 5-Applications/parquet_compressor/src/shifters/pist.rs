use crate::shifters::{ManifoldState, Shifter};
use serde_json::json;

pub struct PISTShifter;

impl Shifter for PISTShifter {
    fn name(&self) -> &'static str {
        "pist"
    }

    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = if !state.encoded.is_empty() {
            &state.encoded
        } else {
            &state.raw_bytes
        };
        let mut result = Vec::with_capacity(data.len() * 2);

        for &b in data {
            let n = b as u64;
            let k = (n as f64).sqrt() as u64;
            let t = n - k * k;
            result.push(k as u8);
            result.push(t as u8);
        }

        state.update(result, self.name(), json!({}));
        Ok(())
    }

    fn decode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = &state.encoded;
        let mut result = Vec::with_capacity(data.len() / 2);
        for i in (0..data.len()).step_by(2) {
            if i + 1 >= data.len() {
                break;
            }
            let k = data[i] as u64;
            let t = data[i + 1] as u64;
            let n = k * k + t;
            result.push(n as u8);
        }
        state.encoded = result;
        Ok(())
    }
}
