use std::env;
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

const DEFAULT_SHM_PATH: &str = "/dev/shm/erdos_surface_loop.bin";
const MAGIC: &[u8; 4] = b"EDS1";

#[derive(Debug)]
struct Config {
    repo_root: PathBuf,
    shm_path: PathBuf,
    out_dir: PathBuf,
    famm_packages_path: PathBuf,
    encode: bool,
}

#[derive(Debug)]
struct Probe {
    name: &'static str,
    available: bool,
    summary: String,
}

fn main() -> io::Result<()> {
    let config = Config::from_args()?;
    fs::create_dir_all(&config.out_dir)?;

    let lean_json = run_lean_surface(&config.repo_root)?;
    let famm_packages_json = fs::read_to_string(&config.famm_packages_path)
        .unwrap_or_else(|_| "{\"schema\":\"missing_famm_packages\",\"packages\":[]}".to_string());
    let counts = parse_count_values(&lean_json);
    if counts.is_empty() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "Lean surface emitted no count_values array",
        ));
    }

    let wgsl = render_wgsl(counts.len());
    let wgsl_path = config.out_dir.join("erdos_counts_reduce.wgsl");
    fs::write(&wgsl_path, wgsl)?;

    let raw_frame_path = config.out_dir.join("erdos_counts_rgba_16x16.raw");
    write_count_frame(&raw_frame_path, &counts)?;
    let raw_pcm_path = config.out_dir.join("erdos_dsp_surface_s16le.raw");
    write_dsp_pcm(&raw_pcm_path, &counts)?;

    let mut encoded = Vec::new();
    let h264_path = config.out_dir.join("erdos_counts_h264.mp4");
    let h265_path = config.out_dir.join("erdos_counts_h265.mp4");
    let flac_path = config.out_dir.join("erdos_dsp_surface.flac");
    if config.encode {
        encoded.push(encode_frame(&raw_frame_path, &h264_path, "libx264"));
        encoded.push(encode_frame(&raw_frame_path, &h265_path, "libx265"));
        encoded.push(encode_flac(&raw_pcm_path, &flac_path));
    }

    let probes = vec![
        probe_vulkan(),
        probe_ffmpeg_codec("h264_nvenc"),
        probe_ffmpeg_codec("hevc_nvenc"),
        probe_ffmpeg_codec("h264_vulkan"),
        probe_ffmpeg_codec("hevc_vulkan"),
        probe_audio_playback(),
        probe_audio_capture(),
    ];

    write_shm(&config.shm_path, &lean_json, &counts)?;

    let divider_manifest_path = config.out_dir.join("erdos_surface_dividers.json");
    let divider_manifest = render_surface_dividers(
        &config,
        &famm_packages_json,
        &counts,
        &wgsl_path,
        &raw_frame_path,
        &raw_pcm_path,
        &h264_path,
        &h265_path,
        &flac_path,
    );
    fs::write(&divider_manifest_path, divider_manifest.as_bytes())?;

    let report = render_report(
        &config,
        &lean_json,
        &famm_packages_json,
        &counts,
        &probes,
        &encoded,
        &wgsl_path,
        &raw_frame_path,
        &raw_pcm_path,
        &flac_path,
        &divider_manifest_path,
        &divider_manifest,
    );
    let report_path = config
        .out_dir
        .join("erdos_surface_orchestrator_report.json");
    fs::write(&report_path, report.as_bytes())?;

    println!("{}", report);
    eprintln!("wrote {}", report_path.display());
    Ok(())
}

impl Config {
    fn from_args() -> io::Result<Self> {
        let mut repo_root = env::current_dir()?;
        let mut shm_path = PathBuf::from(DEFAULT_SHM_PATH);
        let mut famm_packages_path: Option<PathBuf> = None;
        let mut encode = true;

        let mut args = env::args().skip(1);
        while let Some(arg) = args.next() {
            match arg.as_str() {
                "--repo-root" => {
                    if let Some(value) = args.next() {
                        repo_root = PathBuf::from(value);
                    }
                }
                "--shm-path" => {
                    if let Some(value) = args.next() {
                        shm_path = PathBuf::from(value);
                    }
                }
                "--famm-packages" => {
                    if let Some(value) = args.next() {
                        famm_packages_path = Some(PathBuf::from(value));
                    }
                }
                "--no-encode" => encode = false,
                _ => {}
            }
        }

        let out_dir = repo_root.join("4-Infrastructure/shim/erdos_surface_orchestrator/out");
        let famm_packages_path = famm_packages_path.unwrap_or_else(|| {
            repo_root.join("4-Infrastructure/shim/investigate_erdos_dag_famm_packages.json")
        });
        Ok(Self {
            repo_root,
            shm_path,
            out_dir,
            famm_packages_path,
            encode,
        })
    }
}

