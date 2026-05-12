use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

/// Compact feature vector for efficient serialization
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FeatureVector {
    /// Microsecond timestamp for precise temporal alignment
    pub timestamp_us: u64,

    /// Spectral energy bins (fixed small size for compactness)
    pub spectral: SmallVec<[f32; 16]>,

    /// Transient characteristics: [attack, decay, zero_crossing_rate, crest_factor]
    pub transient: SmallVec<[f32; 4]>,

    /// Information metrics: [entropy, variance, predictability]
    pub information: SmallVec<[f32; 3]>,

    /// Optional: binary mask for sparse representations
    #[serde(skip_serializing_if = "Option::is_none")]
    pub mask: Option<SmallVec<[bool; 16]>>,
}

/// Signal workload classification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorkloadClass {
    SpectralFocus,    // Frequency-rich content
    TransientEdge,    // Sharp attacks/decays
    Hybrid,           // Mixed characteristics
    Raw,              // Noisy/aperiodic
    Silent,           // Below threshold
}

impl WorkloadClass {
    pub fn as_u8(&self) -> u8 {
        match self {
            WorkloadClass::SpectralFocus => 0,
            WorkloadClass::TransientEdge => 1,
            WorkloadClass::Hybrid => 2,
            WorkloadClass::Raw => 3,
            WorkloadClass::Silent => 4,
        }
    }
}
