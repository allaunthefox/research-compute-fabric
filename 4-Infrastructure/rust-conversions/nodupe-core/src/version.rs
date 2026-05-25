//! Version management for the NoDupeLabs application.
//!
//! Provides version-information types, parsing, compatibility checks, and
//! system-information helpers.

use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

// ---------------------------------------------------------------------------
// VersionInfo
// ---------------------------------------------------------------------------

/// Represents a structured application version.
///
/// Mirrors Python's `VersionInfo(NamedTuple)` with fields `major`, `minor`,
/// `micro`, `releaselevel`, and `serial`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VersionInfo {
    /// Major version number.
    pub major: u32,
    /// Minor version number.
    pub minor: u32,
    /// Micro (patch) version number.
    pub micro: u32,
    /// Release level — e.g. `"final"`, `"alpha"`, `"beta"`, `"candidate"`.
    #[serde(default)]
    pub releaselevel: String,
    /// Serial number for pre-release builds.
    #[serde(default)]
    pub serial: u32,
}

impl VersionInfo {
    /// Create a new `VersionInfo` (release level defaults to final).
    pub const fn new(major: u32, minor: u32, micro: u32) -> Self {
        Self {
            major,
            minor,
            micro,
            releaselevel: String::new(),
            serial: 0,
        }
    }

    /// Create a `VersionInfo` with a release level and serial.
    pub fn with_release(
        major: u32,
        minor: u32,
        micro: u32,
        releaselevel: impl Into<String>,
        serial: u32,
    ) -> Self {
        Self {
            major,
            minor,
            micro,
            releaselevel: releaselevel.into(),
            serial,
        }
    }

    /// Returns `true` when the release level is `"final"` (or empty).
    pub fn is_final(&self) -> bool {
        self.releaselevel.is_empty() || self.releaselevel == "final"
    }

    /// Format as a short version string (e.g. `"1.0.0"`).
    pub fn to_version_string(&self) -> String {
        let base = format!("{}.{}.{}", self.major, self.minor, self.micro);
        if self.is_final() {
            base
        } else {
            let tag = match self.releaselevel.as_str() {
                "alpha" => "a",
                "beta" => "b",
                "candidate" | "rc" => "rc",
                other => other,
            };
            format!("{base}{tag}{}", self.serial)
        }
    }

    /// Format as a human-readable version string (e.g. `"v1.0.0"`, `"v1.0.0 Beta 1"`).
    pub fn to_pretty_string(&self) -> String {
        let base = format!("v{}.{}.{}", self.major, self.minor, self.micro);
        if self.is_final() {
            base
        } else {
            let label = match self.releaselevel.as_str() {
                "alpha" => "Alpha",
                "beta" => "Beta",
                "candidate" | "rc" => "RC",
                other => other,
            };
            format!("{base} {label} {}", self.serial)
        }
    }
}

impl Default for VersionInfo {
    fn default() -> Self {
        Self::new(1, 0, 0)
    }
}

impl fmt::Display for VersionInfo {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_version_string())
    }
}

/// Error returned when a version string cannot be parsed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseVersionError {
    input: String,
    details: String,
}

impl fmt::Display for ParseVersionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "failed to parse version string {:?}: {}",
            self.input, self.details
        )
    }
}

impl std::error::Error for ParseVersionError {}

impl FromStr for VersionInfo {
    type Err = ParseVersionError;

    /// Parse a version string such as `"1.0.0"`, `"1.0.0a1"`, `"1.0.0b2"`,
    /// or `"1.0.0rc3"` into a `VersionInfo`.
    fn from_str(version_str: &str) -> Result<Self, Self::Err> {
        let err_bad = |details: &str| -> Self::Err {
            ParseVersionError {
                input: version_str.to_owned(),
                details: details.to_owned(),
            }
        };

        let parts: Vec<&str> = version_str.split('.').collect();
        if parts.len() < 3 {
            return Err(err_bad("expected at least major.minor.micro"));
        }

        let major: u32 = parts[0]
            .parse()
            .map_err(|_| err_bad("major is not a valid integer"))?;
        let minor: u32 = parts[1]
            .parse()
            .map_err(|_| err_bad("minor is not a valid integer"))?;

        // The micro part may contain pre-release suffixes like "0a1".
        let micro_raw = parts[2];
        let (micro, releaselevel, serial) = if let Ok(m) = micro_raw.parse::<u32>() {
            // Plain micro, check parts[3..] for pre-release
            if parts.len() > 3 {
                let extra: String = parts[3..].join(".");
                parse_pre_release(&extra, m)?
            } else {
                (m, String::new(), 0)
            }
        } else {
            // Suffix embedded in micro part, e.g. "1.0.0a1"
            parse_embedded_pre_release(micro_raw)?
        };

        Ok(Self {
            major,
            minor,
            micro,
            releaselevel,
            serial,
        })
    }
}