fn run_lean_surface(repo_root: &Path) -> io::Result<String> {
    let lean_root = repo_root.join("0-Core-Formalism/lean/Semantics");
    let output = Command::new("lake")
        .args([
            "env",
            "lean",
            "--run",
            "Semantics/Testing/ErdosSurface.lean",
        ])
        .current_dir(&lean_root)
        .output()?;

    if !output.status.success() {
        return Err(io::Error::new(
            io::ErrorKind::Other,
            format!(
                "Lean surface failed: {}",
                String::from_utf8_lossy(&output.stderr)
            ),
        ));
    }

    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

fn parse_count_values(json: &str) -> Vec<u32> {
    let marker = "\"count_values\":[";
    let Some(start) = json.find(marker).map(|idx| idx + marker.len()) else {
        return Vec::new();
    };
    let Some(end) = json[start..].find(']').map(|idx| start + idx) else {
        return Vec::new();
    };
    json[start..end]
        .split(',')
        .filter_map(|part| part.trim().parse::<u32>().ok())
        .collect()
}

fn render_wgsl(count_len: usize) -> String {
    format!(
        r#"struct Counts {{
  values: array<u32, {count_len}>,
}};

struct Output {{
  total: atomic<u32>,
  max_value: atomic<u32>,
}};

@group(0) @binding(0) var<storage, read> counts: Counts;
@group(0) @binding(1) var<storage, read_write> output: Output;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {{
  let i = gid.x;
  if (i >= {count_len}u) {{
    return;
  }}
  let v = counts.values[i];
  atomicAdd(&output.total, v);
  loop {{
    let old = atomicLoad(&output.max_value);
    if (v <= old) {{
      break;
    }}
    let exchanged = atomicCompareExchangeWeak(&output.max_value, old, v);
    if (exchanged.exchanged) {{
      break;
    }}
  }}
}}
"#
    )
}

fn write_count_frame(path: &Path, counts: &[u32]) -> io::Result<()> {
    let mut frame = vec![0u8; 16 * 16 * 4];
    for (idx, count) in counts.iter().enumerate() {
        let base = idx * 4;
        if base + 3 >= frame.len() {
            break;
        }
        let value = (*count).min(255) as u8;
        frame[base] = value;
        frame[base + 1] = value.saturating_mul(32);
        frame[base + 2] = 255u8.saturating_sub(value.saturating_mul(16));
        frame[base + 3] = 255;
    }
    fs::write(path, frame)
}

fn write_dsp_pcm(path: &Path, counts: &[u32]) -> io::Result<()> {
    let sample_rate = 48_000usize;
    let duration_samples = sample_rate / 2;
    let mut pcm = Vec::with_capacity(duration_samples * 2);
    let base_freqs = [220.0f32, 330.0, 440.0, 660.0, 880.0, 1320.0];
    for i in 0..duration_samples {
        let t = i as f32 / sample_rate as f32;
        let mut sample = 0.0f32;
        for (idx, count) in counts.iter().enumerate() {
            let freq = base_freqs[idx % base_freqs.len()] * (1.0 + (*count as f32 / 16.0));
            let amp = 0.12f32 / (idx as f32 + 1.0);
            sample += amp * (2.0 * std::f32::consts::PI * freq * t).sin();
        }
        let scaled = (sample.clamp(-0.95, 0.95) * i16::MAX as f32) as i16;
        pcm.extend_from_slice(&scaled.to_le_bytes());
    }
    fs::write(path, pcm)
}

fn encode_frame(raw_frame: &Path, out_path: &Path, encoder: &str) -> String {
    let status = Command::new("ffmpeg")
        .args([
            "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "16x16", "-r", "1", "-i",
        ])
        .arg(raw_frame)
        .args(["-frames:v", "1", "-c:v", encoder, "-pix_fmt", "yuv420p"])
        .arg(out_path)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    match status {
        Ok(s) if s.success() => format!(
            "{{\"encoder\":\"{}\",\"status\":\"ok\",\"path\":\"{}\"}}",
            encoder,
            json_escape(&out_path.display().to_string())
        ),
        Ok(s) => format!(
            "{{\"encoder\":\"{}\",\"status\":\"failed\",\"code\":{}}}",
            encoder,
            s.code().unwrap_or(-1)
        ),
        Err(err) => format!(
            "{{\"encoder\":\"{}\",\"status\":\"error\",\"error\":\"{}\"}}",
            encoder,
            json_escape(&err.to_string())
        ),
    }
}

