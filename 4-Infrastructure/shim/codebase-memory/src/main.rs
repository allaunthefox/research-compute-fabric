use std::env;
use std::path::Path;

use codebase_memory::adapter::load_for_hermes;

fn main() {
    let args: Vec<String> = env::args().collect();
    let root = if args.len() > 1 {
        &args[1]
    } else {
        "."
    };
    let memory_path = Path::new(root).join(".hermes").join("codebase_memory.json");
    let mut adapter = load_for_hermes(Path::new(root), &memory_path);

    println!("[hermes-memory] Loaded adapter for {}", root);
    println!("[hermes-memory] Domains: 7");
    for dom in codebase_memory::types::CodeDomain::all() {
        println!(
            "  {}: {} active / {} capacity",
            dom.as_str(),
            adapter.active_count(dom.as_str()),
            adapter.capacity()
        );
    }

    println!("\n--- Sample query: AGENTS.md ---");
    let results = adapter.query_all("AGENTS.md");
    for (domain, cells) in &results {
        println!("  {}: {} matches", domain, cells.len());
    }

    println!("\n--- Committing all domains ---");
    for dom in codebase_memory::types::CodeDomain::all() {
        let receipt = adapter.commit(dom.as_str());
        println!(
            "  {}: success={} invariant={}",
            dom.as_str(),
            receipt.success,
            receipt.invariant
        );
    }

    println!("\n[hermes-memory] Done.");
}
