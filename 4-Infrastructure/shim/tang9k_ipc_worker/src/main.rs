#![allow(dead_code)]

use std::env;
use std::fs::OpenOptions;
use std::io;
use std::os::fd::AsRawFd;
use std::path::PathBuf;
use std::ptr::NonNull;
use std::sync::atomic::{fence, AtomicU32, Ordering};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const DEFAULT_RING: &str = "/dev/shm/tang9k_gpu_fpga_symbol_surface.ring";
const MAGIC: &[u8; 4] = b"T9IP";
const VERSION: u32 = 1;
const HEADER_SIZE: usize = 64;
const RECORD_SIZE: usize = 64;

const HEADER_MAGIC_OFFSET: usize = 0;
const HEADER_VERSION_OFFSET: usize = 4;
const HEADER_SLOTS_OFFSET: usize = 8;
const HEADER_WRITE_INDEX_OFFSET: usize = 12;
const HEADER_READ_INDEX_OFFSET: usize = 16;

const REC_STATUS_OFFSET: usize = 0;
const REC_MODE_OFFSET: usize = 1;
const REC_SEQ_OFFSET: usize = 2;
const REC_PAYLOAD_OFFSET: usize = 4;
const REC_EXPECTED_HASH_OFFSET: usize = 20;
const REC_RECEIPT_HASH_OFFSET: usize = 22;
const REC_MAPPED_OFFSET: usize = 24;
const REC_LITERAL_OFFSET: usize = 25;
const REC_HW_STATUS_OFFSET: usize = 26;
const REC_PAYLOAD_LEN_OFFSET: usize = 27;
const REC_TIMESTAMP_NS_OFFSET: usize = 28;

const STATUS_EMPTY: u8 = 0;
const STATUS_PENDING: u8 = 1;
const STATUS_DONE: u8 = 2;
const STATUS_ERROR: u8 = 3;

#[allow(non_camel_case_types)]
type c_void = core::ffi::c_void;

unsafe extern "C" {
    fn mmap(
        addr: *mut c_void,
        length: usize,
        prot: i32,
        flags: i32,
        fd: i32,
        offset: isize,
    ) -> *mut c_void;
    fn munmap(addr: *mut c_void, length: usize) -> i32;
    fn msync(addr: *mut c_void, length: usize, flags: i32) -> i32;
}

const PROT_READ: i32 = 0x1;
const PROT_WRITE: i32 = 0x2;
const MAP_SHARED: i32 = 0x01;
const MS_SYNC: i32 = 0x4;

#[derive(Debug)]
struct Config {
    ring: PathBuf,
    cmd: Command,
}

#[derive(Debug)]
enum Command {
    Abi,
    Status,
    Consume { max_records: usize, spin_ms: u64 },
}

struct RingMap {
    ptr: NonNull<u8>,
    len: usize,
}

#[derive(Clone, Debug)]
struct Header {
    version: u32,
    slots: u32,
    write_index: u32,
    read_index: u32,
}

#[derive(Clone, Debug)]
struct Receipt {
    slot: u32,
    seq: u16,
    status: u8,
    expected_hash: u16,
    receipt_hash: u16,
    mapped_count: u8,
    literal_count: u8,
}

fn main() -> io::Result<()> {
    let config = Config::from_args();
    match config.cmd {
        Command::Abi => {
            println!(
                "{{\"schema\":\"tang9k_ipc_worker_abi_v1\",\"header_size\":{},\"record_size\":{},\"default_ring\":\"{}\"}}",
                HEADER_SIZE, RECORD_SIZE, DEFAULT_RING
            );
            Ok(())
        }
        Command::Status => {
            let ring = RingMap::open(&config.ring)?;
            let header = ring.header()?;
            let counts = ring.status_counts(&header);
            println!(
                "{{\"schema\":\"tang9k_ipc_worker_status_v1\",\"ring\":\"{}\",\"header\":{{\"version\":{},\"slots\":{},\"write_index\":{},\"read_index\":{}}},\"status_counts\":{{\"0\":{},\"1\":{},\"2\":{},\"3\":{}}}}}",
                config.ring.display(),
                header.version,
                header.slots,
                header.write_index,
                header.read_index,
                counts[0],
                counts[1],
                counts[2],
                counts[3],
            );
            Ok(())
        }
        Command::Consume {
            max_records,
            spin_ms,
        } => {
            let ring = RingMap::open(&config.ring)?;
            let receipts = ring.consume(max_records, Duration::from_millis(spin_ms))?;
            print_consume_report(&config.ring, &receipts);
            Ok(())
        }
    }
}

