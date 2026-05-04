#!/usr/bin/env python3
"""IBM-II-class software Ethernet controller for Omnitoken scalar/LUT intake."""

from __future__ import annotations

import argparse
import random
import struct
import zlib
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


ETHERTYPE_OMNITOKEN = 0x88B5
MIN_ETH_FRAME = 64
MAX_ETH_FRAME = 1518
RX_RING_SLOTS = 4
RX_SLOT_BYTES = 160

DOMAIN_HEALTH = 0x01
DOMAIN_ACK = 0x0A
DOMAIN_RECOVER = 0x0D
DOMAIN_REFUSE = 0x0F
SCALAR_DEFAULT = 0x01

LUT = {
    (DOMAIN_HEALTH, SCALAR_DEFAULT): "health",
    (DOMAIN_ACK, SCALAR_DEFAULT): "ack",
    (DOMAIN_RECOVER, SCALAR_DEFAULT): "recover",
    (DOMAIN_REFUSE, SCALAR_DEFAULT): "refuse",
}

HOST_MAC = bytes.fromhex("020000000001")
NODE_MAC_PREFIX = bytes.fromhex("0200000000")


@dataclass(frozen=True)
class EthernetFrame:
    raw: bytes


@dataclass
class ControllerStats:
    rx_seen: int = 0
    rx_admitted: int = 0
    rx_runt: int = 0
    rx_oversize: int = 0
    rx_bad_fcs: int = 0
    rx_wrong_shell: int = 0
    rx_bad_lut: int = 0
    rx_ring_overflow: int = 0
    rx_slot_overflow: int = 0
    recovered: int = 0


@dataclass
class RecoveryEvent:
    src_mac: str
    domain: int
    scalar: int
    action: str
    shell: str = "ethernet"


@dataclass
class IbmIiEthernetController:
    """A tiny software NIC surface with fixed memory and no dynamic parsing."""

    rx_ring: Deque[EthernetFrame] = field(default_factory=lambda: deque(maxlen=RX_RING_SLOTS))
    stats: ControllerStats = field(default_factory=ControllerStats)
    events: list[RecoveryEvent] = field(default_factory=list)

    def receive(self, frame: EthernetFrame) -> None:
        self.stats.rx_seen += 1
        if len(frame.raw) > RX_SLOT_BYTES:
            self.stats.rx_slot_overflow += 1
            return
        if len(self.rx_ring) == self.rx_ring.maxlen:
            self.stats.rx_ring_overflow += 1
            self.rx_ring.popleft()
        self.rx_ring.append(frame)

    def poll(self) -> None:
        while self.rx_ring:
            self._process(self.rx_ring.popleft())

    def _process(self, frame: EthernetFrame) -> None:
        raw = frame.raw
        if len(raw) < MIN_ETH_FRAME:
            self.stats.rx_runt += 1
            return
        if len(raw) > MAX_ETH_FRAME:
            self.stats.rx_oversize += 1
            return
        if not valid_fcs(raw):
            self.stats.rx_bad_fcs += 1
            return

        dst, src, ethertype = struct.unpack("!6s6sH", raw[:14])
        if dst not in (HOST_MAC, b"\xff\xff\xff\xff\xff\xff"):
            self.stats.rx_wrong_shell += 1
            return
        if ethertype != ETHERTYPE_OMNITOKEN:
            self.stats.rx_wrong_shell += 1
            return

        shell_payload = raw[14:-4]
        if len(shell_payload) < 2:
            self.stats.rx_bad_lut += 1
            return
        if any(shell_payload[2:]):
            self.stats.rx_wrong_shell += 1
            return
        domain, scalar = shell_payload[0], shell_payload[1]
        action = LUT.get((domain, scalar))
        if action is None:
            self.stats.rx_bad_lut += 1
            return

        self.stats.rx_admitted += 1
        if action == "recover":
            self.stats.recovered += 1
            self.events.append(
                RecoveryEvent(src_mac=src.hex(":"), domain=domain, scalar=scalar, action=action)
            )

    def jsonl_events(self) -> list[str]:
        lines: list[str] = []
        for seq, event in enumerate(self.events, start=1):
            lines.append(
                "{"
                f'"v":"hs-jsonl-0.1",'
                f'"id":"ibmii:ethernet:recover:{seq:04d}",'
                '"op":"recover",'
                '"surface":{"class":"node","kind":"ibmii.software_ethernet","caps":["recover"]},'
                '"gcl":{"admission":"admitted","capability_tier":"T1_8kb","invariant":"scalar_lut_before_shell"},'
                f'"omni":{{"domain":"0x{event.domain:02X}","scalar":"0x{event.scalar:02X}","op_id":"0x0D","shell":"{event.shell}"}},'
                f'"provenance":{{"origin":"mac:{event.src_mac}","node":"ibmii-controller"}},'
                '"privacy":{"tier":"internal","retention":"cache","export":"deny","redaction":"none"}'
                "}"
            )
        return lines


