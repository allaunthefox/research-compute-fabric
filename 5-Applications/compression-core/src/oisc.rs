//! Rust OISC decompressor target.
//!
//! This module is a reference backend for the Lean surface
//! `Semantics.RustOISCDecompressor`. It is not a compression benchmark and does
//! not claim silicon-target readiness.

use crate::{CompressionError, Compressor};

pub const MAGIC: &[u8; 4] = b"OISC";
pub const VERSION: u8 = 1;
pub const HEADER_LEN: usize = 5;
pub const INSTRUCTION_LEN: usize = 3;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OiscDecision {
    Done,
    Nan0,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OiscReceipt {
    pub output: Vec<u8>,
    pub instruction_count: usize,
    pub accumulator: u8,
    pub decision: OiscDecision,
    pub input_hash: u64,
    pub output_hash: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OiscReplayMeta {
    pub instruction_count: usize,
    pub accumulator: u8,
    pub decision: OiscDecision,
    pub input_hash: u64,
    pub output_hash: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct OiscState {
    pc: usize,
    acc: u8,
    halted: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Instruction {
    symbol: u8,
    residual: u8,
    final_flag: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Transition {
    Continue,
    Done,
    Nan0,
}

pub struct OiscCompressor;

fn stable_hash(bytes: &[u8]) -> u64 {
    let mut hash = 0xcbf2_9ce4_8422_2325u64;
    for &byte in bytes {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(0x0000_0100_0000_01b3);
    }
    hash
}

fn step(
    state: &mut OiscState,
    output: &mut Vec<u8>,
    capacity: usize,
    instr: Instruction,
) -> Transition {
    if state.halted {
        return Transition::Done;
    }
    if output.len() >= capacity {
        state.halted = true;
        return Transition::Nan0;
    }

    output.push(instr.symbol);
    state.pc += 1;
    state.acc = state
        .acc
        .wrapping_add(instr.symbol)
        .wrapping_add(instr.residual);
    state.halted = instr.final_flag;

    if instr.final_flag {
        Transition::Done
    } else {
        Transition::Continue
    }
}

fn parse_instruction(input: &[u8], pos: usize) -> Result<Instruction, CompressionError> {
    if pos + INSTRUCTION_LEN > input.len() {
        return Err(CompressionError::CorruptStream);
    }
    let final_flag = match input[pos + 2] {
        0 => false,
        1 => true,
        _ => return Err(CompressionError::CorruptStream),
    };
    Ok(Instruction {
        symbol: input[pos],
        residual: input[pos + 1],
        final_flag,
    })
}

fn validate_instruction_stream(input: &[u8]) -> Result<(), CompressionError> {
    let mut pos = HEADER_LEN;
    while pos < input.len() {
        let instr = parse_instruction(input, pos)?;
        if instr.final_flag && pos + INSTRUCTION_LEN < input.len() {
            return Err(CompressionError::CorruptStream);
        }
        pos += INSTRUCTION_LEN;
    }
    Ok(())
}

pub fn decompress_oisc(
    input: &[u8],
    output_capacity: usize,
) -> Result<OiscReceipt, CompressionError> {
    let mut output = Vec::with_capacity(output_capacity);
    let meta = decompress_oisc_into(input, output_capacity, &mut output)?;
    Ok(OiscReceipt {
        output,
        instruction_count: meta.instruction_count,
        accumulator: meta.accumulator,
        decision: meta.decision,
        input_hash: meta.input_hash,
        output_hash: meta.output_hash,
    })
}

pub fn decompress_oisc_into(
    input: &[u8],
    output_capacity: usize,
    output: &mut Vec<u8>,
) -> Result<OiscReplayMeta, CompressionError> {
    output.clear();
    if output.capacity() < output_capacity {
        return Err(CompressionError::CapacityExceeded);
    }

    if input.len() < HEADER_LEN {
        return Err(CompressionError::InvalidData);
    }
    if &input[0..4] != MAGIC {
        return Err(CompressionError::InvalidData);
    }
    if input[4] != VERSION {
        return Err(CompressionError::UnsupportedVersion);
    }

    if input.len() == HEADER_LEN {
        return Ok(OiscReplayMeta {
            instruction_count: 0,
            accumulator: 0,
            decision: OiscDecision::Done,
            input_hash: stable_hash(input),
            output_hash: stable_hash(output),
        });
    }

    let body_len = input.len() - HEADER_LEN;
    if body_len % INSTRUCTION_LEN != 0 {
        return Err(CompressionError::CorruptStream);
    }
    validate_instruction_stream(input)?;

    let mut state = OiscState {
        pc: 0,
        acc: 0,
        halted: false,
    };
    let mut pos = HEADER_LEN;
    let mut instruction_count = 0usize;

    while pos < input.len() {
        let instr = parse_instruction(input, pos)?;
        let decision = step(&mut state, output, output_capacity, instr);
        instruction_count += 1;

        match decision {
            Transition::Done => {
                return Ok(OiscReplayMeta {
                    instruction_count,
                    accumulator: state.acc,
                    decision: OiscDecision::Done,
                    input_hash: stable_hash(input),
                    output_hash: stable_hash(output),
                });
            }
            Transition::Nan0 => {
                return Err(CompressionError::CapacityExceeded);
            }
            Transition::Continue => {}
        }
        pos += INSTRUCTION_LEN;
    }

    Ok(OiscReplayMeta {
        instruction_count,
        accumulator: state.acc,
        decision: OiscDecision::Done,
        input_hash: stable_hash(input),
        output_hash: stable_hash(output),
    })
}

impl Compressor for OiscCompressor {
    fn compress(&self, input: &[u8]) -> Vec<u8> {
        let mut out = Vec::with_capacity(HEADER_LEN + input.len() * INSTRUCTION_LEN);
        out.extend_from_slice(MAGIC);
        out.push(VERSION);
        for (idx, &symbol) in input.iter().enumerate() {
            out.push(symbol);
            out.push(0);
            out.push((idx + 1 == input.len()) as u8);
        }
        out
    }

    fn decompress(&self, input: &[u8]) -> Result<Vec<u8>, CompressionError> {
        let instruction_capacity = if input.len() >= HEADER_LEN {
            (input.len() - HEADER_LEN) / INSTRUCTION_LEN
        } else {
            0
        };
        decompress_oisc(input, instruction_capacity).map(|receipt| receipt.output)
    }

    fn name(&self) -> &'static str {
        "oisc-replay-v0.1"
    }

    fn ratio(&self) -> f64 {
        1.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const ABC_WIRE: &[u8] = b"OISC\x01A\x01\x00B\x01\x00C\x01\x01";
    const RESIDUAL_WIRE: &[u8] = b"OISC\x01A\xff\x00B\x01\x00C\x02\x01";
    const TRANSFER_FIXTURE: &[u8] = br#"Hutter transfer readiness fixture.

This small corpus window is intentionally local and inspectable. It carries
repeated phrases, shifted byte contexts, punctuation, digits 0123456789, and
line breaks so replay code must preserve more than a three-symbol toy stream.

Window alpha binds local recurrence: stack stack stack, receipt receipt receipt,
offset offset offset. Window beta changes cadence with JSON-ish tokens:
{"decision":"HOLD","window":128,"route":"oisc-replay"}.

Window gamma adds mixed case and separators: Alpha/BETA/gamma; phase_00,
phase_01, phase_02. The fixture stops here because the readiness gate is about
manifest discipline, not corpus scale.
"#;

    fn expected_accumulator(instructions: &[(u8, u8)]) -> u8 {
        instructions.iter().fold(0, |acc, &(symbol, residual)| {
            acc.wrapping_add(symbol).wrapping_add(residual)
        })
    }

    #[test]
    fn abc_matches_lean_fixture() {
        let receipt = decompress_oisc(ABC_WIRE, 8).expect("valid ABC fixture");
        assert_eq!(receipt.output, b"ABC");
        assert_eq!(receipt.instruction_count, 3);
        assert_eq!(receipt.accumulator, 201);
        assert_eq!(receipt.decision, OiscDecision::Done);
    }

    #[test]
    fn empty_stream_closes() {
        let receipt = decompress_oisc(b"OISC\x01", 8).expect("header-only stream");
        assert_eq!(receipt.output, b"");
        assert_eq!(receipt.instruction_count, 0);
        assert_eq!(receipt.accumulator, 0);
        assert_eq!(receipt.decision, OiscDecision::Done);
    }

    #[test]
    fn capacity_overflow_fails_closed() {
        let err = decompress_oisc(ABC_WIRE, 2).expect_err("capacity should overflow");
        assert!(matches!(err, CompressionError::CapacityExceeded));
    }

    #[test]
    fn invalid_magic_rejected() {
        let err = decompress_oisc(b"XISC\x01", 8).expect_err("bad magic");
        assert!(matches!(err, CompressionError::InvalidData));
    }

    #[test]
    fn invalid_version_rejected() {
        let err = decompress_oisc(b"OISC\x02", 8).expect_err("bad version");
        assert!(matches!(err, CompressionError::UnsupportedVersion));
    }

    #[test]
    fn truncated_instruction_rejected() {
        let err = decompress_oisc(b"OISC\x01A\x01", 8).expect_err("truncated instruction");
        assert!(matches!(err, CompressionError::CorruptStream));
    }

    #[test]
    fn trailing_after_final_rejected() {
        let err = decompress_oisc(b"OISC\x01A\x01\x01B\x01\x00", 8)
            .expect_err("trailing bytes after final");
        assert!(matches!(err, CompressionError::CorruptStream));
    }

    #[test]
    fn compressor_round_trips_without_claiming_ratio() {
        let compressor = OiscCompressor;
        let wire = compressor.compress(b"ABC");
        let output = compressor.decompress(&wire).expect("round trip");
        assert_eq!(output, b"ABC");
        assert_eq!(compressor.name(), "oisc-replay-v0.1");
        assert_eq!(compressor.ratio(), 1.0);
    }

    #[test]
    fn residual_accumulator_is_deterministic_receipt_field() {
        let first = decompress_oisc(RESIDUAL_WIRE, 8).expect("valid residual fixture");
        let second = decompress_oisc(RESIDUAL_WIRE, 8).expect("valid residual fixture");

        assert_eq!(first, second);
        assert_eq!(first.output, b"ABC");
        assert_eq!(
            first.accumulator,
            expected_accumulator(&[(b'A', 0xff), (b'B', 1), (b'C', 2)])
        );
        assert_eq!(first.instruction_count, 3);
        assert_eq!(first.decision, OiscDecision::Done);
    }

    #[test]
    fn final_instruction_rejects_trailing_without_executing_it() {
        let mut output = Vec::with_capacity(8);
        let err = decompress_oisc_into(b"OISC\x01A\x01\x01Z\xff\x00", 8, &mut output)
            .expect_err("trailing instruction after final must be rejected");

        assert!(matches!(err, CompressionError::CorruptStream));
        assert!(output.is_empty());
        assert!(!output.contains(&b'Z'));
    }

    #[test]
    fn decompress_into_reuses_caller_buffer() {
        let mut output = Vec::with_capacity(8);
        output.extend_from_slice(b"stale");
        let original_capacity = output.capacity();

        let meta = decompress_oisc_into(ABC_WIRE, 8, &mut output).expect("valid ABC fixture");

        assert_eq!(output, b"ABC");
        assert_eq!(output.capacity(), original_capacity);
        assert_eq!(meta.instruction_count, 3);
        assert_eq!(meta.accumulator, 201);
        assert_eq!(meta.output_hash, stable_hash(b"ABC"));
    }

    #[test]
    fn decompress_into_rejects_undersized_caller_buffer_before_writing() {
        let mut output = Vec::with_capacity(2);
        output.extend_from_slice(b"xy");

        let err = decompress_oisc_into(ABC_WIRE, 3, &mut output)
            .expect_err("caller buffer capacity is part of the receipt contract");

        assert!(matches!(err, CompressionError::CapacityExceeded));
        assert!(output.is_empty());
        assert_eq!(output.capacity(), 2);
    }

    #[test]
    fn non_toy_transfer_fixture_replays_byte_exact() {
        let compressor = OiscCompressor;
        let wire = compressor.compress(TRANSFER_FIXTURE);
        let receipt =
            decompress_oisc(&wire, TRANSFER_FIXTURE.len()).expect("transfer fixture replay");

        assert_eq!(receipt.output, TRANSFER_FIXTURE);
        assert_eq!(receipt.instruction_count, TRANSFER_FIXTURE.len());
        assert_eq!(receipt.decision, OiscDecision::Done);
        assert_eq!(receipt.input_hash, stable_hash(&wire));
        assert_eq!(receipt.output_hash, stable_hash(TRANSFER_FIXTURE));
        assert!(receipt.instruction_count > 128);
        assert!(wire.len() > TRANSFER_FIXTURE.len());
    }
}
