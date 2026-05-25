/// S3C shell decomposition — per-sample manifold transform.
/// Every PCM sample n is decomposed into shell coordinates n = k² + a,
/// giving three manifold handles and a J-score.
///
/// GPU backend via wgpu compute shader when available (concept from light repo).
/// Falls back to CPU scalar path.

use serde::Serialize;

#[derive(Debug, Clone, Copy, bytemuck::Zeroable, bytemuck::Pod)]
#[repr(C)]
pub struct S3CShaders {
    pub sample: i32,
    pub k: u32,
    pub a: u32,
    pub b: u32,
    pub j_score: u32,
    pub throat: u32,
}

impl S3CShaders {
    pub fn is_throat(&self) -> bool { self.throat != 0 }
}

/// CPU decomposition of a single sample
pub fn decompose_cpu(sample: i16) -> S3CShaders {
    let n = sample.unsigned_abs() as u32;
    let k = (n as f64).sqrt().floor() as u32;
    let k1 = k + 1;
    let a = n - k * k;
    let b = k1 * k1 - n;

    let mass = a as u64 * b as u64;
    let mirror = if a > b { a - b } else { b - a };
    let j_score = (mass + mirror as u64 + k as u64) as u32;

    S3CShaders {
        sample: sample as i32,
        k,
        a,
        b,
        j_score,
        throat: if a == b { 1 } else { 0 },
    }
}

/// Process a chunk of PCM samples on CPU
pub fn process_chunk(samples: &[i16]) -> Vec<S3CShaders> {
    samples.iter().map(|&s| decompose_cpu(s)).collect()
}

/// GPU compute shader for S3C decomposition (WGSL).
/// Inspired by light repo's photon_hash.wgsl spatial hash kernel.
/// Dispatched as: @workgroup_size(256, 1, 1), n workgroups = ceil(n_samples / 256)
pub const S3C_COMPUTE_SHADER: &str = r#"
struct S3CInput {
  sample: i32,
};

struct S3COutput {
  sample: i32,
  k: u32,
  a: u32,
  b: u32,
  j_score: u32,
  throat: u32,
};

@group(0) @binding(0) var<storage, read> input: array<S3CInput>;
@group(0) @binding(1) var<storage, read_write> output: array<S3COutput>;

@compute @workgroup_size(256, 1, 1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let id = gid.x;
  if (id >= arrayLength(&input)) { return; }
  let sample = abs(input[id].sample);
  let n = u32(sample);

  let kf = sqrt(f32(n));
  let k = u32(floor(kf));
  let k1 = k + 1u;
  let a = n - k * k;
  let b = k1 * k1 - n;

  let mass = a * b;
  let mirror = u32(abs(i32(a) - i32(b)));
  let j_score = mass + mirror + k;

  output[id].sample = i32(n);
  output[id].k = k;
  output[id].a = a;
  output[id].b = b;
  output[id].j_score = j_score;
  output[id].throat = select(0u, 1u, a == b);
}
"#;

#[derive(Debug, Clone, Serialize)]
pub struct S3CStats {
    pub n_samples: usize,
    pub n_throats: usize,
    pub avg_j_score: f64,
    pub max_j_score: u32,
    pub min_j_score: u32,
    pub emission_ratio: f64,
    pub throat_positions: Vec<usize>,
}

pub fn aggregate(handles: &[S3CShaders]) -> S3CStats {
    let n = handles.len();
    let throats: Vec<usize> = handles.iter().enumerate()
        .filter(|(_, h)| h.is_throat()).map(|(i, _)| i).collect();
    let mut total_j: u64 = 0;
    let mut max_j: u32 = 0;
    let mut min_j: u32 = u32::MAX;

    for h in handles {
        total_j += h.j_score as u64;
        max_j = max_j.max(h.j_score);
        min_j = min_j.min(h.j_score);
    }

    let avg = if n > 0 { total_j as f64 / n as f64 } else { 0.0 };
    let var: f64 = handles.iter()
        .map(|h| { let d = h.j_score as f64 - avg; d * d })
        .sum::<f64>() / n as f64;
    let threshold = (avg + var.sqrt()) as u32;
    let emitted = handles.iter().filter(|h| h.j_score > threshold).count();

    S3CStats {
        n_samples: n,
        n_throats: throats.len(),
        avg_j_score: avg,
        max_j_score: max_j,
        min_j_score: if min_j == u32::MAX { 0 } else { min_j },
        emission_ratio: if n > 0 { emitted as f64 / n as f64 } else { 0.0 },
        throat_positions: throats,
    }
}
