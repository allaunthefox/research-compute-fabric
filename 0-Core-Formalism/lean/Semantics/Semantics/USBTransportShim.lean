/-
USBTransportShim.lean — AVM→USB transport bridge shim.

This file defines the types and interface for USB transport operations,
including RDMA over USB and FPGA serial transport modes (UART/braid/PBACS).
All actual I/O is performed by the Rust runtime when it interprets AVM programs.
The AVM dispatch table in AVM.lean is the sole entry point — no Lean, Rust,
or Python code calls USB directly without going through the AVM.
-/

import Semantics.AVM
import Semantics.FixedPoint

open Semantics.AVM

namespace Semantics.USBTransport

/-- USB transport frame type. Mirrors the wire protocol:
    | magic (4) | ver (1) | type (1) | seq (4) | len (4) | payload | -/
structure USBFrame where
  magic : UInt32
  version : UInt8
  msgType : UInt8
  seq : UInt32
  payload : String
  deriving Repr

/-- USB link status. -/
inductive LinkStatus where
  | up
  | down
  | init
  deriving Repr, BEq

/-- Predefined USB transport addresses. -/
def hostIp : String := "192.168.2.1"
def deviceIp : String := "192.168.2.2"
def transportPort : UInt32 := 9735

/-! ## FPGA Serial Transport over USB -/

/-- USB transport sub-mode for FPGA fabric serial. The USB CDC Ethernet link
    carries serial frames to/from the external USB-UART adapter on fabric pins
    17(TX)/18(RX), or directly to the braid_serial.v / pbacs_1bit_transport_core
    when those are the active bitstream. -/
inductive SerialOverUsbMode
  | uart        -- Standard UART framed protocol (0xA5/0xA6 magic, XOR CRC)
  | braid       -- 8-wire braid encoding (BraidSerial.lean)
  | pbacs_1bit  -- 1-bit PBACS delta-sigma transport
  deriving Repr, BEq, DecidableEq

/-- Serial frame envelope tunneled through the USB transport.
    The USB frame carries this as its payload, with msgType indicating
    serial mode: 0x10=UART, 0x11=Braid, 0x12=PBACS. -/
structure SerialTunnelFrame where
  mode : SerialOverUsbMode
  seq : UInt32
  payload : List UInt8
  crc : UInt8
  deriving Repr, BEq

/-- Route table for serial transport over USB.
    Matches the tang9k_uart_transport_router.py structure. -/
structure SerialRouteEntry where
  name : String
  path : String
  online : Bool
  deriving Repr, BEq

/-- Current serial route table. -/
def serialRouteTable : List SerialRouteEntry :=
  [ { name := "onboard-ftdi-a",  path := "/dev/ttyUSB0", online := false }
  , { name := "onboard-ftdi-b",  path := "/dev/ttyUSB1", online := false }
  , { name := "external-usb-uart", path := "/dev/ttyUSB2", online := false }
  , { name := "virtual-q16-pty", path := "virtual://q16-pty", online := true }
  ]

/-! ## RDMA over USB -/

/-- RDMA data tunneled over USB transport. The USB CDC Ethernet link between
    laptop (192.168.2.1) and Steam Deck (192.168.2.2) acts as the RDMA fabric,
    with the USB gadget's DMA shared memory as the registered memory region. -/
structure RDMATunnelFrame where
  qpn : UInt32            -- Queue Pair Number
  wrType : UInt8          -- 0=SEND, 1=WRITE, 2=READ
  lkey : UInt32           -- Local key
  remoteAddr : UInt64     -- Remote buffer address
  rkey : UInt32           -- Remote key
  payloadLen : UInt32
  deriving Repr, BEq

/-! ## Bluetooth over USB -/

/-- BT frame tunneled through the USB transport (msgType 0x20). -/
struct BTTunnelFrame where
  modeByte : UInt8         -- 0=classic, 1=BLE, 2=BT mesh
  peerAddr : UInt64        -- BT MAC
  seq : UInt32
  payload : List UInt8
  rssi : Int32
  deriving Repr, BEq

/-! ## WiFi over USB -/

/-- WiFi frame tunneled through USB transport (msgType 0x21). -/
struct WiFiTunnelFrame where
  modeByte : UInt8         -- 0=ad-hoc, 1=WiFi Direct, 2=SoftAP
  bssid : UInt64           -- BSSID (48-bit MAC)
  seq : UInt32
  payload : List UInt8
  rssi : Int32
  channel : UInt8
  deriving Repr, BEq

/-! ## Mesh Transport Selector -/

/-- Composite mesh header for transport-agnostic routing.
    Carried as USB payload, msgType 0x22. -/
struct MeshTunnelHeader where
  srcPeer : UInt64
  dstPeer : UInt64
  transportUsed : UInt8    -- 0=USB, 1=WiFi, 2=BT, 3=Serial
  hopCount : UInt8
  ttl : UInt8
  deriving Repr, BEq

end Semantics.USBTransport
