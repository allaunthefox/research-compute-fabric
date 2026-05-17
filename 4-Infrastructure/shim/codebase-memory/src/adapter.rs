//!
//! codebase_memory::adapter -- Hermes agent integration for FAMM memory
//!
use serde_json;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;
use walkdir::WalkDir;

use crate::types::{
    ArtifactType, CodeCell, CodeDomain, DualMapMemory, MemoryAccessReceipt, Q16_16,
};

/// Hermes interface to the Research Stack codebase.
pub struct CodebaseMemoryAdapter {
    memory: DualMapMemory,
    capacity: usize,
}

impl CodebaseMemoryAdapter {
    pub fn init_fresh(capacity: usize) -> Self {
        CodebaseMemoryAdapter {
            memory: DualMapMemory::new(capacity),
            capacity,
        }
    }

    pub fn load_or_init(path: &Path) -> Self {
        if path.exists() {
            if let Ok(adapter) = Self::load(path) {
                return adapter;
            }
        }
        Self::init_fresh(1000)
    }

    pub fn load(path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let mut file = fs::File::open(path)?;
        let mut contents = String::new();
        file.read_to_string(&mut contents)?;
        let memory: DualMapMemory = serde_json::from_str(&contents)?;
        Ok(CodebaseMemoryAdapter {
            memory,
            capacity: 1000,
        })
    }

    pub fn save(&self, path: &Path) -> Result<(), Box<dyn std::error::Error>> {
        let json = serde_json::to_string_pretty(&self.memory)?;
        let mut file = fs::File::create(path)?;
        file.write_all(json.as_bytes())?;
        Ok(())
    }

    pub fn observe(
        &mut self,
        domain: &str,
        artifact_type: &str,
        artifact_path: &str,
        data: Q16_16,
        delay: Q16_16,
        delay_mass: Q16_16,
    ) -> MemoryAccessReceipt {
        let bank = match self.memory.ahead.banks.get_mut(domain) {
            Some(b) => b,
            None => {
                return MemoryAccessReceipt {
                    timestamp: 0,
                    domain: domain.to_string(),
                    action: "blocked".to_string(),
                    path: artifact_path.to_string(),
                    success: false,
                    cost: 0xFFFF,
                    invariant: "domain_not_found".to_string(),
                    data_value: 0,
                    thermal_ok: false,
                }
            }
        };
        let idx = match bank.find_index(artifact_path) {
            Some(i) => i,
            None => match bank.next_free() {
                Some(i) => i,
                None => {
                    bank.prune();
                    bank.next_free().unwrap_or(0)
                }
            },
        };
        let old_hash = bank.cells[idx].version_hash.clone();
        let new_hash = file_hash(artifact_path);
        bank.cells[idx] = CodeCell {
            artifact_path: artifact_path.to_string(),
            artifact_type: artifact_type.to_string(),
            data,
            delay,
            delay_mass,
            delay_weight: Q16_16::ONE,
            version_hash: new_hash.clone(),
            last_accessed: now_ms(),
            access_count: bank.cells[idx].access_count + 1,
            receipt_bound: true,
        };
        if !artifact_path.is_empty() {
            bank.active_count += 1;
        }
        bank.current_stress = bank.current_stress.add(delay_mass);
        if !old_hash.is_empty() && old_hash != new_hash {
            if let Some(dsd) = self.memory.differentials.get_mut(domain) {
                dsd.ahead_scar.accumulate(delay_mass);
                dsd.differential = dsd.ahead_scar.total.sub(dsd.behind_scar.total);
            }
        }
        MemoryAccessReceipt {
            timestamp: now_ms(),
            domain: domain.to_string(),
            action: "write".to_string(),
            path: artifact_path.to_string(),
            success: true,
            cost: 0x0000_1000,
            invariant: format!("observed path={}", artifact_path),
            data_value: data.0,
            thermal_ok: true,
        }
    }

    pub fn commit(&mut self, domain: &str) -> MemoryAccessReceipt {
        self.memory.commit_if_admissible(domain)
    }

    pub fn advance_epoch(&mut self) {
        self.memory.epoch += 1;
        let domains: Vec<String> = self.memory.differentials.keys().cloned().collect();
        for dom in domains {
            self.commit(&dom);
        }
    }

    pub fn query_all(&self,
        artifact_path: &str,
    ) -> HashMap<String, Vec<&CodeCell>> {
        let mut results = HashMap::new();
        for (domain, bank) in &self.memory.ahead.banks {
            let cells: Vec<&CodeCell> = bank
                .cells
                .iter()
                .filter(|c| c.artifact_path.contains(artifact_path))
                .collect();
            if !cells.is_empty() {
                results.insert(domain.clone(), cells);
            }
        }
        results
    }

    pub fn active_count(&self, domain: &str) -> usize {
        self.memory
            .ahead
            .banks
            .get(domain)
            .map(|b| b.active_count)
            .unwrap_or(0)
    }

    pub fn capacity(&self) -> usize {
        self.capacity
    }

    pub fn memory(&self) -> &DualMapMemory {
        &self.memory
    }
}

pub fn load_for_hermes(
    project_root: &Path,
    memory_path: &Path,
) -> CodebaseMemoryAdapter {
    std::fs::create_dir_all(memory_path.parent().unwrap_or(memory_path)).ok();
    let mut adapter = CodebaseMemoryAdapter::load_or_init(memory_path);
    for dom in CodeDomain::all() {
        let dom_path = project_root.join(dom.as_str());
        if !dom_path.is_dir() { continue; }
        for entry in WalkDir::new(&dom_path).into_iter().filter_map(|e| e.ok()) {
            if !entry.file_type().is_file() { continue; }
            let path = entry.path();
            let ext = path.extension().and_then(|s| s.to_str());
            let artifact_type = ArtifactType::from_extension(ext);
            adapter.observe(
                dom.as_str(),
                artifact_type.as_str(),
                path.to_string_lossy().as_ref(),
                Q16_16::ZERO, Q16_16::ONE, Q16_16::ZERO,
            );
        }
    }
    adapter.save(memory_path).ok();
    adapter
}

fn file_hash(path: &str) -> String {
    match fs::read(path) {
        Ok(bytes) => {
            let hash = Sha256::digest(&bytes);
            format!("{:x}", hash)[..16].to_string()
        }
        Err(_) => String::new(),
    }
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
