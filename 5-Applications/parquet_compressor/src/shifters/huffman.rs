use crate::shifters::{ManifoldState, Shifter};
use serde_json::json;

pub struct HuffmanShifter;

impl Shifter for HuffmanShifter {
    fn name(&self) -> &'static str {
        "huffman"
    }

    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        // TODO: Implement Huffman
        let data = if !state.encoded.is_empty() {
            &state.encoded
        } else {
            &state.raw_bytes
        };
        state.update(data.to_vec(), self.name(), json!({}));
        Ok(())
    }

    fn decode(&self, _state: &mut ManifoldState) -> anyhow::Result<()> {
        Ok(())
    }
}
