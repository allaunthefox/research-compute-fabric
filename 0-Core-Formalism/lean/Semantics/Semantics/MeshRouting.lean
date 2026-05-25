/-
MeshRouting.lean — Unified transport encoding across all channels.

Binds together the agent designs for:
  - TMDS lane encoding (HDMI/DP PHY — Agent 1)
  - VCN video encode/decode (MKV trick — Agent 2)
  - Multi-transport selection, fragmentation, fallback (Agent 3)

No dependency on NICProbe or ASICTopology to avoid circular imports.
Types shared with NICProbe are duplicated here at the shim boundary.
-/

import Semantics.FixedPoint
import Mathlib.Data.UInt

namespace Semantics.MeshRouting

open Semantics

/-! ## Transport Layer Enum (mirror of NICProbe.TransportLayer) -/

/-- Transport layer selector — mirrors NICProbe.TransportLayer. -/
inductive TransportLayer
  | usbDma
  | wifi
  | bluetooth
  | serial
  deriving Repr, BEq, DecidableEq

/-- MTU per transport. -/
def transportMTU (t : TransportLayer) : Nat :=
  match t with
  | TransportLayer.usbDma => 65536
  | TransportLayer.wifi => 1472
  | TransportLayer.bluetooth => 251
  | TransportLayer.serial => 8

/-- Latency per transport in Q16_16 (fractional ms). -/
def transportLatency (t : TransportLayer) : Q16_16 :=
  match t with
  | TransportLayer.usbDma => 0x00010000
  | TransportLayer.wifi => 0x000A0000
  | TransportLayer.bluetooth => 0x001E0000
  | TransportLayer.serial => 0x00050000

/-- Priority (lower = preferred). -/
def transportPriority (t : TransportLayer) : Nat :=
  match t with
  | TransportLayer.usbDma => 0
  | TransportLayer.wifi => 1
  | TransportLayer.bluetooth => 2
  | TransportLayer.serial => 3

/-! ## Unified Transport Envelope -/

/-- Transport discriminator tag (byte 0 of every wire frame). -/
def transportTag (t : TransportLayer) : UInt8 :=
  match t with
  | TransportLayer.usbDma => 0x00
  | TransportLayer.wifi => 0x01
  | TransportLayer.bluetooth => 0x02
  | TransportLayer.serial => 0x03

/-- Transport-specific header size per tag. -/
def transportHeaderSize (tag : UInt8) : Nat :=
  match tag with
  | 0x00 => 4   -- USB: sessionId
  | 0x01 => 4   -- WiFi: srcPort + dstPort
  | 0x02 => 2   -- BT: cid
  | 0x03 => 1   -- Serial: mode
  | 0x04 => 1   -- TMDS: configId
  | 0x05 => 5   -- VCN: codec + seq
  | 0x06 => 2   -- AUX: addr
  | _    => 0

/-- RDMA net header (mirror of NICProbe.RDMANetHeader, 41 bytes wire format). -/
structure RDMANetHeader where
  version : UInt8          -- = 1
  transport : UInt8        -- 0=USB, 1=WiFi, 2=BT, 3=Serial
  wrType : UInt8           -- 0=SEND, 1=WRITE, 2=READ
  qpn : UInt32
  lkey : UInt32
  rkey : UInt32
  localAddr : UInt64
  remoteAddr : UInt64
  length : UInt32
  seq : UInt32
  flags : UInt16
  deriving Repr, BEq

/-- Serialize RDMANetHeader to wire bytes (41 bytes).
    Manual byte extraction to avoid dependency on toLEBytes. -/
