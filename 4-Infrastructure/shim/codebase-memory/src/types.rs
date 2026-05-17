// Core types for FAMM-based codebase memory

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// ============================================================================
// Q16_16 Fixed-Point Arithmetic
// ============================================================================

/// Q16.16 fixed-point representation.
/// Raw value: 0x00010000 = 1.0, range [-32768, 32767.999985].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Q16_16(pub u32);

impl Q16_16 {
    pub const ZERO: Q16_16 = Q16_16(0);
    pub const ONE: Q16_16 = Q16_16(0x0001_0000);

    pub fn from_nat(n: u32) -> Self {
        Q16_16(n.saturating_mul(65536))
    }

    pub fn from_float(f: f64) -> Self {
        let raw = (f * 65536.0).round() as i64;
        let clamped = raw.max(0).min(u32::MAX as i64) as u32;
        Q16_16(clamped)
    }

    pub fn add(&self, other: Q16_16) -> Self {
        Q16_16(self.0.saturating_add(other.0))
    }

    pub fn sub(&self, other: Q16_16) -> Self {
        Q16_16(self.0.saturating_sub(other.0))
    }

    pub fn mul(&self, other: Q16_16) -> Self {
        let a = self.0 as u64;
        let b = other.0 as u64;
        Q16_16(((a * b) >> 16).min(0xFFFF_FFFF) as u32)
    }

    pub fn lt(&self, other: Q16_16) -> bool {
        (self.0 as i32) < (other.0 as i32)
    }

    pub fn le(&self, other: Q16_16) -> bool {
        (self.0 as i32) <= (other.0 as i32)
    }

    pub fn gt(&self, other: Q16_16) -> bool {
        (self.0 as i32) > (other.0 as i32)
    }

    pub fn to_f64(&self) -> f64 {
        (self.0 as f64) / 65536.0
    }
}

// ============================================================================
// Domain Enumeration
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub enum CodeDomain {
    CoreFormalism = 0,
    Distributed = 1,
    SearchSpace = 2,
    MathModels = 3,
    Infrastructure = 4,
    Applications = 5,
    Documentation = 6,
}

impl CodeDomain {
    pub fn as_str(&self) -> &'static str {
        match self {
            CodeDomain::CoreFormalism  => "0-Core-Formalism",
            CodeDomain::Distributed     => "1-Distributed-Systems",
            CodeDomain::SearchSpace     => "2-Search-Space",
            CodeDomain::MathModels      => "3-Mathematical-Models",
            CodeDomain::Infrastructure => "4-Infrastructure",
            CodeDomain::Applications   => "5-Applications",
            CodeDomain::Documentation  => "6-Documentation",
        }
    }

    pub fn all() -> &'static [CodeDomain] {
        static DOMAINS: [CodeDomain; 7] = [
            CodeDomain::CoreFormalism,
            CodeDomain::Distributed,
            CodeDomain::SearchSpace,
            CodeDomain::MathModels,
            CodeDomain::Infrastructure,
            CodeDomain::Applications,
            CodeDomain::Documentation,
        ];
        &DOMAINS
    }
}

// ============================================================================
// Artifact Types
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArtifactType {
    Lean, Python, Markdown, Json, Yaml, Toml, Rust, Cpp, Verilog,
    Shell, Dockerfile, Config, Receipt, Other,
}

impl ArtifactType {
    pub fn from_extension(ext: Option<&str>) -> Self {
        match ext {
            Some("lean")       => ArtifactType::Lean,
            Some("py")         => ArtifactType::Python,
            Some("md")         => ArtifactType::Markdown,
            Some("json")       => ArtifactType::Json,
            Some("yaml") | Some("yml") => ArtifactType::Yaml,
            Some("toml")       => ArtifactType::Toml,
            Some("rs")         => ArtifactType::Rust,
            Some("cpp") | Some("cc") | Some("cxx") => ArtifactType::Cpp,
            Some("v")          => ArtifactType::Verilog,
            Some("sh")         => ArtifactType::Shell,
            Some("Dockerfile") => ArtifactType::Dockerfile,
            Some("cfg")        => ArtifactType::Config,
            _                  => ArtifactType::Other,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            ArtifactType::Lean      => ".lean",
            ArtifactType::Python    => ".py",
            ArtifactType::Markdown => ".md",
            ArtifactType::Json     => ".json",
            ArtifactType::Yaml     => ".yaml",
            ArtifactType::Toml     => ".toml",
            ArtifactType::Rust     => ".rs",
            ArtifactType::Cpp      => ".cpp",
            ArtifactType::Verilog  => ".v",
            ArtifactType::Shell    => ".sh",
            ArtifactType::Dockerfile => "Dockerfile",
            ArtifactType::Config   => ".cfg",
            ArtifactType::Receipt  => ".receipt.json",
            ArtifactType::Other    => "",
        }
    }
}

