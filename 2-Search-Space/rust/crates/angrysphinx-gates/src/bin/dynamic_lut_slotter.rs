use clap::Parser;
use serde_json::{json, Value};

#[derive(Clone, Copy)]
struct WorkloadProfile {
    name: &'static str,
    slot: u8,
    default_domain: u8,
    default_scalar: u8,
    mountain_range: &'static str,
}

#[derive(Clone)]
struct OmniToken {
    shell: String,
    workload: &'static str,
    mountain_range: &'static str,
    slot: u8,
    domain: u8,
    scalar: u8,
    avmr_signal: u8,
    s3c_emit: bool,
    s3c_score: u8,
    ammr_safe: bool,
}

#[derive(Parser)]
#[command(about = "Dynamic Omnitoken LUT slot selector for workload-shaped tiny tokens.")]
struct Args {
    #[arg(long, default_value = "ethernet")]
    shell: String,
    #[arg(long, default_value = "angry_sphinx")]
    workload: String,
    #[arg(long, default_value_t = 10, value_parser = clap::value_parser!(u8).range(0..=100))]
    pressure: u8,
    #[arg(long = "partial-budget", default_value_t = 32)]
    partial_budget: u8,
    #[arg(long, value_parser = parse_byte)]
    scalar: Option<u8>,
    #[arg(long)]
    demo: bool,
    #[arg(long)]
    jsonl: bool,
}

const RECOVERY: WorkloadProfile = WorkloadProfile {
    name: "recovery",
    slot: 0x01,
    default_domain: 0x0D,
    default_scalar: 0x01,
    mountain_range: "root_mountain",
};

const ANGRY_SPHINX: WorkloadProfile = WorkloadProfile {
    name: "angry_sphinx",
    slot: 0x02,
    default_domain: 0x0F,
    default_scalar: 0x01,
    mountain_range: "frustration_range",
};

const STANDARDS_REGISTRY: WorkloadProfile = WorkloadProfile {
    name: "standards_registry",
    slot: 0x20,
    default_domain: 0x10,
    default_scalar: 0x01,
    mountain_range: "public_basis_range",
};

const CRYPTO_MEV_RESEARCH: WorkloadProfile = WorkloadProfile {
    name: "crypto_mev_research",
    slot: 0x30,
    default_domain: 0x31,
    default_scalar: 0x01,
    mountain_range: "adversarial_flow_range",
};

const IBMII_ETHERNET: WorkloadProfile = WorkloadProfile {
    name: "ibmii_ethernet",
    slot: 0x40,
    default_domain: 0x0D,
    default_scalar: 0x01,
    mountain_range: "legacy_shell_range",
};

const ISO_PREPASS: WorkloadProfile = WorkloadProfile {
    name: "iso_prepass",
    slot: 0x50,
    default_domain: 0x51,
    default_scalar: 0x01,
    mountain_range: "symbol_basis_range",
};

fn parse_byte(value: &str) -> Result<u8, String> {
    let parsed = if let Some(hex) = value
        .strip_prefix("0x")
        .or_else(|| value.strip_prefix("0X"))
    {
        u16::from_str_radix(hex, 16).map_err(|err| err.to_string())?
    } else {
        value.parse::<u16>().map_err(|err| err.to_string())?
    };
    u8::try_from(parsed).map_err(|_| "--scalar must fit in one byte".to_string())
}

fn select_profile(workload: &str, pressure: u8) -> WorkloadProfile {
    if pressure >= 90 && workload != "recovery" {
        return RECOVERY;
    }
    match workload {
        "recovery" => RECOVERY,
        "angry_sphinx" => ANGRY_SPHINX,
        "standards_registry" => STANDARDS_REGISTRY,
        "crypto_mev_research" => CRYPTO_MEV_RESEARCH,
        "ibmii_ethernet" => IBMII_ETHERNET,
        "iso_prepass" => ISO_PREPASS,
        _ => ANGRY_SPHINX,
    }
}

