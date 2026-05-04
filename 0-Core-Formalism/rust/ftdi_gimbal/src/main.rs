//! FTDI Gimbal — Rust hardware-I/O boundary for Tang Nano 9K UART.
//!
//! Links against system libftdi1.so.2 (no crate dependencies).
//! Speaks JSON-lines over stdin/stdout, consumed by the unified Python shim.
//!
//! Protocol (one JSON object per line):
//!   {"method":"ftdi_open","params":{"vid":1027,"pid":24592,"interface":"B","baudrate":115200}}
//!   {"method":"ftdi_send","params":{"data":"deadbeef01020304"}}
//!   {"method":"ftdi_recv","params":{"length":8,"timeout_ms":1000}}
//!   {"method":"ftdi_close","params":{}}
//!
//! AGENTS.md compliant: no logic, no cost, no branching decisions beyond I/O.

use std::io::{self, BufRead, Write};
use std::time::{Duration, Instant};

// ---------------------------------------------------------------------------
// Opaque C types from libftdi1
// ---------------------------------------------------------------------------

#[repr(C)]
pub struct ftdi_context {
    _opaque: [u8; 0],
}

#[repr(C)]
#[derive(Clone, Copy)]
#[allow(non_camel_case_types)]
pub enum ftdi_interface {
    INTERFACE_ANY = 0,
    INTERFACE_A = 1,
    INTERFACE_B = 2,
}

#[repr(C)]
#[derive(Clone, Copy)]
#[allow(non_camel_case_types)]
pub enum ftdi_bitmode_type {
    BITMODE_RESET   = 0x00,
    BITMODE_BITBANG = 0x01,
    BITMODE_MPSSE   = 0x02,
    BITMODE_SYNCBB  = 0x04,
    BITMODE_MCU     = 0x08,
    BITMODE_OPTO    = 0x10,
    BITMODE_CBUS    = 0x20,
    BITMODE_SYNCFF  = 0x40,
}

#[repr(C)]
#[derive(Clone, Copy)]
#[allow(non_camel_case_types)]
pub enum ftdi_bits_type {
    BITS_7 = 7,
    BITS_8 = 8,
}

#[repr(C)]
#[derive(Clone, Copy)]
#[allow(non_camel_case_types)]
pub enum ftdi_stopbits_type {
    STOP_BIT_1 = 0,
    STOP_BIT_15 = 1,
    STOP_BIT_2 = 2,
}

#[repr(C)]
#[derive(Clone, Copy)]
#[allow(non_camel_case_types)]
pub enum ftdi_parity_type {
    NONE = 0,
    ODD = 1,
    EVEN = 2,
    MARK = 3,
    SPACE = 4,
}

#[link(name = "ftdi1")]
extern "C" {
    fn ftdi_new() -> *mut ftdi_context;
    fn ftdi_free(ftdi: *mut ftdi_context);
    fn ftdi_set_interface(ftdi: *mut ftdi_context, interface: ftdi_interface) -> i32;
    fn ftdi_usb_open(ftdi: *mut ftdi_context, vendor: i32, product: i32) -> i32;
    fn ftdi_usb_close(ftdi: *mut ftdi_context) -> i32;
    fn ftdi_set_baudrate(ftdi: *mut ftdi_context, baudrate: i32) -> i32;
    fn ftdi_set_line_property(
        ftdi: *mut ftdi_context,
        bits: ftdi_bits_type,
        sbit: ftdi_stopbits_type,
        parity: ftdi_parity_type,
    ) -> i32;
    fn ftdi_usb_reset(ftdi: *mut ftdi_context) -> i32;
    fn ftdi_set_bitmode(ftdi: *mut ftdi_context, bitmask: u8, mode: ftdi_bitmode_type) -> i32;
    fn ftdi_set_latency_timer(ftdi: *mut ftdi_context, latency: u8) -> i32;
    fn ftdi_usb_purge_buffers(ftdi: *mut ftdi_context) -> i32;
    fn ftdi_write_data(ftdi: *mut ftdi_context, buf: *const u8, size: i32) -> i32;
    fn ftdi_read_data(ftdi: *mut ftdi_context, buf: *mut u8, size: i32) -> i32;
}