// ============================================================================
// CodeCell
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CodeCell {
    pub artifact_path: String,
    pub artifact_type: String,
    pub data: Q16_16,
    pub delay: Q16_16,
    pub delay_mass: Q16_16,
    pub delay_weight: Q16_16,
    pub version_hash: String,
    pub last_accessed: u64,
    pub access_count: u64,
    pub receipt_bound: bool,
}

impl CodeCell {
    pub fn default_cell() -> Self {
        CodeCell {
            artifact_path: String::new(),
            artifact_type: ArtifactType::Other.as_str().to_string(),
            data: Q16_16::ZERO,
            delay: Q16_16::ONE,
            delay_mass: Q16_16::ZERO,
            delay_weight: Q16_16::ONE,
            version_hash: String::new(),
            last_accessed: 0,
            access_count: 0,
            receipt_bound: true,
        }
    }
}

// ============================================================================
// FAMM Result
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FAMMResult {
    pub success: bool,
    pub value: Option<Q16_16>,
    pub cost: u32,
    pub invariant: String,
}

impl FAMMResult {
    pub fn fail(domain: &str, reason: &str) -> Self {
        FAMMResult {
            success: false,
            value: None,
            cost: 0xFFFF,
            invariant: format!("{domain}: {reason}"),
        }
    }
}

// ============================================================================
// Receipt
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryAccessReceipt {
    pub timestamp: u64,
    pub domain: String,
    pub action: String,
    pub path: String,
    pub success: bool,
    pub cost: u32,
    pub invariant: String,
    pub data_value: u32,
    pub thermal_ok: bool,
}

impl MemoryAccessReceipt {
    pub fn new_fail(domain: &str, reason: &str) -> Self {
        MemoryAccessReceipt {
            timestamp: 0,
            domain: domain.to_string(),
            action: "blocked".to_string(),
            path: reason.to_string(),
            success: false,
            cost: 0xFFFF,
            invariant: reason.to_string(),
            data_value: 0,
            thermal_ok: false,
        }
    }
}

// ============================================================================
// Domain Bank
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainBank {
    pub domain: String,
    pub cells: Vec<CodeCell>,
    pub size: usize,
    pub active_count: usize,
    pub max_delay: Q16_16,
    pub thermal_budget: Q16_16,
    pub current_stress: Q16_16,
    pub heatsink_halt: bool,
}

impl DomainBank {
    pub fn new(domain: CodeDomain, capacity: usize) -> Self {
        DomainBank {
            domain: domain.as_str().to_string(),
            cells: vec![CodeCell::default_cell(); capacity],
            size: capacity,
            active_count: 0,
            max_delay: Q16_16::from_nat(1000),
            thermal_budget: Q16_16::from_nat(5000),
            current_stress: Q16_16::ZERO,
            heatsink_halt: false,
        }
    }

    pub fn find_index(&self, path: &str) -> Option<usize> {
        self.cells.iter().position(|c| c.artifact_path == path)
    }

    pub fn next_free(&self) -> Option<usize> {
        self.cells.iter().position(|c| c.artifact_path.is_empty())
    }

    pub fn read(&self, idx: usize) -> FAMMResult {
        if idx >= self.cells.len() {
            return FAMMResult::fail(&self.domain, "out_of_bounds");
        }
        FAMMResult {
            success: true,
            value: Some(self.cells[idx].data),
            cost: 0x0000_1000,
            invariant: format!("{}: delay={}, mass={}",
                               &self.domain, self.cells[idx].delay.0, self.cells[idx].delay_mass.0),
        }
    }