/// Parse pre-release info from a standalone suffix like `"a1"`, `"b2"`, `"rc3"`.
fn parse_pre_release(s: &str, micro: u32) -> Result<(u32, String, u32), ParseVersionError> {
    let err_bad = |d: &str| -> ParseVersionError {
        ParseVersionError {
            input: s.to_owned(),
            details: d.to_owned(),
        }
    };

    if let Some(tail) = s.strip_prefix('a') {
        let serial: u32 = tail.parse().map_err(|_| err_bad("invalid alpha serial"))?;
        Ok((micro, "alpha".into(), serial))
    } else if let Some(tail) = s.strip_prefix('b') {
        let serial: u32 = tail.parse().map_err(|_| err_bad("invalid beta serial"))?;
        Ok((micro, "beta".into(), serial))
    } else if let Some(tail) = s.strip_prefix("rc") {
        let serial: u32 = tail
            .parse()
            .map_err(|_| err_bad("invalid release candidate serial"))?;
        Ok((micro, "candidate".into(), serial))
    } else if s == "final" || s.is_empty() {
        Ok((micro, String::new(), 0))
    } else {
        Err(err_bad("unknown pre-release tag"))
    }
}

/// Parse pre-release info embedded in the micro part, e.g. `"0a1"` -> (0, "alpha", 1).
fn parse_embedded_pre_release(micro_raw: &str) -> Result<(u32, String, u32), ParseVersionError> {
    let err_bad = |d: &str| -> ParseVersionError {
        ParseVersionError {
            input: micro_raw.to_owned(),
            details: d.to_owned(),
        }
    };

    for (prefix, level) in &[("a", "alpha"), ("b", "beta"), ("rc", "candidate")] {
        if let Some((num_str, serial_str)) = micro_raw.split_once(prefix) {
            let micro: u32 = num_str
                .parse()
                .map_err(|_| err_bad("invalid micro in embedded pre-release"))?;
            let serial: u32 = serial_str
                .parse()
                .map_err(|_| err_bad("invalid serial in embedded pre-release"))?;
            return Ok((micro, (*level).into(), serial));
        }
    }

    Err(err_bad("could not parse embedded pre-release tag"))
}

// ---------------------------------------------------------------------------
// Application version
// ---------------------------------------------------------------------------

/// Current application version.
pub const APP_VERSION: VersionInfo = VersionInfo::new(1, 0, 0);

/// Current application version as a string.
pub const APP_VERSION_STR: &str = "1.0.0";

/// Get the current application version string.
pub fn get_version() -> String {
    APP_VERSION.to_string()
}

/// Get detailed version information.
pub fn get_version_info() -> &'static VersionInfo {
    &APP_VERSION
}

// ---------------------------------------------------------------------------
// Compatibility helpers
// ---------------------------------------------------------------------------

/// Minimum supported Rust version as a (major, minor) tuple.
pub const RUST_MIN_VERSION: (u32, u32) = (1, 86);

/// Parse a dotted version string into a `Vec<u32>` of components.
pub fn parse_version_tuple(version_str: &str) -> Option<Vec<u32>> {
    version_str
        .split('.')
        .map(|s| s.parse::<u32>().ok())
        .collect::<Option<Vec<_>>>()
}

/// Compare two dotted version strings; returns `true` if `version >= min`.
pub fn is_compatible_version(version: &str, min_version: &str) -> bool {
    let v = parse_version_tuple(version);
    let m = parse_version_tuple(min_version);
    match (v, m) {
        (Some(mut v), Some(mut m)) => {
            // Pad to at least 3 components.
            while v.len() < 3 {
                v.push(0);
            }
            while m.len() < 3 {
                m.push(0);
            }
            // Compare element-wise.
            for i in 0..3 {
                match v[i].cmp(&m[i]) {
                    std::cmp::Ordering::Less => return false,
                    std::cmp::Ordering::Greater => return true,
                    std::cmp::Ordering::Equal => {}
                }
            }
            true
        }
        _ => false,
    }
}

// ---------------------------------------------------------------------------
// System info
// ---------------------------------------------------------------------------

/// Information about the runtime environment.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    /// Application version string.
    pub app_version: String,
    /// Application version details.
    pub app_version_info: VersionInfo,
    /// Operating system name.
    pub os: String,
    /// OS family (unix, windows, etc.).
    pub os_family: String,
    /// Machine architecture.
    pub arch: String,
}

