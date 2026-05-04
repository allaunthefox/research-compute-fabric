use serde::{Serialize, Deserialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifoldState {
    pub raw_bytes: Vec<u8>,
    pub encoded: Vec<u8>,
    pub shifter_chain: Vec<String>,
    pub metadata: HashMap<String, serde_json::Value>,
    pub compression_ratio: f64,
}

impl ManifoldState {
    pub fn new(raw_bytes: Vec<u8>) -> Self {
        Self {
            raw_bytes,
            encoded: Vec::new(),
            shifter_chain: Vec::new(),
            metadata: HashMap::new(),
            compression_ratio: 1.0,
        }
    }

    pub fn update(&mut self, encoded: Vec<u8>, shifter_name: &str, metadata: serde_json::Value) {
        self.encoded = encoded;
        self.shifter_chain.push(shifter_name.to_string());
        self.metadata.insert(shifter_name.to_string(), metadata);
    }
}

pub trait Shifter {
    fn name(&self) -> &'static str;
    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()>;
    fn decode(&self, state: &mut ManifoldState) -> anyhow::Result<()>;
}

pub mod bwt;
pub mod mtf;
pub mod lzw;
pub mod rle;
pub mod huffman;
pub mod delta_gcl;
pub mod pist;

pub use bwt::BWTShifter;
pub use mtf::MTFShifter;
pub use lzw::LZWShifter;
pub use rle::RunLengthShifter;
pub use huffman::HuffmanShifter;
pub use delta_gcl::DeltaGCLShifter;
pub use pist::PISTShifter;

pub fn get_shifter(name: &str) -> Option<Box<dyn Shifter>> {
    match name {
        "bwt" => Some(Box::new(BWTShifter)),
        "mtf" => Some(Box::new(MTFShifter)),
        "lzw" => Some(Box::new(LZWShifter)),
        "run_length" => Some(Box::new(RunLengthShifter)),
        "huffman" => Some(Box::new(HuffmanShifter)),
        "delta_gcl" => Some(Box::new(DeltaGCLShifter)),
        "pist" => Some(Box::new(PISTShifter)),
        _ => None,
    }
}

pub fn intrinsic_load(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut counts = [0usize; 256];
    for &b in data {
        counts[b as usize] += 1;
    }
    let n = data.len() as f64;
    let mut entropy = 0.0;
    for &count in counts.iter() {
        if count > 0 {
            let p = count as f64 / n;
            entropy -= p * p.log2();
        }
    }
    entropy
}
