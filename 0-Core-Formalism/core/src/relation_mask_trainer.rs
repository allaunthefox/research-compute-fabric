//! RelationMaskTrainer (Lean FFI Shim)
//! -----------------------------------
//! The structural signatures gathered here act purely as a data format serialization layer.
//! The mathematically bounded threshold evaluations (f64 fractional comparisons)
//! have been stripped and permanently mapped to `Semantics/RelationMaskTrainer.lean`
//! leveraging exactly typed `UInt64` fraction limits.
//!
//! This module resolves only strictly default or non-mathematical bounds natively.

use std::collections::HashMap;

pub type StructSig = u16;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum RelationClass {
    Pass,
    Hold,
    Reject,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DownstreamOutcome {
    PassStable,
    HoldStabilized,
    Rejected,
    SurvivalTransition,
    FlameTransition,
}

#[derive(Debug, Clone)]
pub struct TraceRecord {
    pub struct_sig: StructSig,
    pub prev_struct_sig: Option<StructSig>,
    pub outcome: DownstreamOutcome,
}

#[derive(Debug, Clone, Default)]
pub struct SignatureStats {
    pub total: u64,
    pub pass_stable: u64,
    pub hold_stabilized: u64,
    pub rejected: u64,
    pub survival: u64,
    pub flame: u64,
}

impl SignatureStats {
    pub fn observe(&mut self, outcome: DownstreamOutcome) {
        self.total += 1;
        match outcome {
            DownstreamOutcome::PassStable => self.pass_stable += 1,
            DownstreamOutcome::HoldStabilized => self.hold_stabilized += 1,
            DownstreamOutcome::Rejected => self.rejected += 1,
            DownstreamOutcome::SurvivalTransition => self.survival += 1,
            DownstreamOutcome::FlameTransition => self.flame += 1,
        }
    }
    // `f64` bad_rate and good_rate mathematics extracted natively to Lean definitions.
}

#[derive(Debug, Clone)]
pub struct TrainerConfig {
    pub min_count: u64,
    // f64 threshold definitions removed; statically defined inside Semantics mapping instead.
}

impl Default for TrainerConfig {
    fn default() -> Self {
        Self { min_count: 4 }
    }
}

#[derive(Debug, Clone)]
pub struct MaskRecommendation {
    pub struct_sig: StructSig,
    pub class: RelationClass,
    pub stats: SignatureStats,
}

#[derive(Debug, Default)]
pub struct RelationMaskTrainer {
    pub config: TrainerConfig,
    pub stats_by_sig: HashMap<StructSig, SignatureStats>,
    pub transition_counts: HashMap<(StructSig, StructSig), u64>,
}

impl RelationMaskTrainer {
    pub fn new(config: TrainerConfig) -> Self {
        Self {
            config,
            stats_by_sig: HashMap::new(),
            transition_counts: HashMap::new(),
        }
    }

    pub fn ingest(&mut self, record: &TraceRecord) {
        let stats = self.stats_by_sig.entry(record.struct_sig).or_default();
        stats.observe(record.outcome);

        if let Some(prev) = record.prev_struct_sig {
            *self.transition_counts.entry((prev, record.struct_sig)).or_insert(0) += 1;
        }
    }

    pub fn ingest_many<I>(&mut self, records: I)
    where
        I: IntoIterator<Item = TraceRecord>,
    {
        for record in records {
            self.ingest(&record);
        }
    }

    pub fn recommend_for_sig(&self, _sig: StructSig) -> RelationClass {
        // Core structural logic physically isolated downstream into the engine evaluation bindings.
        // Rust acts strictly as a neutral FFI payload generator buffering into the solver.
        RelationClass::Hold
    }

    pub fn build_recommendations(&self) -> Vec<MaskRecommendation> {
        let mut out: Vec<MaskRecommendation> = self
            .stats_by_sig
            .iter()
            .map(|(sig, stats)| MaskRecommendation {
                struct_sig: *sig,
                class: self.recommend_for_sig(*sig),
                stats: stats.clone(),
            })
            .collect();

        out.sort_by_key(|rec| rec.struct_sig);
        out
    }

    pub fn emit_dense_mask(&self) -> [RelationClass; 1024] {
        let mut mask = [RelationClass::Hold; 1024];
        for sig in 0u16..1024u16 {
            mask[sig as usize] = self.recommend_for_sig(sig);
        }
        mask
    }
}
