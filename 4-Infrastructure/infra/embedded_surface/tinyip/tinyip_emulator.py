#!/usr/bin/env python3
"""Shell-agnostic tiny surface emulator for Omnitoken scalar/LUT payloads."""

from __future__ import annotations

import argparse
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


PROTO_SHELL = 1
ADDR_CONTROLLER = 0
MTU = 16

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


@dataclass(frozen=True)
class Packet:
    src: int
    dst: int
    proto: int
    seq: int
    ttl: int
    payload: bytes


@dataclass
class LinkEvent:
    deliver_at: int
    packet: Packet


@dataclass
class Stats:
    sent: int = 0
    delivered: int = 0
    dropped_loss: int = 0
    dropped_mtu: int = 0
    dropped_ttl: int = 0
    duplicate_ignored: int = 0
    acks: int = 0
    retransmits: int = 0
    dropped_lut: int = 0


@dataclass
class TinyNode:
    addr: int
    tx_interval: int = 11
    retry_interval: int = 17
    seq: int = 1
    acked: bool = False
    next_send: int = 0
    seen: set[tuple[int, int]] = field(default_factory=set)
    rx: Deque[Packet] = field(default_factory=lambda: deque(maxlen=4))
    tx: Deque[Packet] = field(default_factory=lambda: deque(maxlen=4))

    def tick(self, now: int, network: "TinyNetwork") -> None:
        self.drain_rx(now, network)
        if self.addr != ADDR_CONTROLLER and not self.acked and now >= self.next_send:
            payload = bytes([DOMAIN_RECOVER, SCALAR_DEFAULT])
            self.enqueue_tx(Packet(self.addr, ADDR_CONTROLLER, PROTO_SHELL, self.seq, 8, payload), network)
            self.next_send = now + self.retry_interval
            if self.seq > 1:
                network.stats.retransmits += 1
            self.seq += 1
        self.drain_tx(network)

    def enqueue_tx(self, packet: Packet, network: "TinyNetwork") -> None:
        if len(packet.payload) > MTU:
            network.stats.dropped_mtu += 1
            return
        if len(self.tx) == self.tx.maxlen:
            self.tx.popleft()
        self.tx.append(packet)

    def recv(self, packet: Packet, network: "TinyNetwork") -> None:
        if packet.ttl <= 0:
            network.stats.dropped_ttl += 1
            return
        if len(packet.payload) > MTU:
            network.stats.dropped_mtu += 1
            return
        key = (packet.src, packet.seq)
        if key in self.seen:
            network.stats.duplicate_ignored += 1
            return
        self.seen.add(key)
        if len(self.rx) == self.rx.maxlen:
            self.rx.popleft()
        self.rx.append(packet)

    def drain_tx(self, network: "TinyNetwork") -> None:
        while self.tx:
            network.send(self.tx.popleft())

    def drain_rx(self, now: int, network: "TinyNetwork") -> None:
        while self.rx:
            packet = self.rx.popleft()
            action = lut_action(packet.payload)
            if action is None:
                network.stats.dropped_lut += 1
                continue
            if self.addr == ADDR_CONTROLLER and action == "recover":
                network.recovered.add(packet.src)
                ack_payload = bytes([DOMAIN_ACK, SCALAR_DEFAULT])
                self.enqueue_tx(Packet(self.addr, packet.src, PROTO_SHELL, packet.seq, 8, ack_payload), network)
            elif action == "ack" and self.addr != ADDR_CONTROLLER:
                self.acked = True
                network.stats.acks += 1


class TinyNetwork:
    def __init__(self, loss: float, duplicate: float, reorder: float, seed: int) -> None:
        self.loss = loss
        self.duplicate = duplicate
        self.reorder = reorder
        self.rng = random.Random(seed)
        self.in_flight: list[LinkEvent] = []
        self.nodes: dict[int, TinyNode] = {}
        self.stats = Stats()
        self.recovered: set[int] = set()
        self.now = 0

    def add_node(self, node: TinyNode) -> None:
        self.nodes[node.addr] = node

    def send(self, packet: Packet) -> None:
        self.stats.sent += 1
        if self.rng.random() < self.loss:
            self.stats.dropped_loss += 1
            return
        delay = 1
        if self.rng.random() < self.reorder:
            delay += self.rng.randint(1, 7)
        self.in_flight.append(LinkEvent(self.now + delay, packet))
        if self.rng.random() < self.duplicate:
            self.in_flight.append(LinkEvent(self.now + delay + 1, packet))

    def deliver_ready(self) -> None:
        ready = [event for event in self.in_flight if event.deliver_at <= self.now]
        self.in_flight = [event for event in self.in_flight if event.deliver_at > self.now]
        self.rng.shuffle(ready)
        for event in ready:
            node = self.nodes.get(event.packet.dst)
            if node is not None:
                self.stats.delivered += 1
                node.recv(event.packet, self)


def lut_action(payload: bytes) -> str | None:
    if len(payload) != 2:
        return None
    return LUT.get((payload[0], payload[1]))


def run_sim(args: argparse.Namespace) -> int:
    net = TinyNetwork(args.loss, args.duplicate, args.reorder, args.seed)
    controller = TinyNode(ADDR_CONTROLLER)
    net.add_node(controller)
    for addr in range(1, args.nodes + 1):
        node = TinyNode(addr, next_send=addr % 5)
        net.add_node(node)

    for tick in range(args.ticks):
        net.now = tick
        net.deliver_ready()
        for node in list(net.nodes.values()):
            node.tick(tick, net)
        if len(net.recovered) >= args.quorum:
            break

    expected = set(range(1, args.nodes + 1))
    missing = sorted(expected - net.recovered)
    print(
        f"tinyip result: recovered={len(net.recovered)}/{args.nodes} "
        f"quorum={args.quorum} ticks={net.now}"
    )
    print(
        "stats "
        f"sent={net.stats.sent} delivered={net.stats.delivered} "
        f"loss={net.stats.dropped_loss} mtu_drop={net.stats.dropped_mtu} "
        f"ttl_drop={net.stats.dropped_ttl} dup_ignored={net.stats.duplicate_ignored} "
        f"lut_drop={net.stats.dropped_lut} acks={net.stats.acks} "
        f"retransmits={net.stats.retransmits} shell={args.shell}"
    )
    if missing:
        print("missing " + ",".join(str(node) for node in missing))
    if len(net.recovered) < args.quorum:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=int, default=10)
    parser.add_argument("--ticks", type=int, default=240)
    parser.add_argument("--loss", type=float, default=0.20)
    parser.add_argument("--duplicate", type=float, default=0.10)
    parser.add_argument("--reorder", type=float, default=0.10)
    parser.add_argument("--quorum", type=int, default=None)
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--shell", default="udp", help="local shell label, e.g. udp/onion/ipv923u")
    args = parser.parse_args()
    if args.nodes < 1:
        parser.error("--nodes must be >= 1")
    if args.quorum is None:
        args.quorum = args.nodes
    if not 1 <= args.quorum <= args.nodes:
        parser.error("--quorum must be between 1 and --nodes")
    for name in ("loss", "duplicate", "reorder"):
        value = getattr(args, name)
        if not 0.0 <= value <= 1.0:
            parser.error(f"--{name} must be between 0 and 1")
    return run_sim(args)


if __name__ == "__main__":
    raise SystemExit(main())
