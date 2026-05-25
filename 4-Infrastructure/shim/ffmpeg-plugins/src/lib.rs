pub mod avfilters;
#[cfg(feature = "gpu")]
pub mod gpu;

use std::ffi::CString;
use std::os::raw::c_char;

pub const AVMEDIA_TYPE_AUDIO: i32 = 1;
pub const AV_SAMPLE_FMT_S16: i32 = 1;
pub const AV_SAMPLE_FMT_FLTP: i32 = 8;
pub const AV_OPT_TYPE_INT: i32 = 0;
pub const AV_OPT_TYPE_STRING: i32 = 3;

#[repr(C)]
pub struct AVFilterPad {
    pub name: *const c_char,
    pub media_type: i32,
}

#[repr(C)]
pub struct AVFilter {
    pub name: *const c_char,
    pub description: *const c_char,
    _reserved: [u8; 64],
}

static FILTERS: &[(&str, &str)] = &[
    ("s3c", "S3C shell decomposition — manifold handles from PCM audio"),
    ("waveprobe", "Waveprobe QUBO projection — attractor ID from audio frames"),
    ("rgflow", "RGFlow — coarse-graining persistence detector"),
];

/// Returns a JSON manifest of available filters.
#[no_mangle]
pub extern "C" fn ffmpeg_plugins_manifest() -> *mut c_char {
    let manifest = serde_json::json!({
        "plugin": "research-stack-ffmpeg-plugins",
        "version": "0.1.0",
        "filters": FILTERS.iter().map(|(name, desc)| {
            serde_json::json!({"name": name, "description": desc})
        }).collect::<Vec<_>>(),
    });
    CString::new(manifest.to_string())
        .unwrap_or_default()
        .into_raw()
}

/// Free a string returned by the plugin.
#[no_mangle]
pub extern "C" fn ffmpeg_plugins_free_string(s: *mut c_char) {
    if !s.is_null() {
        unsafe { let _ = CString::from_raw(s); }
    }
}

/// Process S3C on a buffer of i16 samples. Returns JSON with per-frame stats.
#[no_mangle]
pub extern "C" fn s3c_process(
    samples: *const i16,
    count: i32,
    out_json: *mut *mut c_char,
) -> i32 {
    if samples.is_null() || count <= 0 {
        return -1;
    }
    let buf = unsafe { std::slice::from_raw_parts(samples, count as usize) };
    let handles = avfilters::s3c::process_chunk(buf);
    let stats = avfilters::s3c::aggregate(&handles);

    let result = serde_json::json!({
        "n": stats.n_samples,
        "throats": stats.n_throats,
        "avg_j": stats.avg_j_score,
        "max_j": stats.max_j_score,
        "min_j": stats.min_j_score,
        "emission_ratio": stats.emission_ratio,
        "throat_positions": stats.throat_positions.iter().take(20).cloned().collect::<Vec<_>>(),
    });

    let json_str = CString::new(result.to_string()).unwrap_or_default();
    unsafe { *out_json = json_str.into_raw(); }
    0
}

#[cfg(test)]
mod tests {
    use crate::avfilters::s3c;

    #[test]
    fn test_s3c_decompose_zero() {
        let h = s3c::decompose_cpu(0);
        assert_eq!(h.k, 0);
        assert_eq!(h.a, 0);
        assert_eq!(h.b, 1);
        assert_eq!(h.j_score, 1);
        assert_eq!(h.throat, 0);
    }

    #[test]
    fn test_s3c_decompose_one() {
        let h = s3c::decompose_cpu(1);
        assert_eq!(h.k, 1);
        assert_eq!(h.a, 0);
        assert_eq!(h.b, 3);
        assert_eq!(h.j_score, 4);
    }

    #[test]
    fn test_s3c_decompose_perfect_square() {
        let h = s3c::decompose_cpu(144);
        assert_eq!(h.k, 12);
        assert_eq!(h.a, 0);
        assert_eq!(h.b, 25);
    }

    #[test]
    fn test_s3c_decompose_negative() {
        let pos = s3c::decompose_cpu(128);
        let neg = s3c::decompose_cpu(-128);
        assert_eq!(pos.j_score, neg.j_score);
    }

    #[test]
    fn test_s3c_process_chunk() {
        let samples: Vec<i16> = vec![0, 1, 16, 100, 255, 1000, 32767];
        let handles = s3c::process_chunk(&samples);
        assert_eq!(handles.len(), 7);
        let stats = s3c::aggregate(&handles);
        assert_eq!(stats.n_samples, 7);
        assert!(stats.avg_j_score > 0.0);
    }

    #[test]
    fn test_ffi_s3c_process() {
        let samples: Vec<i16> = (0..100).collect();
        let mut out: *mut std::os::raw::c_char = std::ptr::null_mut();
        let rc = crate::s3c_process(samples.as_ptr(), samples.len() as i32, &mut out);
        assert_eq!(rc, 0);
        assert!(!out.is_null());
        let result = unsafe { std::ffi::CStr::from_ptr(out) }.to_str().unwrap();
        assert!(result.contains("n"));
        assert!(result.contains("throats"));
        crate::ffmpeg_plugins_free_string(out);
    }
}
