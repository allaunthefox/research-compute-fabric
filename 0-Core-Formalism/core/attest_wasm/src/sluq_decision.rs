//! # SLUQ-Enhanced Decision Tree (Lean Shim)
//!
//! Concept:
//! - SLUQ accumulators measure decision temperature rigorously bounded in Lean via Q16.16 metrics.
//! - Stable (00): Decision path is cool
//! - Rising (01): Decision path is warming up
//! - Unstable (10): Decision path is overheating
//! - Reset (11): Decision path snapped
//!
//! Note: Mathematical evaluations (float boundaries) have been stripped as per AGENTS.md Functional Collapse.
//! Actual accumulator transitions now resolve asynchronously via the global `bindserver` pipe bridging to `Semantics.SLUQ`.

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum SLUQState {
    Stable = 0b00,
    Rising = 0b01,
    Unstable = 0b10,
    Reset = 0b11,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CMYK {
    K = 0,
    C = 1,
    M = 2,
    Y = 3,
}

const PHI_SCALED: u32 = 0x9E3779B9;

/// Structural representation of SLUQ node bound over Q16.16 (UInt16 limits) for passing to Lean logic.
pub struct SluqDecisionNode {
    pub method: String,
    pub state: SLUQState,
    pub acc: u16,
    pub phi: u8,
    pub selection_count: u32,
}

impl SluqDecisionNode {
    pub fn new(method: &str, node_index: usize) -> Self {
        let phi = ((PHI_SCALED >> (node_index * 8)) & 0xFF) as u8;
        Self {
            method: method.to_string(),
            state: SLUQState::Stable,
            acc: 0,
            phi,
            selection_count: 0,
        }
    }

    /// Retrieve pre-quantized parameters for Lean evaluation step.
    /// Actual accumulation evaluation now performed exclusively via `bindserver`.
    pub fn q16_buffer_state(&self) -> (u16, u8) {
        (self.acc, self.phi)
    }

    pub fn is_overheated(&self) -> bool {
        matches!(self.state, SLUQState::Unstable | SLUQState::Reset)
    }
}