impl Config {
    fn from_args() -> Self {
        let mut ring = PathBuf::from(DEFAULT_RING);
        let mut cmd = None;
        let mut max_records = 1usize;
        let mut spin_ms = 0u64;

        let mut args = env::args().skip(1);
        while let Some(arg) = args.next() {
            match arg.as_str() {
                "--ring" => {
                    if let Some(value) = args.next() {
                        ring = PathBuf::from(value);
                    }
                }
                "abi" => cmd = Some(Command::Abi),
                "status" => cmd = Some(Command::Status),
                "consume" => {
                    cmd = Some(Command::Consume {
                        max_records,
                        spin_ms,
                    })
                }
                "--max-records" => {
                    if let Some(value) = args.next() {
                        max_records = value.parse().unwrap_or(1);
                    }
                    cmd = Some(Command::Consume {
                        max_records,
                        spin_ms,
                    });
                }
                "--spin-ms" => {
                    if let Some(value) = args.next() {
                        spin_ms = value.parse().unwrap_or(0);
                    }
                    cmd = Some(Command::Consume {
                        max_records,
                        spin_ms,
                    });
                }
                _ => {}
            }
        }

        Self {
            ring,
            cmd: cmd.unwrap_or(Command::Status),
        }
    }
}

impl RingMap {
    fn open(path: &PathBuf) -> io::Result<Self> {
        let file = OpenOptions::new().read(true).write(true).open(path)?;
        let len = file.metadata()?.len() as usize;
        if len < HEADER_SIZE {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "ring is smaller than header",
            ));
        }

        let raw = unsafe {
            mmap(
                std::ptr::null_mut(),
                len,
                PROT_READ | PROT_WRITE,
                MAP_SHARED,
                file.as_raw_fd(),
                0,
            )
        };
        if raw as isize == -1 {
            return Err(io::Error::last_os_error());
        }
        Ok(Self {
            ptr: NonNull::new(raw.cast::<u8>()).expect("mmap returned null"),
            len,
        })
    }

    fn header(&self) -> io::Result<Header> {
        let magic = self.bytes(HEADER_MAGIC_OFFSET, 4);
        if magic != MAGIC {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "not a Tang9K IPC symbol surface ring",
            ));
        }
        let version = self.load_u32(HEADER_VERSION_OFFSET, Ordering::Acquire);
        let slots = self.load_u32(HEADER_SLOTS_OFFSET, Ordering::Acquire);
        let write_index = self.load_u32(HEADER_WRITE_INDEX_OFFSET, Ordering::Acquire);
        let read_index = self.load_u32(HEADER_READ_INDEX_OFFSET, Ordering::Acquire);
        if version != VERSION {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                format!("unsupported ring version {version}"),
            ));
        }
        if HEADER_SIZE + (slots as usize * RECORD_SIZE) > self.len {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "ring header slot count exceeds mapped file size",
            ));
        }
        Ok(Header {
            version,
            slots,
            write_index,
            read_index,
        })
    }

    fn consume(&self, max_records: usize, spin: Duration) -> io::Result<Vec<Receipt>> {
        let deadline = SystemTime::now() + spin;
        let mut receipts = Vec::new();
        while receipts.len() < max_records {
            let Some(receipt) = self.consume_one()? else {
                if spin.is_zero() || SystemTime::now() >= deadline {
                    break;
                }
                thread::yield_now();
                continue;
            };
            receipts.push(receipt);
        }
        unsafe {
            msync(self.ptr.as_ptr().cast::<c_void>(), self.len, MS_SYNC);
        }
        Ok(receipts)
    }

    fn consume_one(&self) -> io::Result<Option<Receipt>> {
        let header = self.header()?;
        if header.read_index == header.write_index {
            return Ok(None);
        }

        let slot = header.read_index % header.slots;
        let base = record_offset(slot);
        let status = self.load_u8(base + REC_STATUS_OFFSET);
        if status != STATUS_PENDING {
            return Ok(None);
        }

        fence(Ordering::SeqCst);
        let seq = self.load_u16(base + REC_SEQ_OFFSET);
        let expected_hash = self.load_u16(base + REC_EXPECTED_HASH_OFFSET);
        let payload_len = self.load_u8(base + REC_PAYLOAD_LEN_OFFSET).min(16);
        let payload = self.bytes(base + REC_PAYLOAD_OFFSET, payload_len as usize);
        let receipt = receipt_for_payload(payload);
        let status = if receipt.hash16 == expected_hash {
            STATUS_DONE
        } else {
            STATUS_ERROR
        };

        self.store_u16(base + REC_RECEIPT_HASH_OFFSET, receipt.hash16);
        self.store_u8(base + REC_MAPPED_OFFSET, receipt.mapped);
        self.store_u8(base + REC_LITERAL_OFFSET, receipt.literal);
        self.store_u8(base + REC_HW_STATUS_OFFSET, 0);
        self.store_u64(base + REC_TIMESTAMP_NS_OFFSET, now_ns());
        fence(Ordering::SeqCst);
        self.store_u8(base + REC_STATUS_OFFSET, status);
        self.store_u32(
            HEADER_READ_INDEX_OFFSET,
            header.read_index.wrapping_add(1),
            Ordering::Release,
        );

        Ok(Some(Receipt {
            slot,
            seq,
            status,
            expected_hash,
            receipt_hash: receipt.hash16,
            mapped_count: receipt.mapped,
            literal_count: receipt.literal,
        }))
    }

    fn status_counts(&self, header: &Header) -> [u32; 4] {
        let mut counts = [0u32; 4];
        for slot in 0..header.slots {
            let status = self.load_u8(record_offset(slot) + REC_STATUS_OFFSET);
            if let Some(count) = counts.get_mut(status as usize) {
                *count += 1;
            }
        }
        counts
    }

    fn bytes(&self, offset: usize, len: usize) -> &[u8] {
        assert!(offset + len <= self.len);
        unsafe { std::slice::from_raw_parts(self.ptr.as_ptr().add(offset), len) }
    }

    fn load_u8(&self, offset: usize) -> u8 {
        self.bytes(offset, 1)[0]
    }

    fn store_u8(&self, offset: usize, value: u8) {
        assert!(offset < self.len);
        unsafe {
            self.ptr.as_ptr().add(offset).write(value);
        }
    }

    fn load_u16(&self, offset: usize) -> u16 {
        let bytes = self.bytes(offset, 2);
        u16::from_le_bytes([bytes[0], bytes[1]])
    }

    fn store_u16(&self, offset: usize, value: u16) {
        let bytes = value.to_le_bytes();
        self.store_bytes(offset, &bytes);
    }

    fn store_u64(&self, offset: usize, value: u64) {
        let bytes = value.to_le_bytes();
        self.store_bytes(offset, &bytes);
    }

    fn load_u32(&self, offset: usize, ordering: Ordering) -> u32 {
        assert_eq!(offset % 4, 0);
        assert!(offset + 4 <= self.len);
        let ptr = unsafe { self.ptr.as_ptr().add(offset).cast::<AtomicU32>() };
        unsafe { (*ptr).load(ordering) }
    }

    fn store_u32(&self, offset: usize, value: u32, ordering: Ordering) {
        assert_eq!(offset % 4, 0);
        assert!(offset + 4 <= self.len);
        let ptr = unsafe { self.ptr.as_ptr().add(offset).cast::<AtomicU32>() };
        unsafe {
            (*ptr).store(value, ordering);
        }
    }

    fn store_bytes(&self, offset: usize, bytes: &[u8]) {
        assert!(offset + bytes.len() <= self.len);
        unsafe {
            std::ptr::copy_nonoverlapping(
                bytes.as_ptr(),
                self.ptr.as_ptr().add(offset),
                bytes.len(),
            );
        }
    }
}