impl SystemInfo {
    /// Gather system information at runtime.
    pub fn collect() -> Self {
        Self {
            app_version: get_version(),
            app_version_info: APP_VERSION.clone(),
            os: std::env::consts::OS.to_owned(),
            os_family: if cfg!(unix) {
                "unix"
            } else if cfg!(windows) {
                "windows"
            } else {
                "other"
            }
            .to_owned(),
            arch: std::env::consts::ARCH.to_owned(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ------------------------------------------------------------------
    // VersionInfo construction
    // ------------------------------------------------------------------

    #[test]
    fn version_info_default() {
        let v = VersionInfo::default();
        assert_eq!(v.major, 1);
        assert_eq!(v.minor, 0);
        assert_eq!(v.micro, 0);
        assert!(v.is_final());
    }

    #[test]
    fn version_info_new() {
        let v = VersionInfo::new(2, 3, 1);
        assert_eq!(v.major, 2);
        assert_eq!(v.minor, 3);
        assert_eq!(v.micro, 1);
        assert!(v.is_final());
    }

    #[test]
    fn version_info_with_release() {
        let v = VersionInfo::with_release(1, 0, 0, "beta", 2);
        assert!(!v.is_final());
        assert_eq!(v.releaselevel, "beta");
        assert_eq!(v.serial, 2);
    }

    // ------------------------------------------------------------------
    // Display / to_string
    // ------------------------------------------------------------------

    #[test]
    fn display_final() {
        let v = VersionInfo::new(1, 0, 0);
        assert_eq!(v.to_string(), "1.0.0");
    }

    #[test]
    fn display_alpha() {
        let v = VersionInfo::with_release(1, 0, 0, "alpha", 1);
        assert_eq!(v.to_string(), "1.0.0a1");
    }

    #[test]
    fn display_beta() {
        let v = VersionInfo::with_release(1, 0, 0, "beta", 2);
        assert_eq!(v.to_string(), "1.0.0b2");
    }

    #[test]
    fn display_candidate() {
        let v = VersionInfo::with_release(1, 0, 0, "candidate", 3);
        assert_eq!(v.to_string(), "1.0.0rc3");
    }

    #[test]
    fn pretty_final() {
        let v = VersionInfo::new(1, 0, 0);
        assert_eq!(v.to_pretty_string(), "v1.0.0");
    }

    #[test]
    fn pretty_beta() {
        let v = VersionInfo::with_release(1, 0, 0, "beta", 2);
        assert_eq!(v.to_pretty_string(), "v1.0.0 Beta 2");
    }

    #[test]
    fn pretty_rc() {
        let v = VersionInfo::with_release(1, 0, 0, "candidate", 3);
        assert_eq!(v.to_pretty_string(), "v1.0.0 RC 3");
    }

    // ------------------------------------------------------------------
    // Parsing
    // ------------------------------------------------------------------

    #[test]
    fn parse_simple() {
        let v: VersionInfo = "1.2.3".parse().unwrap();
        assert_eq!(v.major, 1);
        assert_eq!(v.minor, 2);
        assert_eq!(v.micro, 3);
        assert!(v.is_final());
    }

    #[test]
    fn parse_alpha() {
        let v: VersionInfo = "1.0.0a1".parse().unwrap();
        assert_eq!(v.releaselevel, "alpha");
        assert_eq!(v.serial, 1);
    }

    #[test]
    fn parse_beta() {
        let v: VersionInfo = "1.0.0b2".parse().unwrap();
        assert_eq!(v.releaselevel, "beta");
        assert_eq!(v.serial, 2);
    }

    #[test]
    fn parse_rc() {
        let v: VersionInfo = "1.0.0rc3".parse().unwrap();
        assert_eq!(v.releaselevel, "candidate");
        assert_eq!(v.serial, 3);
    }

    #[test]
    fn parse_too_short() {
        let err = "1.2".parse::<VersionInfo>().unwrap_err();
        assert!(err.to_string().contains("expected at least"));
    }

    #[test]
    fn parse_invalid() {
        let err = "abc.def.ghi".parse::<VersionInfo>().unwrap_err();
        assert!(err.to_string().contains("not a valid integer"));
    }

    #[test]
    fn parse_version_tuple_ok() {
        assert_eq!(parse_version_tuple("1.2.3"), Some(vec![1, 2, 3]));
    }

    #[test]
    fn parse_version_tuple_invalid() {
        assert_eq!(parse_version_tuple("1.x.3"), None);
    }

    // ------------------------------------------------------------------
    // Compatibility
    // ------------------------------------------------------------------

    #[test]
    fn compatible_equal() {
        assert!(is_compatible_version("1.0.0", "1.0.0"));
    }

    #[test]
    fn compatible_greater() {
        assert!(is_compatible_version("2.0.0", "1.9.9"));
    }

    #[test]
    fn compatible_less() {
        assert!(!is_compatible_version("0.9.0", "1.0.0"));
    }

    #[test]
    fn compatible_padded() {
        assert!(is_compatible_version("1.0", "0.9.9"));
        assert!(!is_compatible_version("0.9", "1.0.0"));
    }

    #[test]
    fn compatible_invalid_returns_false() {
        assert!(!is_compatible_version("bad", "1.0.0"));
    }

    #[test]
    fn app_version_constants() {
        assert_eq!(get_version(), "1.0.0");
        assert_eq!(get_version_info().major, 1);
        assert_eq!(get_version_info().minor, 0);
        assert_eq!(get_version_info().micro, 0);
    }

    #[test]
    fn version_info_serialize() {
        let v = VersionInfo::new(2, 3, 4);
        let json = serde_json::to_string(&v).unwrap();
        assert!(json.contains("\"major\":2"));
        let back: VersionInfo = serde_json::from_str(&json).unwrap();
        assert_eq!(back, v);
    }

    #[test]
    fn system_info_collect() {
        let info = SystemInfo::collect();
        assert_eq!(info.app_version, "1.0.0");
        assert!(!info.os.is_empty());
        assert!(!info.arch.is_empty());
    }

    #[test]
    fn parse_serde_roundtrip() {
        let original = VersionInfo::with_release(1, 2, 3, "beta", 4);
        let json = serde_json::to_string(&original).unwrap();
        let restored: VersionInfo = serde_json::from_str(&json).unwrap();
        assert_eq!(original, restored);
    }

    #[test]
    fn parse_embedded_pre_release_alpha() {
        let v: VersionInfo = "1.2.3a4".parse().unwrap();
        assert_eq!(v.micro, 3);
        assert_eq!(v.releaselevel, "alpha");
        assert_eq!(v.serial, 4);
    }

    #[test]
    fn parse_embedded_pre_release_beta() {
        let v: VersionInfo = "1.2.3b5".parse().unwrap();
        assert_eq!(v.micro, 3);
        assert_eq!(v.releaselevel, "beta");
        assert_eq!(v.serial, 5);
    }

    #[test]
    fn parse_embedded_pre_release_rc() {
        let v: VersionInfo = "1.2.3rc6".parse().unwrap();
        assert_eq!(v.micro, 3);
        assert_eq!(v.releaselevel, "candidate");
        assert_eq!(v.serial, 6);
    }

    #[test]
    fn to_version_string_roundtrip() {
        let cases = ["1.0.0", "1.0.0a1", "1.0.0b2", "1.0.0rc3"];
        for s in &cases {
            let v: VersionInfo = s.parse().unwrap();
            assert_eq!(&v.to_version_string(), s, "roundtrip for {s}");
        }
    }

    #[test]
    fn is_final_edge_cases() {
        let v = VersionInfo::new(1, 0, 0);
        assert!(v.is_final());
        let v = VersionInfo::with_release(1, 0, 0, "", 0);
        assert!(v.is_final());
        let v = VersionInfo::with_release(1, 0, 0, "final", 0);
        assert!(v.is_final());
    }

    #[test]
    fn is_compatible_version_edge_cases() {
        assert!(is_compatible_version("1.0.0", "1.0.0"));
        assert!(is_compatible_version("1.0.1", "1.0.0"));
        assert!(!is_compatible_version("1.0.0", "1.0.1"));
        assert!(is_compatible_version("2.0.0", "1.999.999"));
        assert!(!is_compatible_version("1.999.999", "2.0.0"));
    }

    #[test]
    fn parse_version_tuple_padding() {
        assert_eq!(parse_version_tuple("1"), Some(vec![1]));
        assert_eq!(parse_version_tuple("1.2"), Some(vec![1, 2]));
        assert_eq!(parse_version_tuple(""), Some(vec![]));
    }

    #[test]
    fn version_info_clone_eq() {
        let a = VersionInfo::new(1, 2, 3);
        let b = a.clone();
        assert_eq!(a, b);
    }

    #[test]
    #[should_panic(expected = "expected at least")]
    fn parse_empty_fails() {
        let _: VersionInfo = "".parse().unwrap();
    }
}
