use crate::shifters::{ManifoldState, Shifter};
use serde_json::json;

pub struct MTFShifter;

impl Shifter for MTFShifter {
    fn name(&self) -> &'static str {
        "mtf"
    }

    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = if !state.encoded.is_empty() {
            &state.encoded
        } else {
            &state.raw_bytes
        };
        let mut alphabet: Vec<u8> = (0..=255).collect();
        let mut result = Vec::with_capacity(data.len());

        for &b in data {
            let idx = alphabet.iter().position(|&x| x == b).unwrap();
            result.push(idx as u8);
            alphabet.remove(idx);
            alphabet.insert(0, b);
        }

        state.update(result, self.name(), json!({}));
        Ok(())
    }

    fn decode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = &state.encoded;
        let mut alphabet: Vec<u8> = (0..=255).collect();
        let mut result = Vec::with_capacity(data.len());

        for &idx in data {
            let b = alphabet[idx as usize];
            result.push(b);
            alphabet.remove(idx as usize);
            alphabet.insert(0, b);
        }

        state.encoded = result;
        Ok(())
    }
}
