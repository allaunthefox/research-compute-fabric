use anyhow::{Context, Result};
use clap::Parser;
use famm_receipts::sha256_json;
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
struct Args {
    #[arg(long)]
    config: PathBuf,
    #[arg(long)]
    out: PathBuf,
}

fn pair_sums(values: &[i64]) -> Vec<Value> {
    let mut out = Vec::new();
    for (i, a) in values.iter().enumerate() {
        for (offset, b) in values[i..].iter().enumerate() {
            let j = i + offset;
            out.push(json!({"i": i, "j": j, "a": a, "b": b, "sum": a + b}));
        }
    }
    out
}

fn find_collisions(pairs: &[Value]) -> Vec<Value> {
    let mut seen: HashMap<i64, &Value> = HashMap::new();
    let mut collisions = Vec::new();

    for pair in pairs {
        let sum = pair["sum"].as_i64().unwrap_or_default();
        if let Some(previous) = seen.get(&sum) {
            let current_indices = HashSet::from([
                pair["i"].as_u64().unwrap_or_default(),
                pair["j"].as_u64().unwrap_or_default(),
            ]);
            let previous_indices = HashSet::from([
                previous["i"].as_u64().unwrap_or_default(),
                previous["j"].as_u64().unwrap_or_default(),
            ]);
            if current_indices != previous_indices {
                collisions.push(json!({
                    "sum_address": sum,
                    "pair_a": {
                        "i": previous["i"],
                        "j": previous["j"],
                        "values": [previous["a"].clone(), previous["b"].clone()]
                    },
                    "pair_b": {
                        "i": pair["i"],
                        "j": pair["j"],
                        "values": [pair["a"].clone(), pair["b"].clone()]
                    },
                    "trivial_collision": false,
                    "scar": "nontrivial_pair_sum_collision"
                }));
            }
        } else {
            seen.insert(sum, pair);
        }
    }

    collisions
}

fn candidate_gate(values: &[i64], candidate: i64) -> Value {
    let current_sums = pair_sums(values)
        .into_iter()
        .filter_map(|pair| pair["sum"].as_i64())
        .collect::<HashSet<_>>();

    let mut new_sums = values
        .iter()
        .map(|x| json!({"a": candidate, "b": x, "sum": candidate + x}))
        .collect::<Vec<_>>();
    new_sums.push(json!({"a": candidate, "b": candidate, "sum": 2 * candidate}));

    let external = new_sums
        .iter()
        .filter(|pair| {
            pair["sum"]
                .as_i64()
                .is_some_and(|sum| current_sums.contains(&sum))
        })
        .cloned()
        .collect::<Vec<_>>();

    let unique = new_sums
        .iter()
        .filter_map(|pair| pair["sum"].as_i64())
        .collect::<HashSet<_>>();
    let internal_count = new_sums.len().saturating_sub(unique.len());
    let admissible = external.is_empty() && internal_count == 0;

    json!({
        "candidate": candidate,
        "admissible": admissible,
        "new_sums": new_sums,
        "external_collisions": external,
        "internal_duplicate_count": internal_count
    })
}

fn additive_energy_ordered(values: &[i64]) -> i64 {
    let mut counts: HashMap<i64, i64> = HashMap::new();
    for a in values {
        for b in values {
            *counts.entry(a + b).or_default() += 1;
        }
    }
    counts.values().map(|count| count * count).sum()
}

fn run(config: &Value) -> Result<Value> {
    let values = config["set"]
        .as_array()
        .context("config.set must be an array")?
        .iter()
        .map(|value| value.as_i64().context("set values must be integers"))
        .collect::<Result<Vec<_>>>()?;

    let pairs = pair_sums(&values);
    let collisions = find_collisions(&pairs);
    let m = values.len() as i64;
    let e_plus = additive_energy_ordered(&values);
    let omega = e_plus - (2 * m * m - m);
    let is_sidon = collisions.is_empty() && omega == 0;

    let capacity = config.get("capacity_N").and_then(|capacity| {
        capacity.as_f64().map(|n| {
            let occupied = values.len() as f64;
            json!({
                "N": n as i64,
                "theodorus_shell_sqrt_N": n.sqrt(),
                "occupied": values.len(),
                "slack": n.sqrt() - occupied
            })
        })
    });

    let candidate_receipt = config
        .get("candidate")
        .and_then(Value::as_i64)
        .map(|candidate| candidate_gate(&values, candidate));

    let capacity_pressure = capacity
        .as_ref()
        .and_then(|c| c["slack"].as_f64())
        .map(|slack| -slack);

    let famm = json!({
        "sidon_collision_count": collisions.len(),
        "additive_energy_ordered": e_plus,
        "omega_sidon": omega,
        "scar_class": if is_sidon { "PASS_ZERO_SCAR" } else { "COLLISION_SCAR" },
        "coarsening_agent": if is_sidon {
            Value::Null
        } else {
            json!({
                "type": "sidon_collision_coarsener",
                "action": "downweight_or_merge_collision_basin",
                "reason": "nontrivial pair-sum collision or additive energy excess"
            })
        },
        "capacity": capacity,
        "candidate_gate": candidate_receipt,
        "semantic_mass_lanes": {
            "collision": collisions.len(),
            "additive_energy_excess": omega,
            "capacity_pressure": capacity_pressure,
            "residual": if is_sidon { 0 } else { collisions.len() as i64 + omega.max(0) }
        }
    });

    let mut receipt = json!({
        "receipt_type": "famm_sidon_map_receipt",
        "schema_version": "0.1.0",
        "set": values,
        "is_sidon": is_sidon,
        "pair_sums": pairs,
        "collisions": collisions,
        "famm": famm,
        "no_drift_boundary": "This receipt verifies Sidon pair-sum uniqueness and maps failures to FAMM scars. It does not prove maximality or physical realization."
    });

    let hash = sha256_json(&receipt);
    receipt["receipt_hash"] = json!(hash);
    Ok(receipt)
}

fn main() -> Result<()> {
    let args = Args::parse();
    let config_text = fs::read_to_string(&args.config)
        .with_context(|| format!("failed to read {}", args.config.display()))?;
    let config: Value = serde_json::from_str(&config_text)
        .with_context(|| format!("failed to parse {}", args.config.display()))?;
    let receipt = run(&config)?;

    if let Some(parent) = args.out.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&args.out, serde_json::to_string_pretty(&receipt)?)?;

    println!("Wrote {}", args.out.display());
    println!("Sidon: {}", receipt["is_sidon"].as_bool().unwrap_or(false));
    println!(
        "Collision count: {}",
        receipt["famm"]["sidon_collision_count"]
            .as_u64()
            .unwrap_or_default()
    );
    println!("Omega Sidon: {}", receipt["famm"]["omega_sidon"]);
    if !receipt["famm"]["candidate_gate"].is_null() {
        println!(
            "Candidate admissible: {}",
            receipt["famm"]["candidate_gate"]["admissible"]
                .as_bool()
                .unwrap_or(false)
        );
    }
    println!(
        "Receipt hash: {}",
        receipt["receipt_hash"].as_str().unwrap_or("")
    );
    Ok(())
}