impl Drop for RingMap {
    fn drop(&mut self) {
        unsafe {
            munmap(self.ptr.as_ptr().cast::<c_void>(), self.len);
        }
    }
}

struct SymbolReceipt {
    hash16: u16,
    mapped: u8,
    literal: u8,
}

fn receipt_for_payload(payload: &[u8]) -> SymbolReceipt {
    let mut hash = 0xACE1u16;
    let mut mapped = 0u8;
    let mut literal = 0u8;
    for &byte in payload {
        let (code, hit) = substitute(byte);
        hash = hash.rotate_left(1) ^ ((if hit { 0x10 } else { 0x00 }) | code as u16);
        if hit {
            mapped = mapped.wrapping_add(1);
        } else {
            literal = literal.wrapping_add(1);
        }
    }
    SymbolReceipt {
        hash16: hash,
        mapped,
        literal,
    }
}

fn substitute(byte: u8) -> (u8, bool) {
    match byte {
        b' ' => (0x0, true),
        b'e' | b'E' => (0x1, true),
        b't' | b'T' => (0x2, true),
        b'a' | b'A' => (0x3, true),
        b'o' | b'O' => (0x4, true),
        b'i' | b'I' => (0x5, true),
        b'n' | b'N' => (0x6, true),
        b's' | b'S' => (0x7, true),
        b'r' | b'R' => (0x8, true),
        b'h' | b'H' => (0x9, true),
        b'l' | b'L' => (0xA, true),
        b'd' => (0xB, true),
        b'c' | b'C' => (0xC, true),
        b'u' | b'U' => (0xD, true),
        b'F' => (0xE, true),
        b'D' => (0xF, true),
        _ => (byte & 0xF, false),
    }
}

fn record_offset(slot: u32) -> usize {
    HEADER_SIZE + (slot as usize * RECORD_SIZE)
}

fn now_ns() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos() as u64
}

fn print_consume_report(ring: &PathBuf, receipts: &[Receipt]) {
    print!(
        "{{\"schema\":\"tang9k_ipc_worker_consume_v1\",\"ring\":\"{}\",\"receipt_count\":{},\"receipts\":[",
        ring.display(),
        receipts.len()
    );
    for (idx, receipt) in receipts.iter().enumerate() {
        if idx > 0 {
            print!(",");
        }
        print!(
            "{{\"slot\":{},\"seq\":{},\"status\":\"{}\",\"expected_hash\":{},\"receipt_hash\":{},\"mapped_count\":{},\"literal_count\":{}}}",
            receipt.slot,
            receipt.seq,
            if receipt.status == STATUS_DONE { "done" } else { "error" },
            receipt.expected_hash,
            receipt.receipt_hash,
            receipt.mapped_count,
            receipt.literal_count
        );
    }
    println!("]}}");
}
