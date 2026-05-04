# Substrate.lean Design Specification
**Target:** `0-Core-Formalism/lean/Semantics/Semantics/Substrate.lean`  
**Approach:** Design from architecture (Rust code already deleted)  
**Swarm:** Lean Domain Experts with NII Cores  
**Date:** 2026-04-15

---

## Design Context

**Status:** The Rust core (`core/gwl-vm/`) has been deleted per AGENTS.md cleanup rules.  
**Approach:** Design `Substrate.lean` from first principles based on:
- `Semantics/` module architecture
- XTAF/XARCH specifications in docs
- Bind primitive integration requirements
- FFI boundary to remaining Rust shims

---

## Required Components

### 1. Opcode Inductive Type
**Purpose:** Define all VM operations as Lean inductive type  
**Integration:** Must work with `Bind.lean` and `Canon.lean`

```lean
namespace Semantics.Substrate

/-- XTAF-inspired opcode set for GWL-VM -/
inductive Opcode where
  -- Stack operations
  | push (value : UInt64)     -- Push immediate value
  | pop                       -- Pop top of stack
  | dup (n : UInt8)          -- Duplicate nth stack item
  | swap (n : UInt8)         -- Swap with nth stack item
  
  -- Arithmetic operations (Q16.16 fixed-point)
  | add                      -- Add top two stack items
  | sub                      -- Subtract
  | mul                      -- Multiply
  | div                      -- Divide
  | rem                      -- Remainder
  
  -- Logical operations
  | and                      -- Bitwise AND
  | or                       -- Bitwise OR
  | xor                      -- Bitwise XOR
  | not                      -- Bitwise NOT
  | shiftL (n : UInt8)       -- Left shift
  | shiftR (n : UInt8)       -- Right shift
  
  -- Memory operations
  | load (addr : UInt64)     -- Load from address
  | store (addr : UInt64)    -- Store to address
  
  -- Control flow
  | jump (offset : Int64)    -- Unconditional jump
  | jumpIf (offset : Int64)  -- Conditional jump (if top != 0)
  | call (addr : UInt64)     -- Call function
  | ret                      -- Return from function
  
  -- Bind operations (integration with Semantics)
  | bind (kind : ParticleKind)  -- Execute bind for particle kind
  | witness (hash : ByteArray) -- Record witness hash
  | attest (data : ByteArray)  -- Attestation operation
  
  -- Substrate operations
  | substrateAlloc (size : UInt64)  -- Allocate substrate memory
  | substrateFree (ptr : UInt64)    -- Free substrate memory
  | substrateExec (id : UInt64)     -- Execute substrate computation
  
  deriving DecidableEq, Repr, Inhabited

def Opcode.toByte (op : Opcode) : UInt8 :=
  match op with
  | push _ => 0x01
  | pop => 0x02
  | dup _ => 0x03
  | swap _ => 0x04
  | add => 0x10
  | sub => 0x11
  | mul => 0x12
  | div => 0x13
  | rem => 0x14
  | and => 0x20
  | or => 0x21
  | xor => 0x22
  | not => 0x23
  | shiftL _ => 0x24
  | shiftR _ => 0x25
  | load _ => 0x30
  | store _ => 0x31
  | jump _ => 0x40
  | jumpIf _ => 0x41
  | call _ => 0x42
  | ret => 0x43
  | bind _ => 0x50
  | witness _ => 0x51
  | attest _ => 0x52
  | substrateAlloc _ => 0x60
  | substrateFree _ => 0x61
  | substrateExec _ => 0x62
```

### 2. Decoder Function
**Purpose:** Parse ByteArray into Opcode  
**Requirement:** Total function with proof of termination