def rdmaNetHeaderBytes (h : RDMANetHeader) : List UInt8 :=
  let tagByte := h.version
  let txpByte := h.transport
  let wrByte := h.wrType
  -- 32-bit values as 4 bytes each (little-endian manual)
  let qpn := [UInt8.ofNat (h.qpn.toNat % 256), UInt8.ofNat ((h.qpn.toNat / 256) % 256),
              UInt8.ofNat ((h.qpn.toNat / 65536) % 256), UInt8.ofNat ((h.qpn.toNat / 16777216) % 256)]
  let lkey := [UInt8.ofNat (h.lkey.toNat % 256), UInt8.ofNat ((h.lkey.toNat / 256) % 256),
               UInt8.ofNat ((h.lkey.toNat / 65536) % 256), UInt8.ofNat ((h.lkey.toNat / 16777216) % 256)]
  let rkey := [UInt8.ofNat (h.rkey.toNat % 256), UInt8.ofNat ((h.rkey.toNat / 256) % 256),
               UInt8.ofNat ((h.rkey.toNat / 65536) % 256), UInt8.ofNat ((h.rkey.toNat / 16777216) % 256)]
  -- 64-bit values as 8 bytes each
  let localAddr := List.range 8 |>.map (fun i => UInt8.ofNat ((h.localAddr.toNat / (256 ^ i)) % 256))
  let remoteAddr := List.range 8 |>.map (fun i => UInt8.ofNat ((h.remoteAddr.toNat / (256 ^ i)) % 256))
  let len := [UInt8.ofNat (h.length.toNat % 256), UInt8.ofNat ((h.length.toNat / 256) % 256),
              UInt8.ofNat ((h.length.toNat / 65536) % 256), UInt8.ofNat ((h.length.toNat / 16777216) % 256)]
  let seq := [UInt8.ofNat (h.seq.toNat % 256), UInt8.ofNat ((h.seq.toNat / 256) % 256),
              UInt8.ofNat ((h.seq.toNat / 65536) % 256), UInt8.ofNat ((h.seq.toNat / 16777216) % 256)]
  let flags := [UInt8.ofNat (h.flags.toNat % 256), UInt8.ofNat (h.flags.toNat / 256)]
  [tagByte, txpByte, wrByte] ++ qpn ++ lkey ++ rkey ++ localAddr ++ remoteAddr ++ len ++ seq ++ flags

/-- Unified transport envelope. -/
structure TransportEnvelope where
  tag : UInt8
  transportHdr : List UInt8
  rdmaHdr : RDMANetHeader
  payload : List UInt8
  deriving Repr, BEq

/-- Serialize envelope to wire bytes. -/
def serializeEnvelope (env : TransportEnvelope) : List UInt8 :=
  env.tag :: env.transportHdr ++ rdmaNetHeaderBytes env.rdmaHdr ++ env.payload

/-- Fragment header prepended to each payload chunk. -/
structure FragmentHeader where
  fragSeq : UInt16
  totalFrags : UInt8
  flags : UInt8          -- bit 0=START, bit 1=END, bit 2=RETRANS
  deriving Repr, BEq

/-- Fragment header size in bytes. -/
def fragmentHeaderSize : Nat := 4

/-- Serialize fragment header. -/
def serializeFragmentHdr (fh : FragmentHeader) : List UInt8 :=
  let seqLo := UInt8.ofNat (fh.fragSeq.toNat % 256)
  let seqHi := UInt8.ofNat (fh.fragSeq.toNat / 256)
  [seqLo, seqHi, fh.totalFrags, fh.flags]

/-- Split a list into chunks of at most n bytes. -/
partial def chunkList (bytes : List UInt8) (n : Nat) : List (List UInt8) :=
  let rec go (remaining : List UInt8) (acc : List (List UInt8)) :=
    if remaining.isEmpty then acc.reverse
    else go (remaining.drop n) (remaining.take n :: acc)
  go bytes []

/-- Fragment an envelope at the transport's MTU boundary. -/
def fragmentEnvelope (env : TransportEnvelope) (mtu : Nat) : List (FragmentHeader × List UInt8) :=
  let hdrSize := 1 + env.transportHdr.length + 41
  if mtu ≤ hdrSize + fragmentHeaderSize then [] else
    let maxPayload := mtu - hdrSize - fragmentHeaderSize
    let chunks := chunkList env.payload maxPayload
    let totalFrags := chunks.length.toUInt8
    let rec tagFrags (chunks : List (List UInt8)) (seq : UInt16) (acc : List (FragmentHeader × List UInt8)) :=
      match chunks with
      | [] => acc.reverse
      | c :: rest =>
        let startFlag := if seq == 0 then 1 else 0
        let endFlag := if rest.isEmpty then 2 else 0
        let fh : FragmentHeader := { fragSeq := seq, totalFrags := totalFrags, flags := startFlag ||| endFlag }
        tagFrags rest (seq + 1) ((fh, c) :: acc)
    tagFrags chunks 0 []