fn encode_flac(raw_pcm: &Path, out_path: &Path) -> String {
    let status = Command::new("ffmpeg")
        .args(["-y", "-f", "s16le", "-ar", "48000", "-ac", "1", "-i"])
        .arg(raw_pcm)
        .args(["-c:a", "flac"])
        .arg(out_path)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    match status {
        Ok(s) if s.success() => format!(
            "{{\"encoder\":\"flac\",\"status\":\"ok\",\"path\":\"{}\"}}",
            json_escape(&out_path.display().to_string())
        ),
        Ok(s) => format!(
            "{{\"encoder\":\"flac\",\"status\":\"failed\",\"code\":{}}}",
            s.code().unwrap_or(-1)
        ),
        Err(err) => format!(
            "{{\"encoder\":\"flac\",\"status\":\"error\",\"error\":\"{}\"}}",
            json_escape(&err.to_string())
        ),
    }
}

fn write_shm(path: &Path, lean_json: &str, counts: &[u32]) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut file = File::create(path)?;
    file.write_all(MAGIC)?;
    file.write_all(&(lean_json.len() as u32).to_le_bytes())?;
    file.write_all(&(counts.len() as u32).to_le_bytes())?;
    file.write_all(lean_json.as_bytes())?;
    for count in counts {
        file.write_all(&count.to_le_bytes())?;
    }
    file.flush()
}

fn count_occurrences(haystack: &str, needle: &str) -> usize {
    haystack.match_indices(needle).count()
}

fn render_surface_dividers(
    config: &Config,
    famm_packages_json: &str,
    counts: &[u32],
    wgsl_path: &Path,
    raw_frame_path: &Path,
    raw_pcm_path: &Path,
    h264_path: &Path,
    h265_path: &Path,
    flac_path: &Path,
) -> String {
    let package_count =
        count_occurrences(famm_packages_json, "\"schema\":\"erdos_famm_package_v1\"")
            + count_occurrences(famm_packages_json, "\"schema\": \"erdos_famm_package_v1\"");
    let dsp_motifs = [
        "raw",
        "spectral_focus",
        "transient_edge",
        "hybrid",
        "palette_control",
        "braid_prior",
        "mode_mux_dsp",
    ];
    let dsp_motif_json = dsp_motifs
        .iter()
        .map(|motif| {
            format!(
                "{{\"motif\":\"{}\",\"package_refs\":{}}}",
                motif,
                count_occurrences(famm_packages_json, &format!("\"name\": \"{}\"", motif))
                    + count_occurrences(famm_packages_json, &format!("\"name\":\"{}\"", motif))
            )
        })
        .collect::<Vec<_>>()
        .join(",");

    let total_count: u32 = counts.iter().sum();
    let max_count = counts.iter().copied().max().unwrap_or(0);

    format!(
        "{{\"schema\":\"erdos_surface_dividers_v1\",\
\"claim_boundary\":\"dividers route data between surfaces; only Lean/CPU can promote receipts\",\
\"source_packages\":\"{}\",\
\"package_count\":{},\
\"dividers\":[\
{{\"divider\":\"cpu_lean_trust\",\"input\":\"{}\",\"output\":\"{}\",\"operation\":\"receipt classification and promotion gate\",\"trust\":\"authoritative\"}},\
{{\"divider\":\"gpu_vulkan_numeric\",\"input\":\"{}\",\"output\":\"{}\",\"operation\":\"u32 count total/max reduction\",\"trust\":\"accelerator; recheck before promotion\",\"count_total\":{},\"count_max\":{}}},\
{{\"divider\":\"h264_transport\",\"input\":\"{}\",\"output\":\"{}\",\"operation\":\"RGBA package-count frame to H.264 packet telemetry\",\"trust\":\"transport only; hash after decode\"}},\
{{\"divider\":\"h265_transport\",\"input\":\"{}\",\"output\":\"{}\",\"operation\":\"RGBA package-count frame to H.265 packet telemetry\",\"trust\":\"transport only; hash after decode\"}},\
{{\"divider\":\"flac_dsp_container\",\"input\":\"{}\",\"output\":\"{}\",\"operation\":\"S16LE DSP motif waveform to FLAC surface container\",\"trust\":\"signal transport only; hash after decode\"}},\
{{\"divider\":\"dsp_motif_router\",\"input\":\"{}\",\"output\":\"/dev/snd or PipeWire DSP workload\",\"operation\":\"map package motifs to spectral/transient/hybrid/palette/braid/mode-mux surfaces\",\"trust\":\"signal lane only\",\"motifs\":[{}]}}\
]}}",
        json_escape(&config.famm_packages_path.display().to_string()),
        package_count,
        json_escape(&config.famm_packages_path.display().to_string()),
        json_escape(&config.shm_path.display().to_string()),
        json_escape(&config.shm_path.display().to_string()),
        json_escape(&wgsl_path.display().to_string()),
        total_count,
        max_count,
        json_escape(&raw_frame_path.display().to_string()),
        json_escape(&h264_path.display().to_string()),
        json_escape(&raw_frame_path.display().to_string()),
        json_escape(&h265_path.display().to_string()),
        json_escape(&raw_pcm_path.display().to_string()),
        json_escape(&flac_path.display().to_string()),
        json_escape(&config.famm_packages_path.display().to_string()),
        dsp_motif_json
    )
}