```lean
/-- Decode single opcode from byte array starting at offset
    Returns (opcode, bytes_consumed) or none if invalid -/
def decodeOpcode (bytes : ByteArray) (offset : Nat := 0) : Option (Opcode × Nat) :=
  if h : offset < bytes.size then
    let byte := bytes.get! offset
    match byte with
    | 0x01 => 
        -- push: next 8 bytes are the value
        if offset + 8 < bytes.size then
          let value := UInt64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.push value, 9)
        else none
    | 0x02 => some (Opcode.pop, 1)
    | 0x03 => 
        if offset + 1 < bytes.size then
          let n := bytes.get! (offset + 1)
          some (Opcode.dup n, 2)
        else none
    | 0x04 => 
        if offset + 1 < bytes.size then
          let n := bytes.get! (offset + 1)
          some (Opcode.swap n, 2)
        else none
    | 0x10 => some (Opcode.add, 1)
    | 0x11 => some (Opcode.sub, 1)
    | 0x12 => some (Opcode.mul, 1)
    | 0x13 => some (Opcode.div, 1)
    | 0x14 => some (Opcode.rem, 1)
    | 0x20 => some (Opcode.and, 1)
    | 0x21 => some (Opcode.or, 1)
    | 0x22 => some (Opcode.xor, 1)
    | 0x23 => some (Opcode.not, 1)
    | 0x24 => 
        if offset + 1 < bytes.size then
          let n := bytes.get! (offset + 1)
          some (Opcode.shiftL n, 2)
        else none
    | 0x25 => 
        if offset + 1 < bytes.size then
          let n := bytes.get! (offset + 1)
          some (Opcode.shiftR n, 2)
        else none
    | 0x30 => 
        if offset + 8 < bytes.size then
          let addr := UInt64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.load addr, 9)
        else none
    | 0x31 => 
        if offset + 8 < bytes.size then
          let addr := UInt64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.store addr, 9)
        else none
    | 0x40 => 
        if offset + 8 < bytes.size then
          let offset := Int64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.jump offset, 9)
        else none
    | 0x41 => 
        if offset + 8 < bytes.size then
          let offset := Int64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.jumpIf offset, 9)
        else none
    | 0x42 => 
        if offset + 8 < bytes.size then
          let addr := UInt64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.call addr, 9)
        else none
    | 0x43 => some (Opcode.ret, 1)
    | 0x50 => 
        if offset + 1 < bytes.size then
          let kind := ParticleKind.ofByte (bytes.get! (offset + 1))
          some (Opcode.bind kind, 2)
        else none
    | 0x51 => 
        if offset + 32 < bytes.size then
          let hash := bytes.as[offset+1:offset+33]
          some (Opcode.witness hash, 33)
        else none
    | 0x52 => 
        if offset + 32 < bytes.size then
          let data := bytes.as[offset+1:offset+33]
          some (Opcode.attest data, 33)
        else none
    | 0x60 => 
        if offset + 8 < bytes.size then
          let size := UInt64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.substrateAlloc size, 9)
        else none
    | 0x61 => 
        if offset + 8 < bytes.size then
          let ptr := UInt64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.substrateFree ptr, 9)
        else none
    | 0x62 => 
        if offset + 8 < bytes.size then
          let id := UInt64.ofNat (bytes.as[offset+1:offset+9].toNat)
          some (Opcode.substrateExec id, 9)
        else none
    | _ => none  -- Unknown opcode
  else none
```

### 3. Encoder Function
**Purpose:** Serialize Opcode to ByteArray  
**Requirement:** Inverse of decoder (proof of roundtrip)

```lean
/-- Encode opcode to byte array -/
def Opcode.encode (op : Opcode) : ByteArray :=
  match op with
  | push value => 
      ByteArray.mk #[0x01] ++ UInt64.toByteArray value
  | pop => ByteArray.mk #[0x02]
  | dup n => ByteArray.mk #[0x03, n]
  | swap n => ByteArray.mk #[0x04, n]
  | add => ByteArray.mk #[0x10]
  | sub => ByteArray.mk #[0x11]
  | mul => ByteArray.mk #[0x12]
  | div => ByteArray.mk #[0x13]
  | rem => ByteArray.mk #[0x14]
  | and => ByteArray.mk #[0x20]
  | or => ByteArray.mk #[0x21]
  | xor => ByteArray.mk #[0x22]
  | not => ByteArray.mk #[0x23]
  | shiftL n => ByteArray.mk #[0x24, n]
  | shiftR n => ByteArray.mk #[0x25, n]
  | load addr => ByteArray.mk #[0x30] ++ UInt64.toByteArray addr
  | store addr => ByteArray.mk #[0x31] ++ UInt64.toByteArray addr
  | jump offset => ByteArray.mk #[0x40] ++ Int64.toByteArray offset
  | jumpIf offset => ByteArray.mk #[0x41] ++ Int64.toByteArray offset
  | call addr => ByteArray.mk #[0x42] ++ UInt64.toByteArray addr
  | ret => ByteArray.mk #[0x43]
  | bind kind => ByteArray.mk #[0x50, ParticleKind.toByte kind]
  | witness hash => ByteArray.mk #[0x51] ++ hash
  | attest data => ByteArray.mk #[0x52] ++ data
  | substrateAlloc size => ByteArray.mk #[0x60] ++ UInt64.toByteArray size
  | substrateFree ptr => ByteArray.mk #[0x61] ++ UInt64.toByteArray ptr
  | substrateExec id => ByteArray.mk #[0x62] ++ UInt64.toByteArray id
```

### 4. VM State Representation
**Purpose:** Formalize VM execution state  
**Integration:** With `Canon.lean` for canonical state

```lean
/-- VM execution state -/
structure VMState where
  stack : List UInt64           -- Operand stack
  memory : ByteArray            -- Linear memory
  pc : Nat                      -- Program counter
  gas : UInt64                  -- Remaining gas
  substrate : SubstrateState    -- Substrate computation state
  
-- Canon integration: VM state must be canonically representable
instance : Canon VMState where
  canonicalize s := 
    Canon.canonicalize (s.stack, s.memory, s.pc, s.gas, s.substrate)
```

