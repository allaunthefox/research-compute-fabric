use crate::shifters::{ManifoldState, Shifter};
use byteorder::{BigEndian, ByteOrder};
use serde_json::json;

pub struct Compressor;

impl Compressor {
    pub fn compress(data: Vec<u8>, shifters: Vec<Box<dyn Shifter>>) -> anyhow::Result<Vec<u8>> {
        let mut state = ManifoldState::new(data);

        for shifter in shifters {
            shifter.encode(&mut state)?;
        }

        // Final result: [4-byte header_len][header_json][encoded_data]
        let header = json!({
            "chain": state.shifter_chain,
            "metadata": state.metadata,
        });
        let header_bytes = serde_json::to_vec(&header)?;

        let mut result = Vec::new();
        let mut buf = [0u8; 4];
        BigEndian::write_u32(&mut buf, header_bytes.len() as u32);
        result.extend_from_slice(&buf);
        result.extend_from_slice(&header_bytes);
        result.extend_from_slice(&state.encoded);

        Ok(result)
    }

    #[allow(dead_code)]
    pub fn decompress(compressed_data: &[u8]) -> anyhow::Result<Vec<u8>> {
        if compressed_data.len() < 4 {
            return Err(anyhow::anyhow!("Data too short"));
        }

        let header_len = BigEndian::read_u32(&compressed_data[0..4]) as usize;
        if compressed_data.len() < 4 + header_len {
            return Err(anyhow::anyhow!("Data too short for header"));
        }

        let header_bytes = &compressed_data[4..4 + header_len];
        let header: serde_json::Value = serde_json::from_slice(header_bytes)?;

        let encoded_data = &compressed_data[4 + header_len..];

        let mut state = ManifoldState::new(Vec::new());
        state.encoded = encoded_data.to_vec();
        state.shifter_chain = header["chain"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect();
        state.metadata = header["metadata"]
            .as_object()
            .unwrap_or(&serde_json::Map::new())
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();

        // Decode in reverse order
        let mut shifter_chain = state.shifter_chain.clone();
        shifter_chain.reverse();

        for name in shifter_chain {
            let shifter = crate::shifters::get_shifter(&name)
                .ok_or_else(|| anyhow::anyhow!("Unknown shifter: {}", name))?;
            shifter.decode(&mut state)?;
        }

        Ok(state.encoded)
    }
}