/-! ## Transport Selection -/

/-- Cost function for transport selection (lower = better). -/
def transportCost (txp : TransportLayer) (payloadLen : Nat) : Nat :=
  let bwMbps := match txp with
    | TransportLayer.usbDma => 3840
    | TransportLayer.wifi => 150
    | TransportLayer.bluetooth => 3
    | TransportLayer.serial => 1
  let latMs := match txp with
    | TransportLayer.usbDma => 1
    | TransportLayer.wifi => 10
    | TransportLayer.bluetooth => 30
    | TransportLayer.serial => 5
  let mtu := transportMTU txp
  let frags := (payloadLen + mtu - 1) / mtu
  latMs * 1000 + (100000 / bwMbps) * 100 + frags * 10

/-- Select best transport from a set of reachable transports. -/
def selectBestTransport (payloadLen : Nat) (reachable : List TransportLayer) : Option TransportLayer :=
  match reachable with
  | [] => none
  | first :: rest =>
    let best := rest.foldl (fun (best : TransportLayer) (c : TransportLayer) =>
      if transportCost c payloadLen < transportCost best payloadLen then c else best) first
    some best

/-! ## Multi-Hop Re-Encapsulation -/

/-- Re-encapsulate for the next transport in a multi-hop route. -/
def reEncapForNextHop (env : TransportEnvelope) (nextTransport : TransportLayer) : TransportEnvelope :=
  let newTag := transportTag nextTransport
  let newHdrSize := transportHeaderSize newTag
  { tag := newTag
  , transportHdr := List.replicate newHdrSize 0
  , rdmaHdr := env.rdmaHdr
  , payload := env.payload }

/-! ## Fallback Chain -/

/-- Ordered fallback chain (ascending cost). -/
def fallbackChain (payloadLen : Nat) (reachable : List TransportLayer) : List TransportLayer :=
  reachable.insertionSort (fun a b => transportCost a payloadLen < transportCost b payloadLen)

/-- Fallback retry state. -/
structure FallbackState where
  remainingTransports : List TransportLayer
  currentTransport : Option TransportLayer
  retriesLeft : UInt8
  maxRetries : UInt8 := 3
  deriving Repr

/-- Advance to the next transport in the fallback chain. -/
def fallbackAdvance (fs : FallbackState) : FallbackState :=
  match fs.remainingTransports with
  | [] => { fs with currentTransport := none, remainingTransports := [] }
  | next :: rest => { currentTransport := some next, remainingTransports := rest, retriesLeft := fs.maxRetries }

/-! ## Multi-Transmit Striping -/

/-- Compute stripe planes for concurrent multi-transmit. -/
def computeStripePlanes (payload : List UInt8) (transports : List TransportLayer) : List (TransportLayer × List UInt8) :=
  let n := max transports.length 1
  let planeSize := (payload.length + n - 1) / n
  let rec go (remaining : List UInt8) (txps : List TransportLayer) (acc : List (TransportLayer × List UInt8)) :=
    match txps with
    | [] => acc.reverse
    | t :: rest =>
      let plane := remaining.take planeSize
      go (remaining.drop planeSize) rest ((t, plane) :: acc)
    termination_by txps.length
  go payload transports []

/-! ## Wiring to AVM dispatch (bridge methods) -/

/-- Build a TransportEnvelope from AVM stack parameters. -/
def makeEnvelope (tag : UInt8) (rdma : RDMANetHeader) (payload : List UInt8) : TransportEnvelope :=
  { tag := tag
  , transportHdr := List.replicate (transportHeaderSize tag) 0
  , rdmaHdr := rdma
  , payload := payload }

/-- Pick the right transport tag for a destination peer. -/
def peerTransportTag (peerAddr : UInt64) (preferred : TransportLayer) : UInt8 :=
  if peerAddr == 0 then transportTag TransportLayer.usbDma
  else if peerAddr == 1 then transportTag preferred
  else transportTag TransportLayer.wifi

end Semantics.MeshRouting
