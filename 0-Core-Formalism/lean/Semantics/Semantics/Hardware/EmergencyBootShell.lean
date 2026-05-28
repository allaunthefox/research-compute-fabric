/-
  Emergency Boot Shell -- Command interface and packet format

  Defines the Tiny IP surface extensions for emergency boot operations:
  - Command opcodes and payloads
  - Status byte encoding
  - Process definitions (geometry_scan, seed_assembly, tsm_reconstruct, etc.)

  Specification: GEOMETRY_EMERGENCY_BOOT_WITNESS_2026-04-08.md Appendix
-/

import Semantics.FixedPoint
import Semantics.Hardware.EmergencyBootTypes
import Semantics.Hardware.EmergencyBootState

namespace Semantics.Hardware.EmergencyBoot

open Semantics.Q16_16

-- ============================================================================
-- Command Opcodes (Tiny IP domain 0x0D emergency boot extensions)
-- ============================================================================

inductive EmergencyCommand where
  | BOOT       -- 0x01: Extract and return geometric seed
  | SCAN       -- 0x02: Return full geometry witness
  | RECOVER    -- 0x03: Expand seed to TSM-VDP ISA word
  | DIAG       -- 0x04: Run diagnostics with test mask
  | STATUS     -- 0x05: Return system status byte
  | OPTICAL    -- 0x06: Control/query optical fiber paths
  | FIBER      -- 0x07: Query outer optical ring status
  | GRAPHENE   -- 0x08: Query graphene material health
  | GAN        -- 0x09: Query GaN wire/interconnect status
  | MEMRISTOR  -- 0x0A: Query memristor memory state
  | VOLTAGE    -- 0x0B: Query voltage differential computation
  | EXIT       -- 0xFF: Exit recovery, return to normal operation
  deriving Repr, BEq

/-- Map command to its 1-byte opcode. -/
def commandOpcode (cmd : EmergencyCommand) : UInt8 :=
  match cmd with
  | EmergencyCommand.BOOT      => 0x01
  | EmergencyCommand.SCAN      => 0x02
  | EmergencyCommand.RECOVER   => 0x03
  | EmergencyCommand.DIAG      => 0x04
  | EmergencyCommand.STATUS    => 0x05
  | EmergencyCommand.OPTICAL   => 0x06
  | EmergencyCommand.FIBER     => 0x07
  | EmergencyCommand.GRAPHENE  => 0x08
  | EmergencyCommand.GAN       => 0x09
  | EmergencyCommand.MEMRISTOR => 0x0A
  | EmergencyCommand.VOLTAGE   => 0x0B
  | EmergencyCommand.EXIT      => 0xFF

/-- Parse opcode byte to command. Returns none for unknown opcodes. -/
def parseOpcode (opcode : UInt8) : Option EmergencyCommand :=
  match opcode with
  | 0x01 => some EmergencyCommand.BOOT
  | 0x02 => some EmergencyCommand.SCAN
  | 0x03 => some EmergencyCommand.RECOVER
  | 0x04 => some EmergencyCommand.DIAG
  | 0x05 => some EmergencyCommand.STATUS
  | 0x06 => some EmergencyCommand.OPTICAL
  | 0x07 => some EmergencyCommand.FIBER
  | 0x08 => some EmergencyCommand.GRAPHENE
  | 0x09 => some EmergencyCommand.GAN
  | 0x0A => some EmergencyCommand.MEMRISTOR
  | 0x0B => some EmergencyCommand.VOLTAGE
  | 0xFF => some EmergencyCommand.EXIT
  | _    => none

-- ============================================================================
-- Status Byte (1-byte system health bitmap)
-- ============================================================================