    pub fn write(&mut self, idx: usize, cell: CodeCell) -> FAMMResult {
        if idx >= self.cells.len() {
            return FAMMResult::fail(&self.domain, "out_of_bounds");
        }
        if self.heatsink_halt {
            return FAMMResult::fail(&self.domain, "JUDGE_PAUSE thermal overload");
        }
        let mass = cell.delay_mass;
        self.current_stress = self.current_stress.add(mass);
        if !cell.artifact_path.is_empty() {
            self.active_count += 1;
        }
        self.cells[idx] = cell;
        FAMMResult {
            success: true,
            value: Some(self.cells[idx].data),
            cost: 0x0000_1000,
            invariant: format!("{}: written idx={}", &self.domain, idx),
        }
    }

    pub fn prune(&mut self) -> usize {
        let before = self.active_count;
        self.cells.retain(|c| c.artifact_path.is_empty() || c.delay.lt(self.max_delay));
        self.active_count = self.cells.iter().filter(|c| !c.artifact_path.is_empty()).count();
        while self.cells.len() < self.size {
            self.cells.push(CodeCell::default_cell());
        }
        before.saturating_sub(self.active_count)
    }

    pub fn check_thermal(&self) -> (bool, String) {
        if self.current_stress.gt(self.thermal_budget) || self.heatsink_halt {
            (false, "JUDGE_PAUSE: Thermal budget exceeded".to_string())
        } else {
            (true, "BUILDER_ADD: Within thermal budget".to_string())
        }
    }
}

// ============================================================================
// Scar Field
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainScarField {
    pub domain: String,
    pub residuals: Vec<Q16_16>,
    pub total: Q16_16,
    pub sorry_count: u64,
    pub todo_count: u64,
    pub gap_count: u64,
    pub last_updated: u64,
}

impl DomainScarField {
    pub fn new(domain: CodeDomain) -> Self {
        DomainScarField {
            domain: domain.as_str().to_string(),
            residuals: Vec::new(),
            total: Q16_16::ZERO,
            sorry_count: 0,
            todo_count: 0,
            gap_count: 0,
            last_updated: 0,
        }
    }

    pub fn accumulate(&mut self, scar: Q16_16) {
        self.residuals.push(scar);
        self.total = self.total.add(scar);
        self.last_updated += 1;
    }
}

// ============================================================================
// Memory State
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CodebaseMemoryState {
    pub banks: HashMap<String, DomainBank>,
    pub scar_fields: HashMap<String, DomainScarField>,
    pub epoch: u64,
    pub timestamp: u64,
    pub is_serialized: bool,
}

impl CodebaseMemoryState {
    pub fn new(capacity_per_domain: usize) -> Self {
        let mut banks = HashMap::new();
        let mut scars = HashMap::new();
        for dom in CodeDomain::all() {
            banks.insert(dom.as_str().to_string(), DomainBank::new(*dom, capacity_per_domain));
            scars.insert(dom.as_str().to_string(), DomainScarField::new(*dom));
        }
        CodebaseMemoryState {
            banks,
            scar_fields: scars,
            epoch: 0,
            timestamp: 0,
            is_serialized: false,
        }
    }

    pub fn check_thermal(&self) -> (bool, String) {
        for bank in self.banks.values() {
            let (ok, msg) = bank.check_thermal();
            if !ok { return (false, msg); }
        }
        (true, "BUILDER_ADD: All domains within thermal budget".to_string())
    }
}

// ============================================================================
// Commits
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CommitResult {
    Admit { reason: String },
    Hold  { reason: String },
    Block { reason: String },
}

// ============================================================================
// Differentials
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainScarDifferential {
    pub domain: String,
    pub ahead_scar: DomainScarField,
    pub behind_scar: DomainScarField,
    pub differential: Q16_16,
    pub epsilon: Q16_16,
    pub epoch: u64,
}

// ============================================================================
// Dual Map
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DualMapMemory {
    pub ahead: CodebaseMemoryState,
    pub behind: CodebaseMemoryState,
    pub differentials: HashMap<String, DomainScarDifferential>,
    pub global_epsilon: Q16_16,
    pub commit_queue: Vec<String>,
    pub epoch: u64,
}

