pub mod adapter;
pub mod types;

pub use adapter::{load_for_hermes, CodebaseMemoryAdapter};
pub use types::{
    ArtifactType, CodeCell, CodeDomain, CommitResult, DomainBank, DomainScarDifferential,
    DomainScarField, DualMapMemory, FAMMResult, MemoryAccessReceipt, Q16_16,
};