fn avmr_signal(shell: &str, workload: &str, pressure: u8) -> u8 {
    let text = format!("{shell}:{workload}");
    let shell_mass = text
        .as_bytes()
        .iter()
        .enumerate()
        .fold(0u16, |acc, (idx, byte)| {
            acc.wrapping_add(((idx as u16) + 1) * (*byte as u16)) & 0xFF
        });
    let pressure_penalty = u16::from(pressure).saturating_mul(2).min(200);
    let signal = i32::from(shell_mass) - i32::from(pressure_penalty) + 64;
    signal.clamp(0, 255) as u8
}

fn s3c_partial_gate(slot: u8, domain: u8, scalar: u8, budget: u8) -> (bool, u8) {
    let n = ((slot as u32) << 8) | ((domain as u32) << 4) | u32::from(scalar & 0x0F);
    let k = (n as f64).sqrt() as u32;
    let a = n - k * k;
    let b = (k + 1) * (k + 1) - n;
    let mass = a * b;
    let width = (a + b + 1).max(1);
    let echo = u32::from((slot ^ domain).wrapping_add(scalar));
    let contact_a = (a + echo) % 3 != 0;
    let contact_c = (b + echo) % 5 != 0;
    let score = (mass % 256) as i32 + i32::from(budget) - width as i32;
    (
        contact_a && contact_c && score > 0,
        score.clamp(0, 255) as u8,
    )
}

fn ammr_allows(profile: WorkloadProfile, signal: u8, pressure: u8, s3c_emit: bool) -> bool {
    if profile.name == "angry_sphinx" || profile.name == "recovery" {
        return true;
    }
    if pressure >= 90 {
        return false;
    }
    signal >= 24 && s3c_emit
}

fn make_token(
    shell: &str,
    workload: &str,
    pressure: u8,
    scalar: Option<u8>,
    partial_budget: u8,
) -> OmniToken {
    let mut profile = select_profile(workload, pressure);
    let mut signal = avmr_signal(shell, profile.name, pressure);
    let mut candidate_scalar = scalar.unwrap_or(profile.default_scalar);
    let (mut s3c_emit, mut s3c_score) = s3c_partial_gate(
        profile.slot,
        profile.default_domain,
        candidate_scalar,
        partial_budget,
    );
    let mut safe = ammr_allows(profile, signal, pressure, s3c_emit);

    if !safe && profile.name != "recovery" {
        profile = if pressure >= 90 {
            RECOVERY
        } else {
            ANGRY_SPHINX
        };
        signal = avmr_signal(shell, profile.name, pressure);
        candidate_scalar = scalar.unwrap_or(profile.default_scalar);
        (s3c_emit, s3c_score) = s3c_partial_gate(
            profile.slot,
            profile.default_domain,
            candidate_scalar,
            partial_budget,
        );
        safe = ammr_allows(profile, signal, pressure, s3c_emit);
    }

    OmniToken {
        shell: shell.to_string(),
        workload: profile.name,
        mountain_range: profile.mountain_range,
        slot: profile.slot,
        domain: profile.default_domain,
        scalar: candidate_scalar,
        avmr_signal: signal,
        s3c_emit,
        s3c_score,
        ammr_safe: safe,
    }
}

fn admit(token: &OmniToken) -> &'static str {
    match (token.slot, token.domain, token.scalar) {
        (0x01, 0x0D, 0x01) => "recover",
        (0x02, 0x0F, 0x01) => "angry_sphinx_challenge",
        (0x20, 0x10, 0x01) => "index_standard_surface",
        (0x20, 0x10, 0x02) => "refresh_registry_pointer",
        (0x30, 0x31, 0x01) => "classify_mempool_surface",
        (0x30, 0x31, 0x02) => "route_mev_research_candidate",
        (0x40, 0x0D, 0x01) => "recover_from_ethernet_shell",
        (0x50, 0x51, 0x01) => "apply_iso_symbol_basis",
        _ => "refuse",
    }
}

