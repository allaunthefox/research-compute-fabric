use anyhow::{Context, Result};
use clap::Parser;
use famm_receipts::{clamp01, sha256_json};
use serde_json::{json, Value};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
struct Args {
    #[arg(long)]
    config: PathBuf,
    #[arg(long)]
    out: PathBuf,
}

fn number(test: &Value, key: &str) -> f64 {
    clamp01(test.get(key).and_then(Value::as_f64).unwrap_or(0.0))
}

fn score_anti_famm(test: &Value) -> Value {
    let invisible = number(test, "projection_invisibility");
    let target_change = number(test, "target_behavior_change");
    let invariant_fail = number(test, "invariant_failure");
    let false_scar = number(test, "false_scar_evidence");
    let residual = number(test, "hidden_residual");
    let risk = clamp01(
        0.30 * invisible
            + 0.30 * target_change
            + 0.20 * invariant_fail
            + 0.10 * false_scar
            + 0.10 * residual,
    );
    let test_hash = sha256_json(test);
    json!({
        "test_id": test.get("id").and_then(Value::as_str).map(str::to_owned).unwrap_or_else(|| test_hash[..12].to_string()),
        "type": "anti_famm",
        "risk": risk,
        "decision": if risk >= 0.5 { "WARDEN_BLOCK_OR_REOPEN" } else { "PASS_ADVERSARY_CHECK" },
        "test_hash": test_hash,
        "summary": {
            "projection_invisibility": invisible,
            "target_behavior_change": target_change,
            "invariant_failure": invariant_fail,
            "false_scar_evidence": false_scar,
            "hidden_residual": residual
        }
    })
}

fn score_anti_braid(test: &Value) -> Value {
    let order = number(test, "braid_order_residual");
    let alias = number(test, "receipt_alias_risk");
    let fake = number(test, "fake_receipt_risk");
    let toxic = number(test, "toxic_recombination_risk");
    let scar_mask = number(test, "scar_masking_risk");
    let local_global = number(test, "local_pass_global_fail");
    let risk = clamp01(
        0.20 * order
            + 0.20 * alias
            + 0.15 * fake
            + 0.15 * toxic
            + 0.15 * scar_mask
            + 0.15 * local_global,
    );
    let test_hash = sha256_json(test);
    json!({
        "test_id": test.get("id").and_then(Value::as_str).map(str::to_owned).unwrap_or_else(|| test_hash[..12].to_string()),
        "type": "anti_braidstorm",
        "risk": risk,
        "decision": if risk >= 0.5 { "WARDEN_BLOCK_OR_REOPEN" } else { "PASS_ADVERSARY_CHECK" },
        "test_hash": test_hash,
        "summary": {
            "braid_order_residual": order,
            "receipt_alias_risk": alias,
            "fake_receipt_risk": fake,
            "toxic_recombination_risk": toxic,
            "scar_masking_risk": scar_mask,
            "local_pass_global_fail": local_global
        }
    })
}

fn run(config: &Value) -> Value {
    let anti_famm = config
        .get("anti_famm_tests")
        .and_then(Value::as_array)
        .map(|tests| tests.iter().map(score_anti_famm).collect::<Vec<_>>())
        .unwrap_or_default();
    let anti_braid = config
        .get("anti_braidstorm_tests")
        .and_then(Value::as_array)
        .map(|tests| tests.iter().map(score_anti_braid).collect::<Vec<_>>())
        .unwrap_or_default();

    let all_tests = anti_famm
        .iter()
        .chain(anti_braid.iter())
        .cloned()
        .collect::<Vec<_>>();
    let blocked = all_tests
        .iter()
        .filter(|test| test["decision"] == "WARDEN_BLOCK_OR_REOPEN")
        .count();
    let max_risk = all_tests
        .iter()
        .filter_map(|test| test["risk"].as_f64())
        .fold(0.0, f64::max);
    let test_hashes = all_tests
        .iter()
        .map(|test| test["test_hash"].clone())
        .collect::<Vec<_>>();

    let mut receipt = json!({
        "receipt_type": "famm_adversarial_duals_receipt",
        "schema_version": "0.1.0",
        "target": config.get("target").cloned().unwrap_or_else(|| json!({})),
        "anti_famm_results": anti_famm,
        "anti_braidstorm_results": anti_braid,
        "summary": {
            "test_count": all_tests.len(),
            "blocked_or_reopened_count": blocked,
            "max_risk": max_risk
        },
        "warden_decision": if blocked > 0 { "BLOCK_OR_REOPEN_ROUTE" } else { "ALLOW_PROMOTION_CANDIDATE" },
        "nuvmap": {
            "target_hash": sha256_json(config.get("target").unwrap_or(&json!({}))),
            "test_hashes": test_hashes,
            "adversarial_dual_hash": sha256_json(&json!(all_tests.iter().map(|test| test["test_hash"].clone()).collect::<Vec<_>>()))
        },
        "no_drift_boundary": "Anti-FAMM and Anti-BraidStorm expose adversarial failure modes. Passing these checks is not a global proof by itself."
    });
    let hash = sha256_json(&receipt);
    receipt["receipt_hash"] = json!(hash);
    receipt
}

fn main() -> Result<()> {
    let args = Args::parse();
    let config_text = fs::read_to_string(&args.config)
        .with_context(|| format!("failed to read {}", args.config.display()))?;
    let config: Value = serde_json::from_str(&config_text)
        .with_context(|| format!("failed to parse {}", args.config.display()))?;
    let receipt = run(&config);

    if let Some(parent) = args.out.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&args.out, serde_json::to_string_pretty(&receipt)?)?;

    println!("Wrote {}", args.out.display());
    println!("Tests: {}", receipt["summary"]["test_count"]);
    println!(
        "Blocked/reopened: {}",
        receipt["summary"]["blocked_or_reopened_count"]
    );
    println!(
        "Warden decision: {}",
        receipt["warden_decision"].as_str().unwrap_or("")
    );
    println!(
        "Receipt hash: {}",
        receipt["receipt_hash"].as_str().unwrap_or("")
    );
    Ok(())
}