def valid_fcs(raw: bytes) -> bool:
    if len(raw) < 4:
        return False
    body, fcs_bytes = raw[:-4], raw[-4:]
    expected = zlib.crc32(body) & 0xFFFFFFFF
    actual = struct.unpack("<I", fcs_bytes)[0]
    return actual == expected


def make_frame(src_node: int, payload: bytes, *, ethertype: int = ETHERTYPE_OMNITOKEN) -> EthernetFrame:
    src = NODE_MAC_PREFIX + bytes([src_node & 0xFF])
    body = HOST_MAC + src + struct.pack("!H", ethertype) + payload
    if len(body) < MIN_ETH_FRAME - 4:
        body += b"\x00" * ((MIN_ETH_FRAME - 4) - len(body))
    fcs = struct.pack("<I", zlib.crc32(body) & 0xFFFFFFFF)
    return EthernetFrame(body + fcs)


def corrupt_fcs(frame: EthernetFrame) -> EthernetFrame:
    raw = bytearray(frame.raw)
    raw[-1] ^= 0x80
    return EthernetFrame(bytes(raw))


def run(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    ctl = IbmIiEthernetController()
    for node in range(1, args.nodes + 1):
        payload = bytes([DOMAIN_RECOVER, SCALAR_DEFAULT])
        frame = make_frame(node, payload)
        if rng.random() < args.bad_fcs:
            frame = corrupt_fcs(frame)
        if rng.random() < args.wrong_shell:
            frame = make_frame(node, payload, ethertype=0x0800)
        if rng.random() < args.bad_lut:
            frame = make_frame(node, bytes([0xEE, 0xEE]))
        ctl.receive(frame)
        if rng.random() >= args.burst:
            ctl.poll()
    ctl.poll()

    for line in ctl.jsonl_events()[: args.emit_jsonl]:
        print(line)
    print(
        "ibmii-eth result: "
        f"recovered={ctl.stats.recovered}/{args.nodes} admitted={ctl.stats.rx_admitted} "
        f"seen={ctl.stats.rx_seen} ring_overflow={ctl.stats.rx_ring_overflow} "
        f"slot_overflow={ctl.stats.rx_slot_overflow} bad_fcs={ctl.stats.rx_bad_fcs} "
        f"wrong_shell={ctl.stats.rx_wrong_shell} bad_lut={ctl.stats.rx_bad_lut}"
    )
    return 0 if ctl.stats.recovered >= args.quorum else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=int, default=10)
    parser.add_argument("--quorum", type=int, default=None)
    parser.add_argument("--seed", type=int, default=5150)
    parser.add_argument("--bad-fcs", type=float, default=0.0)
    parser.add_argument("--wrong-shell", type=float, default=0.0)
    parser.add_argument("--bad-lut", type=float, default=0.0)
    parser.add_argument("--burst", type=float, default=0.0, help="chance to defer polling and stress the RX ring")
    parser.add_argument("--emit-jsonl", type=int, default=0)
    args = parser.parse_args()
    if args.nodes < 1:
        parser.error("--nodes must be >= 1")
    if args.quorum is None:
        args.quorum = args.nodes
    if not 1 <= args.quorum <= args.nodes:
        parser.error("--quorum must be between 1 and --nodes")
    for name in ("bad_fcs", "wrong_shell", "bad_lut", "burst"):
        value = getattr(args, name)
        if not 0.0 <= value <= 1.0:
            parser.error(f"--{name.replace('_', '-')} must be between 0 and 1")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