// ---------------------------------------------------------------------------
// Minimal JSON helpers (no serde — constrained schema only)
// ---------------------------------------------------------------------------

fn extract_string_field<'a>(json: &'a str, key: &str) -> Option<&'a str> {
    let pat = format!("\"{}\"", key);
    let start = json.find(&pat)? + pat.len();
    let tail = &json[start..];
    // skip whitespace and colon
    let colon = tail.find(':')?;
    let tail = &tail[colon + 1..].trim_start();
    if !tail.starts_with('"') {
        return None;
    }
    let tail = &tail[1..];
    let end = tail.find('"')?;
    Some(&tail[..end])
}

fn extract_u64(json: &str, key: &str) -> Option<u64> {
    let pat = format!("\"{}\"", key);
    let start = json.find(&pat)? + pat.len();
    let tail = &json[start..];
    let colon = tail.find(':')?;
    let tail = &tail[colon + 1..].trim_start();
    let end = tail
        .find(|c: char| !c.is_ascii_digit())
        .unwrap_or(tail.len());
    tail[..end].parse().ok()
}

fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{:02x}", b));
    }
    s
}

fn hex_decode(hex: &str) -> Option<Vec<u8>> {
    if hex.len() % 2 != 0 {
        return None;
    }
    let mut out = Vec::with_capacity(hex.len() / 2);
    for i in (0..hex.len()).step_by(2) {
        out.push(u8::from_str_radix(&hex[i..i + 2], 16).ok()?);
    }
    Some(out)
}

// ---------------------------------------------------------------------------
// FTDI operations
// ---------------------------------------------------------------------------