fn event(token: &OmniToken, action: &str) -> Value {
    json!({
        "v": "hs-jsonl-0.1",
        "id": format!("omni-lut:{}:0x{:02X}:0x{:02X}", token.workload, token.slot, token.scalar),
        "op": if action.starts_with("recover") { "recover" } else { "route" },
        "surface": {
            "class": "node",
            "kind": "omnisurface.dynamic_lut",
            "caps": ["recover", "route", "attest"]
        },
        "gcl": {
            "admission": if action != "refuse" { "admitted" } else { "refused" },
            "capability_tier": "T1_8kb",
            "invariant": "workload_slot_before_lut_expansion",
            "refusal_code": if action != "refuse" { "none" } else { "op_not_supported" }
        },
        "omni": {
            "shell": token.shell,
            "workload_profile": token.workload,
            "mountain_range": token.mountain_range,
            "lut_slot": format!("0x{:02X}", token.slot),
            "domain": format!("0x{:02X}", token.domain),
            "scalar": format!("0x{:02X}", token.scalar),
            "avmr_signal": token.avmr_signal,
            "s3c_emit": token.s3c_emit,
            "s3c_score": token.s3c_score,
            "ammr_safe": token.ammr_safe,
            "angry_sphinx_default": token.workload == "angry_sphinx",
            "action": action
        },
        "privacy": {
            "tier": "internal",
            "retention": "cache",
            "export": "deny",
            "redaction": "none"
        }
    })
}

fn run_cases(
    cases: Vec<(&str, &str, u8, Option<u8>)>,
    emit_jsonl: bool,
    partial_budget: u8,
) -> i32 {
    let mut refused = 0;
    for (shell, workload, pressure, scalar) in cases {
        let token = make_token(shell, workload, pressure, scalar, partial_budget);
        let action = admit(&token);
        refused += i32::from(action == "refuse");
        if emit_jsonl {
            println!(
                "{}",
                serde_json::to_string(&event(&token, action)).expect("json event")
            );
        } else {
            let raw = format!("{:02x}{:02x}{:02x}", token.slot, token.domain, token.scalar);
            println!(
                "shell={} workload={} mountain={} signal={} s3c_emit={} s3c_score={} ammr_safe={} slot=0x{:02X} domain=0x{:02X} scalar=0x{:02X} bytes={} action={}",
                token.shell,
                token.workload,
                token.mountain_range,
                token.avmr_signal,
                i32::from(token.s3c_emit),
                token.s3c_score,
                i32::from(token.ammr_safe),
                token.slot,
                token.domain,
                token.scalar,
                raw,
                action
            );
        }
    }
    i32::from(refused > 0)
}

fn main() {
    let args = Args::parse();
    let code = if args.demo {
        run_cases(
            vec![
                ("unknown-shell", "unknown", 10, None),
                ("ethernet", "ibmii_ethernet", 20, None),
                ("ipv923u", "standards_registry", 25, None),
                ("onion", "crypto_mev_research", 40, None),
                ("serial", "iso_prepass", 15, None),
                ("tcp", "crypto_mev_research", 95, None),
            ],
            args.jsonl,
            args.partial_budget,
        )
    } else {
        let token = make_token(
            &args.shell,
            &args.workload,
            args.pressure,
            args.scalar,
            args.partial_budget,
        );
        let action = admit(&token);
        if args.jsonl {
            println!(
                "{}",
                serde_json::to_string(&event(&token, action)).expect("json event")
            );
        } else {
            let raw = format!("{:02x}{:02x}{:02x}", token.slot, token.domain, token.scalar);
            println!(
                "shell={} workload={} mountain={} signal={} s3c_emit={} s3c_score={} ammr_safe={} slot=0x{:02X} domain=0x{:02X} scalar=0x{:02X} bytes={} action={}",
                token.shell,
                token.workload,
                token.mountain_range,
                token.avmr_signal,
                i32::from(token.s3c_emit),
                token.s3c_score,
                i32::from(token.ammr_safe),
                token.slot,
                token.domain,
                token.scalar,
                raw,
                action
            );
        }
        i32::from(action == "refuse")
    };
    std::process::exit(code);
}