impl DualMapMemory {
    pub fn new(capacity: usize) -> Self {
        let mut diffs = HashMap::new();
        for dom in CodeDomain::all() {
            diffs.insert(
                dom.as_str().to_string(),
                DomainScarDifferential {
                    domain: dom.as_str().to_string(),
                    ahead_scar: DomainScarField::new(*dom),
                    behind_scar: DomainScarField::new(*dom),
                    differential: Q16_16::ZERO,
                    epsilon: Q16_16::from_nat(50),
                    epoch: 0,
                },
            );
        }
        DualMapMemory {
            ahead: CodebaseMemoryState::new(capacity),
            behind: CodebaseMemoryState::new(capacity),
            differentials: diffs,
            global_epsilon: Q16_16::from_nat(50),
            commit_queue: Vec::new(),
            epoch: 0,
        }
    }

    pub fn commit_if_admissible(&mut self, domain: &str) -> MemoryAccessReceipt {
        let dsd = match self.differentials.get(domain) {
            Some(d) => d.clone(),
            None => return MemoryAccessReceipt::new_fail(domain, "domain_not_found"),
        };
        let abs_diff = if dsd.differential.lt(Q16_16::ZERO) {
            Q16_16::ZERO.sub(dsd.differential)
        } else {
            dsd.differential
        };
        if abs_diff.le(dsd.epsilon) {
            if let Some(bank) = self.ahead.banks.get(domain).cloned() {
                self.behind.banks.insert(domain.to_string(), bank);
            }
            if let Some(scar) = self.ahead.scar_fields.get(domain).cloned() {
                self.behind.scar_fields.insert(domain.to_string(), scar);
            }
            self.commit_queue.push("admit".to_string());
            MemoryAccessReceipt {
                timestamp: now_ms(),
                domain: domain.to_string(),
                action: "admitted".to_string(),
                path: "commit".to_string(),
                success: true,
                cost: 0x0000_1000,
                invariant: format!("admit: |Delta|={} <= epsilon={}", abs_diff.0, dsd.epsilon.0),
                data_value: 0,
                thermal_ok: true,
            }
        } else {
            self.commit_queue.push("hold".to_string());
            MemoryAccessReceipt {
                timestamp: now_ms(),
                domain: domain.to_string(),
                action: "blocked".to_string(),
                path: "commit".to_string(),
                success: false,
                cost: 0x0000_1000,
                invariant: format!("hold: |Delta|={} > epsilon={}", abs_diff.0, dsd.epsilon.0),
                data_value: 0,
                thermal_ok: true,
            }
        }
    }
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_q16_16_basic() {
        let a = Q16_16::from_nat(5);
        let b = Q16_16::from_nat(3);
        let sum = a.add(b);
        assert_eq!(sum.0, (5u32 + 3u32) * 65536);
    }

    #[test]
    fn test_code_domain_all() {
        let domains = CodeDomain::all();
        assert_eq!(domains.len(), 7);
        assert_eq!(domains[0], CodeDomain::CoreFormalism);
    }

    #[test]
    fn test_artifact_type_from_ext() {
        assert_eq!(ArtifactType::from_extension(Some("lean")), ArtifactType::Lean);
        assert_eq!(ArtifactType::from_extension(Some("unknown")), ArtifactType::Other);
    }

    #[test]
    fn test_domain_bank() {
        let mut bank = DomainBank::new(CodeDomain::CoreFormalism, 10);
        assert_eq!(bank.size, 10);
        let mut cell = CodeCell::default_cell();
        cell.artifact_path = "foo".to_string();
        let result = bank.write(0, cell);
        assert!(result.success);
        assert_eq!(bank.active_count, 1);
    }

    #[test]
    fn test_memory_state() {
        let state = CodebaseMemoryState::new(100);
        assert_eq!(state.banks.len(), 7);
    }

    #[test]
    fn test_dual_map_commit() {
        let mut dmm = DualMapMemory::new(50);
        let receipt = dmm.commit_if_admissible("0-Core-Formalism");
        assert!(receipt.success);
        assert!(receipt.invariant.contains("admit"));
    }
}