fn probe_vulkan() -> Probe {
    match Command::new("vulkaninfo").arg("--summary").output() {
        Ok(output) if output.status.success() => {
            let text = String::from_utf8_lossy(&output.stdout);
            let summary = text
                .lines()
                .find(|line| line.trim_start().starts_with("deviceName"))
                .unwrap_or("vulkan device present")
                .trim()
                .to_string();
            Probe {
                name: "vulkan",
                available: true,
                summary,
            }
        }
        Ok(_) => Probe {
            name: "vulkan",
            available: false,
            summary: "vulkaninfo returned nonzero".to_string(),
        },
        Err(err) => Probe {
            name: "vulkan",
            available: false,
            summary: err.to_string(),
        },
    }
}

fn probe_ffmpeg_codec(codec: &'static str) -> Probe {
    match Command::new("ffmpeg")
        .args(["-hide_banner", "-encoders"])
        .output()
    {
        Ok(output) if output.status.success() => {
            let text = String::from_utf8_lossy(&output.stdout);
            let available = text.contains(codec);
            Probe {
                name: codec,
                available,
                summary: if available {
                    "encoder listed by ffmpeg".to_string()
                } else {
                    "encoder not listed by ffmpeg".to_string()
                },
            }
        }
        Ok(_) => Probe {
            name: codec,
            available: false,
            summary: "ffmpeg -encoders returned nonzero".to_string(),
        },
        Err(err) => Probe {
            name: codec,
            available: false,
            summary: err.to_string(),
        },
    }
}

fn probe_audio_playback() -> Probe {
    probe_command("audio_playback", "aplay", &["-l"])
}

fn probe_audio_capture() -> Probe {
    probe_command("audio_capture", "arecord", &["-l"])
}

fn probe_command(name: &'static str, cmd: &str, args: &[&str]) -> Probe {
    match Command::new(cmd).args(args).output() {
        Ok(output) if output.status.success() => {
            let text = String::from_utf8_lossy(&output.stdout);
            let summary = text.lines().next().unwrap_or("available").to_string();
            Probe {
                name,
                available: true,
                summary,
            }
        }
        Ok(_) => Probe {
            name,
            available: false,
            summary: format!("{} returned nonzero", cmd),
        },
        Err(err) => Probe {
            name,
            available: false,
            summary: err.to_string(),
        },
    }
}

fn render_report(
    config: &Config,
    lean_json: &str,
    famm_packages_json: &str,
    counts: &[u32],
    probes: &[Probe],
    encoded: &[String],
    wgsl_path: &Path,
    raw_frame_path: &Path,
    raw_pcm_path: &Path,
    flac_path: &Path,
    divider_manifest_path: &Path,
    divider_manifest: &str,
) -> String {
    let probe_json = probes
        .iter()
        .map(|p| {
            format!(
                "{{\"name\":\"{}\",\"available\":{},\"summary\":\"{}\"}}",
                p.name,
                p.available,
                json_escape(&p.summary)
            )
        })
        .collect::<Vec<_>>()
        .join(",");

    format!(
        "{{\"schema\":\"erdos_surface_orchestrator_v1\",\
\"claim_boundary\":\"Lean owns receipts; Vulkan/codec/audio lanes accelerate or transport only\",\
\"shm_path\":\"{}\",\
\"famm_packages_path\":\"{}\",\
\"famm_package_count\":{},\
\"lean_receipt\":{},\
\"counts\":[{}],\
\"wgsl_shader\":\"{}\",\
\"raw_frame\":\"{}\",\
\"raw_pcm\":\"{}\",\
\"flac_container\":\"{}\",\
\"encoded\":[{}],\
\"surface_dividers_path\":\"{}\",\
\"surface_dividers\":{},\
\"probes\":[{}]}}",
        json_escape(&config.shm_path.display().to_string()),
        json_escape(&config.famm_packages_path.display().to_string()),
        count_occurrences(famm_packages_json, "\"schema\":\"erdos_famm_package_v1\"")
            + count_occurrences(famm_packages_json, "\"schema\": \"erdos_famm_package_v1\""),
        lean_json,
        counts
            .iter()
            .map(u32::to_string)
            .collect::<Vec<_>>()
            .join(","),
        json_escape(&wgsl_path.display().to_string()),
        json_escape(&raw_frame_path.display().to_string()),
        json_escape(&raw_pcm_path.display().to_string()),
        json_escape(&flac_path.display().to_string()),
        encoded.join(","),
        json_escape(&divider_manifest_path.display().to_string()),
        divider_manifest,
        probe_json
    )
}

fn json_escape(s: &str) -> String {
    s.replace('\\', "\\\\").replace('"', "\\\"")
}