### 5. Step Function
**Purpose:** Single VM step execution  
**Requirement:** Total function, provably safe

```lean
/-- Execute single VM step
    Returns new state or none if halt/error -/
def vmStep (state : VMState) (opcode : Opcode) : Option VMState :=
  match opcode with
  | push value => 
      some { state with 
        stack := value :: state.stack,
        pc := state.pc + 9,
        gas := state.gas - 1
      }
  | pop => 
      match state.stack with
      | _ :: rest => 
          some { state with
            stack := rest,
            pc := state.pc + 1,
            gas := state.gas - 1
          }
      | [] => none  -- Stack underflow
  | add => 
      match state.stack with
      | b :: a :: rest => 
          some { state with
            stack := (a + b) :: rest,
            pc := state.pc + 1,
            gas := state.gas - 1
          }
      | _ => none  -- Stack underflow
  -- ... other opcodes
  | bind kind =>
      -- Execute bind primitive via Bind.lean
      match Bind.execute kind state.substrate with
      | (result, newSubstrate) =>
          some { state with
            stack := result :: state.stack,
            substrate := newSubstrate,
            pc := state.pc + 2,
            gas := state.gas - Bind.cost kind
          }
  | _ => none  -- Unimplemented
```

---

## Proof Obligations (LF-03)

### Theorem 1: Decoder Totality
```lean
theorem decodeOpcode_total (bytes : ByteArray) (offset : Nat) :
  offset < bytes.size → 
  decodeOpcode bytes offset = none ∨ 
  ∃ (op : Opcode) (n : Nat), decodeOpcode bytes offset = some (op, n) := by
  intro h
  simp [decodeOpcode, h]
  split <;> simp <;> try { exact Or.inl rfl } <;> try { exact Or.inr ⟨_, _, rfl⟩ }
```

### Theorem 2: Encode-Decode Roundtrip
```lean
theorem encode_decode_roundtrip (op : Opcode) :
  decodeOpcode (op.encode) 0 = some (op, op.encode.size) := by
  cases op <;> simp [Opcode.encode, decodeOpcode] <;> native_decide
```

### Theorem 3: Step Function Safety
```lean
theorem vmStep_preserves_invariant (state : VMState) (op : Opcode) :
  state.gas > 0 → 
  match vmStep state op with
  | some newState => newState.gas < state.gas ∧ Canon.isValid newState
  | none => True := by
  intro h_gas
  cases op <;> simp [vmStep] <;> try { simp [h_gas] } <;> split <;> simp [Canon.isValid]
```

---

## FFI Boundaries (LT-04 + LF-04)

### Rust Shim (remaining after cleanup)
```rust
// infra/access_control/rust_shim/src/substrate.rs
// Minimal FFI shim for Substrate operations

#[no_mangle]
pub extern "C" fn lean_substrate_step(
    vm_state_ptr: *const u8,
    vm_state_len: usize,
    opcode_byte: u8,
    result_ptr: *mut u8,
    result_len: usize
) -> i32 {
    // FFI boundary to Lean Substrate.step function
    // Marshals VM state, calls Lean, returns result
}
```

### Lean Extern
```lean
@[extern "lean_substrate_step"]
opaque substrateStepExtern (state : VMState) (opcodeByte : UInt8) : Option VMState

def substrateStep (state : VMState) (opcodeByte : UInt8) : Option VMState :=
  -- Can use pure Lean implementation OR FFI
  substrateStepExtern state opcodeByte
```

---

## Integration Points

### With Bind.lean
- `Opcode.bind` delegates to `Bind.execute`
- VM state substrate component managed by Bind

### With Canon.lean
- `VMState` has `Canon` instance for canonical serialization
- Enables deterministic state hashing

### With FixedPoint.lean
- Arithmetic operations use Q16.16 fixed-point
- Gas costs in Q16.16 for fractional accounting

### With Evolution.lean
- VM step transitions as evolution steps
- Regime changes based on gas/operation patterns

---

**SWARM ASSIGNMENT:**
- **LF-01:** Design inductive type (Section 2 above)
- **LF-02:** Implement DecidableEq, Repr, Inhabited
- **LT-02:** Port decoder function with pattern matching
- **LT-01:** Port encoder function
- **LF-04:** Design VMState structure
- **LF-03:** Prove theorems 1-3
- **LT-04:** Design FFI boundaries
- **RA Team:** Extract patterns from XTAF/XARCH docs

**TIMELINE:** 8 hours for complete Substrate.lean module

---

**COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)**  
**PROJECT:** SOVEREIGN STACK  
**DESIGN:** SUBSTRATE_SPECIFICATION_2026-04-15

---