structure StatusByte where
  powerOk : Bool           -- Bit 0: Main power within safe range
  seedValid : Bool         -- Bit 1: Geometric seed extracted and verified
  tsmReconstructed : Bool  -- Bit 2: TSM-VDP ISA word reconstructed
  starkValid : Bool        -- Bit 3: ZK-STARK proof validated
  opticalPathHot : Bool    -- Bit 4: 0 = hot priority, 1 = cold priority
  outerRingHealthy : Bool  -- Bit 5: Cold outer optical ring operational
  emNeutralityOk : Bool    -- Bit 6: EM neutrality verified
  voltageCompActive : Bool -- Bit 7: Voltage differential computation active
  deriving Repr, BEq

/-- Encode status byte to UInt8. -/
def statusByteToUInt8 (s : StatusByte) : UInt8 :=
  let b0 := if s.powerOk           then 0x01 else 0x00
  let b1 := if s.seedValid         then 0x02 else 0x00
  let b2 := if s.tsmReconstructed  then 0x04 else 0x00
  let b3 := if s.starkValid        then 0x08 else 0x00
  let b4 := if s.opticalPathHot    then 0x00 else 0x10  -- inverted: hot=0
  let b5 := if s.outerRingHealthy  then 0x20 else 0x00
  let b6 := if s.emNeutralityOk    then 0x40 else 0x00
  let b7 := if s.voltageCompActive then 0x80 else 0x00
  b0 ||| b1 ||| b2 ||| b3 ||| b4 ||| b5 ||| b6 ||| b7

/-- Decode UInt8 to status byte. -/
def uint8ToStatusByte (b : UInt8) : StatusByte :=
  { powerOk           := (b &&& 0x01) != 0,
    seedValid         := (b &&& 0x02) != 0,
    tsmReconstructed  := (b &&& 0x04) != 0,
    starkValid        := (b &&& 0x08) != 0,
    opticalPathHot    := (b &&& 0x10) == 0,  -- inverted: 0 = hot
    outerRingHealthy  := (b &&& 0x20) != 0,
    emNeutralityOk    := (b &&& 0x40) != 0,
    voltageCompActive := (b &&& 0x80) != 0
  }

-- ============================================================================
-- Command Response Types
-- ============================================================================

inductive CommandResult where
  | ok        -- Command executed successfully
  | invalid   -- Invalid command or parameters
  | busy      -- System busy, command queued
  | error     -- Execution error
  | forbidden -- Command not allowed in current phase
  deriving Repr, BEq

structure CommandResponse where
  result : CommandResult
  status : StatusByte
  payloadLength : Nat
  deriving Repr

-- ============================================================================
-- Cooperative Process Definitions (Tiny IP event loop extensions)
-- ============================================================================

/-- Process states for the cooperative event loop. -/
inductive ProcessState where
  | idle      -- Process waiting for event
  | running   -- Process currently executing
  | blocked   -- Process waiting for I/O or timer
  | done      -- Process completed, results available
  | error     -- Process failed with error code
  deriving Repr, BEq

structure GeometryScanProcess where
  state : ProcessState
  scan : ScanState
  deriving Repr

structure SeedAssemblyProcess where
  state : ProcessState
  seed : Option Nat
  deriving Repr

structure TsmReconstructProcess where
  state : ProcessState
  isaWord : Option Nat
  deriving Repr

structure EmergencyShellProcess where
  state : ProcessState
  lastCommand : Option EmergencyCommand
  deriving Repr

structure PowerMonitorProcess where
  state : ProcessState
  power : PowerState
  deriving Repr

structure OpticalPathManager where
  state : ProcessState
  currentPriority : OpticalPath
  activePaths : Nat
  deriving Repr

structure MemristorManager where
  state : ProcessState
  memristors : Array GrapheneMemristor
  deriving Repr

structure VoltageComputationManager where
  state : ProcessState
  voltagePaths : Array VoltageDifferential
  deriving Repr

-- ============================================================================
-- Shell Command Execution
-- ============================================================================