unsafe fn ftdi_open(params: &str, handle: &mut *mut ftdi_context) -> String {
    if !handle.is_null() {
        return r#"{"ok":false,"error":"already open"}"#.to_string();
    }

    let vid = extract_u64(params, "vid").unwrap_or(0x0403) as i32;
    let pid = extract_u64(params, "pid").unwrap_or(0x6010) as i32;
    let baud = extract_u64(params, "baudrate").unwrap_or(115200) as i32;
    let iface_str = extract_string_field(params, "interface").unwrap_or("B");

    let iface = match iface_str {
        "A" => ftdi_interface::INTERFACE_A,
        "B" => ftdi_interface::INTERFACE_B,
        _ => ftdi_interface::INTERFACE_ANY,
    };

    let ctx = ftdi_new();
    if ctx.is_null() {
        return r#"{"ok":false,"error":"ftdi_new failed"}"#.to_string();
    }

    let mut r = ftdi_set_interface(ctx, iface);
    if r < 0 {
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_set_interface failed: {}"}}"#, r);
    }

    r = ftdi_usb_open(ctx, vid, pid);
    if r < 0 {
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_usb_open failed: {}"}}"#, r);
    }

    r = ftdi_usb_reset(ctx);
    if r < 0 {
        ftdi_usb_close(ctx);
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_usb_reset failed: {}"}}"#, r);
    }

    r = ftdi_set_bitmode(ctx, 0, ftdi_bitmode_type::BITMODE_RESET);
    if r < 0 {
        ftdi_usb_close(ctx);
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_set_bitmode failed: {}"}}"#, r);
    }

    r = ftdi_set_latency_timer(ctx, 2);
    if r < 0 {
        ftdi_usb_close(ctx);
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_set_latency_timer failed: {}"}}"#, r);
    }

    r = ftdi_set_baudrate(ctx, baud);
    if r < 0 {
        ftdi_usb_close(ctx);
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_set_baudrate failed: {}"}}"#, r);
    }

    r = ftdi_set_line_property(ctx, ftdi_bits_type::BITS_8, ftdi_stopbits_type::STOP_BIT_1, ftdi_parity_type::NONE);
    if r < 0 {
        ftdi_usb_close(ctx);
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_set_line_property failed: {}"}}"#, r);
    }

    r = ftdi_usb_purge_buffers(ctx);
    if r < 0 {
        ftdi_usb_close(ctx);
        ftdi_free(ctx);
        return format!(r#"{{"ok":false,"error":"ftdi_usb_purge_buffers failed: {}"}}"#, r);
    }

    *handle = ctx;
    r#"{"ok":true}"#.to_string()
}

unsafe fn ftdi_close(handle: &mut *mut ftdi_context) -> String {
    if handle.is_null() {
        return r#"{"ok":true}"#.to_string();
    }
    ftdi_usb_close(*handle);
    ftdi_free(*handle);
    *handle = std::ptr::null_mut();
    r#"{"ok":true}"#.to_string()
}

unsafe fn ftdi_send(params: &str, handle: &mut *mut ftdi_context) -> String {
    if handle.is_null() {
        return r#"{"ok":false,"error":"not open"}"#.to_string();
    }
    let data_hex = match extract_string_field(params, "data") {
        Some(h) => h,
        None => return r#"{"ok":false,"error":"missing data"}"#.to_string(),
    };
    let data = match hex_decode(data_hex) {
        Some(d) => d,
        None => return r#"{"ok":false,"error":"invalid hex"}"#.to_string(),
    };

    let n = ftdi_write_data(*handle, data.as_ptr(), data.len() as i32);
    if n < 0 {
        format!(r#"{{"ok":false,"error":"ftdi_write_data failed: {}"}}"#, n)
    } else {
        format!(r#"{{"ok":true,"bytes_written":{}}}"#, n)
    }
}

unsafe fn ftdi_recv(params: &str, handle: &mut *mut ftdi_context) -> String {
    if handle.is_null() {
        return r#"{"ok":false,"error":"not open"}"#.to_string();
    }
    let length = extract_u64(params, "length").unwrap_or(8) as usize;
    let timeout_ms = extract_u64(params, "timeout_ms").unwrap_or(1000);

    let mut buf = vec![0u8; length];
    let deadline = Instant::now() + Duration::from_millis(timeout_ms);
    let mut received = 0usize;

    while received < length && Instant::now() < deadline {
        let remaining = (length - received) as i32;
        let n = ftdi_read_data(*handle, buf[received..].as_mut_ptr(), remaining);
        if n > 0 {
            received += n as usize;
        } else if n < 0 {
            return format!(r#"{{"ok":false,"error":"ftdi_read_data failed: {}"}}"#, n);
        }
        if received < length {
            std::thread::sleep(Duration::from_millis(1));
        }
    }

    if received == 0 {
        return r#"{"ok":false,"error":"timeout"}"#.to_string();
    }

    buf.truncate(received);
    format!(r#"{{"ok":true,"data":"{}"}}"#, hex_encode(&buf))
}

// ---------------------------------------------------------------------------
// Dispatch
// ---------------------------------------------------------------------------

fn dispatch(line: &str, handle: &mut *mut ftdi_context) -> String {
    let method = match extract_string_field(line, "method") {
        Some(m) => m,
        None => return r#"{"ok":false,"error":"missing method"}"#.to_string(),
    };

    let params_start = line.find("\"params\"").unwrap_or(0);
    let params = if params_start > 0 {
        let tail = &line[params_start..];
        let colon = tail.find(':').unwrap_or(0);
        let tail = &tail[colon..];
        let brace = tail.find('{').unwrap_or(0);
        &tail[brace..]
    } else {
        "{}"
    };

    unsafe {
        match method {
            "ftdi_open" => ftdi_open(params, handle),
            "ftdi_close" => ftdi_close(handle),
            "ftdi_send" => ftdi_send(params, handle),
            "ftdi_recv" => ftdi_recv(params, handle),
            _ => format!(r#"{{"ok":false,"error":"unknown method: {}"}}"#, method),
        }
    }
}

// ---------------------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------------------

fn main() {
    let stdin = io::stdin();
    let mut stdout = io::stdout();
    let mut handle: *mut ftdi_context = std::ptr::null_mut();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };
        let response = dispatch(&line, &mut handle);
        if writeln!(stdout, "{}", response).is_err() {
            break;
        }
        if stdout.flush().is_err() {
            break;
        }
    }

    if !handle.is_null() {
        unsafe {
            ftdi_usb_close(handle);
            ftdi_free(handle);
        }
    }
}