/-- Derive status byte from current boot phase and power state. -/
def statusFromBootState (s : EmergencyBootState) : StatusByte :=
  { powerOk           := ge s.power.vccMain (ofRatio 60 1000),
    seedValid         := s.seed.isSome,
    tsmReconstructed  := s.isaWord.isSome,
    starkValid        := s.phase == BootPhase.validated || s.phase == BootPhase.recoveryMode,
    opticalPathHot    := s.power.opticalPathPriority == OpticalPath.hot,
    outerRingHealthy  := s.phase != BootPhase.idle && s.phase != BootPhase.powerFail,
    emNeutralityOk    := s.phase != BootPhase.idle,
    voltageCompActive := s.phase == BootPhase.recoveryMode
  }

/-- Execute a command against the current emergency boot state.
    Returns updated state and response. This is the core dispatch function. -/
def executeCommand
    (cmd : EmergencyCommand)
    (bootState : EmergencyBootState)
    (payload : List UInt8)
    : EmergencyBootState × CommandResponse :=
  let status := statusFromBootState bootState
  match cmd with
  | EmergencyCommand.BOOT =>
      if bootState.phase == BootPhase.seedReady ||
         bootState.phase == BootPhase.recoveryMode then
        let resp := { result := CommandResult.ok, status := status, payloadLength := 16 }
        (bootState, resp)
      else
        let resp := { result := CommandResult.forbidden, status := status, payloadLength := 0 }
        (bootState, resp)
  | EmergencyCommand.SCAN =>
      if bootState.phase == BootPhase.scanning ||
         bootState.phase == BootPhase.seedReady ||
         bootState.phase == BootPhase.recoveryMode then
        let resp := { result := CommandResult.ok, status := status, payloadLength := 0 }
        (bootState, resp)
      else
        let resp := { result := CommandResult.forbidden, status := status, payloadLength := 0 }
        (bootState, resp)
  | EmergencyCommand.STATUS =>
      let resp := { result := CommandResult.ok, status := status, payloadLength := 1 }
      (bootState, resp)
  | EmergencyCommand.DIAG =>
      let resp := { result := CommandResult.ok, status := status, payloadLength := 0 }
      (bootState, resp)
  | EmergencyCommand.EXIT =>
      if bootState.phase == BootPhase.recoveryMode then
        let newState := { bootState with phase := BootPhase.exiting }
        let resp := { result := CommandResult.ok, status := status, payloadLength := 0 }
        (newState, resp)
      else
        let resp := { result := CommandResult.forbidden, status := status, payloadLength := 0 }
        (bootState, resp)
  | _ =>
      -- OPTICAL, FIBER, GRAPHENE, GAN, MEMRISTOR, VOLTAGE, RECOVER
      -- All require recovery mode or later phases
      if bootState.phase == BootPhase.recoveryMode then
        let resp := { result := CommandResult.ok, status := status, payloadLength := 0 }
        (bootState, resp)
      else
        let resp := { result := CommandResult.forbidden, status := status, payloadLength := 0 }
        (bootState, resp)

-- ============================================================================
-- Verification Lemmas
-- ============================================================================

/-- Command opcode round-trip: parse ∘ commandOpcode = some for known commands. -/
theorem commandOpcode_roundTrip (cmd : EmergencyCommand) :
  parseOpcode (commandOpcode cmd) = some cmd := by
  cases cmd <;> rfl

#eval
  let idleState := initEmergencyBoot 0 {
    vccMain := ofRatio 60 1000,
    watchdogCountdown := 0,
    bridgeIsolated := true,
    opticalPathPriority := OpticalPath.hot,
    activeHotPaths := 0,
    solarState := {
      solarInputVoltage := ofInt 0,
      solarInputCurrent := ofInt 0,
      powerGeneration := ofInt 0,
      batteryLevel := ofInt 0,
      selfPowerMode := false
    }
  }
  (executeCommand EmergencyCommand.BOOT idleState []).2.result == CommandResult.forbidden

end Semantics.Hardware.EmergencyBoot
