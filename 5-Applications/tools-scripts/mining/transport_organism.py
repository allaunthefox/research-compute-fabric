#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Transport Organism

Applies the ENE organism model to transport decisions.
Instead of fixed protocols, transport adapts to:
- Payload structure (MI)
- Network conditions (regret)
- System constraints (geometry)

Transport action = argmax_m NetValue(m | z(x), state, constraints)

Derived from mimo-v2-pro / ChatGPT hybrid log.
"""

import json
import sys
import time
import hashlib
import zlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

from ene_mi_signal import MISignal, extract_mi_features
from omnitoken_metrics import OmnitokenMetrics, omnitoken_encode, omnitoken_decode
from network_security import NetworkSecurityPolicy
from context_gate import ContextGate, GateMode

# λ_b weight for bind_z contribution to structure_match utility (DAG 775).
# Calibrated range: c89cc=+5.84σ, urandom≈0σ, flat/spike≈-2.5σ.
# DAG 778 calibration: previous value 0.08 had max contribution +0.020, unable
# to overcome the zlib cpu_cost delta (0.10). Break-even requires λ_b ≥ 0.41
# for c89cc-class data (bind_z ≈ 5.84).
# Value 0.50:  c89cc (bz=5.84) → +0.022 utility (compress wins)
#              WN    (bz=-0.29) → -0.106 utility (no-compress wins)
#              English text (bz≈2.0) still uses MI path (mi>1.0 branch).
# Analysis: /tmp/lambda_b_calibration.py
LAMBDA_B: float = 0.50


@dataclass
class TransportAction:
    """A transport decision with rationale"""
    chunk_size: int          # bytes per chunk
    batch_size: int          # chunks per batch
    compress: bool           # enable compression
    compress_method: str     # 'zlib', 'lzma', 'none'
    framing: str             # 'omnitoken', 'json', 'binary'
    retry_policy: str        # 'aggressive', 'moderate', 'none'
    priority: str            # 'high', 'normal', 'low'
    
    # Rationale
    mi_score: float          # compressibility proxy: 1-entropy [0=incompressible, 1=constant]
    net_value: float         # utility of this choice
    regret: float            # expected regret vs alternatives
    surprise: float          # deviation from prediction


@dataclass
class TransportOutcome:
    """Measurable outcome of a transport action"""
    bytes_sent: int
    bytes_received: int
    latency_ms: float
    success: bool
    retries: int
    cpu_ms: float
    memory_kb: float


class TransportOrganism:
    """
    Adaptive transport selector using ENE geometry.
    
    Instead of:
        transport = fixed_protocol(payload)
    
    Does:
        transport = organism(payload, network_state, constraints)
    
    The organism learns:
        - When to compress vs not
        - Optimal chunk/batch sizes
        - When to retry vs fail fast
        - Framing strategy per payload type
    """
    
    def __init__(self, available_memory_kb: int = 512):
        self.mi = MISignal(low_mi_threshold=0.3, high_mi_threshold=0.7)
        self.metrics = OmnitokenMetrics()
        self.available_memory = available_memory_kb
        
        # Transport parameter ranges
        self.chunk_sizes = [64, 256, 1024, 4096, 16384, 65536]
        self.batch_sizes = [1, 4, 16, 64, 256]
        self.compress_methods = ['none', 'zlib', 'lzma']
        self.framings = ['omnitoken', 'json', 'binary']
        self.retry_policies = ['none', 'moderate', 'aggressive']
        
        # History
        self.outcome_history: deque = deque(maxlen=1000)
        self.security = NetworkSecurityPolicy(node_id='transport-organism')
        self.context_gate = ContextGate(
            smoother=self.security._smoother,
            warden_db_path='warden_attestation.db',
        )

    def _build_deterministic_manifest(self, data: bytes, action: TransportAction) -> Dict:
        """Create deterministic transport metadata with stable chunk hashes."""
        chunk_size = max(1, int(action.chunk_size))
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)] or [b""]
        chunk_hashes = [hashlib.sha256(chunk).hexdigest() for chunk in chunks]
        manifest = {
            'version': 1,
            'encoding': action.compress_method,
            'framing': action.framing,
            'chunk_size': chunk_size,
            'chunk_count': len(chunk_hashes),
            'payload_sha256': hashlib.sha256(data).hexdigest(),
            'chunk_hashes': chunk_hashes,
        }
        return manifest
    
    def _encode_action(self, action: TransportAction) -> bytes:
        """Encode action as Omnitoken packet"""
        return omnitoken_encode(
            f'transport:{action.framing}',
            action.net_value,
            {
                'chunk': str(action.chunk_size),
                'batch': str(action.batch_size),
                'compress': action.compress_method,
                'framing': action.framing,
                'retry': action.retry_policy,
                'priority': action.priority,
                'mi': f'{action.mi_score:.4f}',
                'regret': f'{action.regret:.4f}',
                'surprise': f'{action.surprise:.4f}',
            }
        )
    
    def _decode_action(self, packet: bytes) -> Optional[TransportAction]:
        """Decode Omnitoken packet to action"""
        decoded = omnitoken_decode(packet)
        if decoded is None:
            return None
        
        tags = decoded.get('tags', {})
        return TransportAction(
            chunk_size=int(tags.get('chunk', '1024')),
            batch_size=int(tags.get('batch', '16')),
            compress=tags.get('compress', 'none') != 'none',
            compress_method=tags.get('compress', 'none'),
            framing=tags.get('framing', 'omnitoken'),
            retry_policy=tags.get('retry', 'moderate'),
            priority=tags.get('priority', 'normal'),
            mi_score=float(tags.get('mi', '0')),
            net_value=decoded.get('value', 0),
            regret=float(tags.get('regret', '0')),
            surprise=float(tags.get('surprise', '0')),
        )
    
    def _compute_bind_z(self, data: bytes) -> Optional[float]:
        """Compute bind_z via eigenvalue-whitened PCA bind score (DAG 774/775).

        Returns None if the soliton geometry stack is unavailable.
        Lazy-initialises the soliton imports on first call; cached thereafter.
        bind_z > 0 = c89cc.sh-like (high code density); ≈ 0 = WN-like; < 0 = anti-correlated.
        """
        if not hasattr(self, '_bind_R_MAT'):
            try:
                import os
                import numpy as _np
                _base = os.path.dirname(os.path.abspath(__file__))
                sys.path.insert(0, os.path.join(_base, 'scripts'))
                sys.path.insert(0, os.path.join(_base, 'tools'))
                import soliton_constants as _sc
                import soliton_factory as _sf
                from geometry_bind import bind_score_whitened as _bsw, bind_z_score as _bzs
                self._bind_R_MAT  = _np.array(_sc.ROT_R,  dtype=_np.float64)
                self._bind_MU_VEC = _np.array(_sc.ROT_MU, dtype=_np.float64)
                self._bind_modes  = _sf._modes_from_bytes
                self._bind_score  = _bsw
                self._bind_z_fn   = _bzs
                self._bind_np     = _np
            except Exception as _e:
                # FIXED: Import failure now logged to stderr for visibility
                print(f"WARNING: transport_organism bind_z init failed: {_e}", file=sys.stderr)
                self._bind_R_MAT = None
        if self._bind_R_MAT is None:
            return None
        try:
            np    = self._bind_np
            modes = xp.array(self._bind_modes(data), dtype=xp.float64)
            f_rot = (self._bind_R_MAT.T @ (modes - self._bind_MU_VEC)).tolist()
            return self._bind_z_fn(self._bind_score(f_rot))
        except Exception as _e:
            # FIXED: Computation failure now logged to stderr for visibility
            print(f"WARNING: transport_organism bind_z compute failed: {_e}", file=sys.stderr)
            return None

    def _estimate_utility(self, action: TransportAction,
                          data: bytes, mi: float,
                          bind_z: Optional[float] = None,
                          predicted_gain: Optional[float] = None) -> float:
        """
        U_transport(a) = λ_s·success - λ_l·latency - λ_b·bandwidth
                         - λ_c·cpu - λ_r·recovery + λ_m·structure_match

        bind_z augments structure_match: positive values reward compression of
        code-dense data; negative reduce the compressibility estimate.
        """
        n = len(data)
        
        # Bandwidth cost (bytes transmitted)
        if action.compress:
            compressed_size = n * 0.5  # estimate
            bytes_transmitted = compressed_size + 32  # overhead
        else:
            bytes_transmitted = n
        
        bandwidth_cost = bytes_transmitted / 1048576  # normalize to MB
        
        # Latency estimate (ms)
        chunks = max(1, n // action.chunk_size)
        batches = max(1, chunks // action.batch_size)
        dispatch_overhead = batches * 0.001                                    # ms per batch
        encode_time = n / (500 * 1024 * 1024) * 1000 if action.compress else 0 # ms at 500 MB/s
        latency = dispatch_overhead + encode_time
        
        # CPU cost — LUT following the recovery_cost pattern two lines down
        cpu_cost = {'lzma': 5.0, 'zlib': 2.0}.get(action.compress_method, 1.0)
        
        # Recovery cost
        recovery_cost = {'none': 0, 'moderate': 1, 'aggressive': 3}[action.retry_policy]
        
        # Structure match bonus.
        # Unit map: three additive terms mix different original spaces —
        #   mi * 2.77:           mi ∈ [0,1]    → bonus ∈ [0, 2.77] utility units
        #                        (×2.77 restores nats-equiv magnitude: 0.5×8×ln2)
        #   LAMBDA_B * bind_z/6: bind_z ∈ ≈[-8,+8] → contribution ∈ [-0.25, +0.50]
        #                        (LAMBDA_B=0.50 scales σ-units into utility range)
        #   gain_adj = predicted_gain/10.0: gain ∈ ≈[-8,+8] bpb → adj ∈ [-0.4, +0.8]
        #                        (/10 is the dimensional bridge from bpb to utility)
        # All three terms are calibrated to roughly the same utility magnitude so
        # addition makes sense, but the /10 divisor for predicted_gain is empirical
        # (DAG 775), not derived from first principles.
        if mi > 0.35 and action.compress:
            structure_bonus = mi * 2.77  # high compressibility → reward compression
        elif mi < 0.25 and not action.compress:
            structure_bonus = 0.3  # near-random → reward not compressing
        else:
            structure_bonus = 0.0

        # λ_b: bind_z augments structure bonus for compress actions.
        # bind_z/6 clamped to [-0.5, 1.0]; with LAMBDA_B=0.50: contribution [-0.25, +0.50]
        if bind_z is not None and action.compress:
            structure_bonus += LAMBDA_B * max(-0.5, min(1.0, bind_z / 6.0))

        # History-informed adjustment (wired via predicted_gain from select_action)
        # predicted_gain is bpb gain from kNN over past outcomes;
        # gain_adj clamped to [-0.4, +0.8] to avoid overwhelming static terms.
        # Only applied once ≥3 points exist — prior to that kNN is noisy.
        if predicted_gain is not None and len(self.mi.points) >= 3 and action.compress:
            gain_adj = min(0.8, max(-0.4, predicted_gain / 10.0))
            structure_bonus += gain_adj

        # Utility
        utility = (
            -0.3 * bandwidth_cost
            - 0.2 * latency
            - 0.1 * cpu_cost
            - 0.15 * recovery_cost
            + 0.25 * structure_bonus
        )
        
        return utility
    
    def _predict_best_action(self, mi: float, data_size: int) -> TransportAction:
        """
        Rule-based prediction (will be overridden by ENE once enough history).
        
        Rules:
        - High MI → compress, larger chunks
        - Low MI → no compression, small chunks
        - Small data → single batch, aggressive retry
        - Large data → batched, moderate retry
        """
        if mi > 0.7:
            # Very high compressibility (constant/trivial) → aggressive compression
            chunk = 4096
            batch = 16
            compress = True
            method = 'zlib' if data_size < 65536 else 'lzma'
            retry = 'moderate'
        elif mi < 0.25:
            # Near-random → no compression
            chunk = 1024
            batch = 64
            compress = False
            method = 'none'
            retry = 'moderate'
        else:
            # Normal → balanced
            chunk = 1024
            batch = 16
            compress = True
            method = 'zlib'
            retry = 'moderate'
        
        if data_size < 1024:
            # Small data → single batch, quick
            batch = 1
            retry = 'none'
            priority = 'high'
        else:
            priority = 'normal'
        
        return TransportAction(
            chunk_size=chunk,
            batch_size=batch,
            compress=compress,
            compress_method=method,
            framing='omnitoken',
            retry_policy=retry,
            priority=priority,
            mi_score=mi,
            net_value=0.0,
            regret=0.0,
            surprise=0.0,
        )
    
    def _compute_surprise(self, predicted: TransportAction,
                          actual_mi: float) -> float:
        """How surprised is the organism by actual MI?"""
        predicted_mi = predicted.mi_score
        raw = abs(actual_mi - predicted_mi)
        return min(1.0, raw)  # [0,1] — was /2.0, halving the range
    
    def select_action(self, data: bytes) -> TransportAction:
        """
        Main entry point: choose transport action for given data.
        
        Flow:
        1. Extract features / MI
        2. Predict best action
        3. Score alternatives
        4. Return best + log
        """
        n = len(data)
        
        # Extract features
        features = extract_mi_features(data)
        # Compressibility proxy: 1 - normalized_entropy.
        # byte_entropy is HIGH for random (hard to compress), LOW for constant/pattern (easy).
        # Inverting gives mi=1.0 for perfectly compressible, mi=0.0 for incompressible.
        mi = 1.0 - float(features[0])
        bind_z = self._compute_bind_z(data)

        # Query accumulated bpb-gain history (fixed: was never called — write-only kNN)
        predicted_gain, _ = self.mi.predict_mi(features)  # bpb units; 0.0 when store empty

        # Predict
        predicted = self._predict_best_action(mi, n)

        # Score alternatives
        best_action = predicted
        best_utility = self._estimate_utility(predicted, data, mi, bind_z, predicted_gain)

        # Try a few variants
        variants = [
            TransportAction(
                chunk_size=1024, batch_size=64, compress=False,
                compress_method='none', framing='omnitoken',
                retry_policy='moderate', priority='normal',
                mi_score=mi, net_value=0, regret=0, surprise=0,
            ),
            TransportAction(
                chunk_size=4096, batch_size=16, compress=True,
                compress_method='zlib', framing='omnitoken',
                retry_policy='moderate', priority='normal',
                mi_score=mi, net_value=0, regret=0, surprise=0,
            ),
            # compress=True, retry='none' — previously missing; needed when data is
            # structured (high structure_bonus) but reliable (no retry overhead)
            TransportAction(
                chunk_size=4096, batch_size=16, compress=True,
                compress_method='zlib', framing='omnitoken',
                retry_policy='none', priority='normal',
                mi_score=mi, net_value=0, regret=0, surprise=0,
            ),
            TransportAction(
                chunk_size=4096, batch_size=8, compress=True,
                compress_method='lzma', framing='omnitoken',
                retry_policy='aggressive', priority='normal',
                mi_score=mi, net_value=0, regret=0, surprise=0,
            ),
            TransportAction(
                chunk_size=256, batch_size=256, compress=False,
                compress_method='none', framing='json',
                retry_policy='none', priority='high',
                mi_score=mi, net_value=0, regret=0, surprise=0,
            ),
        ]

        for variant in variants:
            u = self._estimate_utility(variant, data, mi, bind_z, predicted_gain)
            if u > best_utility:
                best_utility = u
                best_action = variant

        # Set net value
        best_action.net_value = best_utility

        # Log to metrics
        self.metrics.record('transport.mi', mi)
        self.metrics.record('transport.bind_z', bind_z if bind_z is not None else 0.0)
        self.metrics.record('transport.net_value', best_utility)
        self.metrics.record('transport.chunk_size', best_action.chunk_size)
        self.metrics.record('transport.compress', 1.0 if best_action.compress else 0.0)
        
        return best_action
    
    def gate_for_context(
        self,
        payload: str | dict,
        mode: GateMode = GateMode.COMPRESS,
    ):
        """Run payload through the context gate before external ingestion.

        Call this on anything heading toward an LLM context window,
        MCP tool description, or agent prompt.  Returns a GateResult
        whose .safe_text is offensively boring.

        Default is COMPRESS — prefer local hyperlut/soliton surfaces
        and substrate cache over burning external context tokens.
        """
        return self.context_gate.process(payload, mode=mode)

    def execute(self, data: bytes, action: TransportAction) -> TransportOutcome:
        """
        Execute transport action and measure outcome.
        """
        import time

        t0 = time.time()

        # Deterministic transport manifest anchors payload + chunk ordering.
        manifest = self._build_deterministic_manifest(data, action)

        # Simulate encoding — use the method actually specified
        if action.compress_method == 'lzma':
            import lzma as _lzma
            encoded = _lzma.compress(data)
            bytes_sent = len(encoded)
        elif action.compress_method == 'zlib':
            encoded = zlib.compress(data, 9)
            bytes_sent = len(encoded)
        else:
            bytes_sent = len(data)
        
        # Simulate framing
        if action.framing == 'omnitoken':
            frame = omnitoken_encode('payload', bytes_sent, {
                'chunks': str(manifest['chunk_count']),
                'payload_sha256': manifest['payload_sha256'],
                'manifest_sha256': hashlib.sha256(
                    json.dumps(manifest, sort_keys=True).encode('utf-8')
                ).hexdigest(),
            })
            bytes_sent += len(frame)
        elif action.framing == 'json':
            frame = json.dumps({'manifest': manifest, 'len': len(data)}).encode()
            bytes_sent += len(frame)
        
        latency_ms = (time.time() - t0) * 1000
        
        outcome = TransportOutcome(
            bytes_sent=bytes_sent,
            bytes_received=0,
            latency_ms=latency_ms,
            success=True,
            retries=0,
            cpu_ms=latency_ms,
            memory_kb=bytes_sent / 1024,
        )
        
        # Record outcome
        self.outcome_history.append({
            'action': action,
            'outcome': outcome,
            'timestamp': time.time(),
        })
        
        # Log metrics
        self.metrics.record('transport.latency_ms', latency_ms)
        self.metrics.record('transport.bytes_sent', bytes_sent)
        
        return outcome
    
    def diff(self, action_a: TransportAction, 
             action_b: TransportAction) -> Dict:
        """
        Diff two transport actions.
        
        Returns: {changes: [...], magnitude: float}
        """
        changes = []
        
        if action_a.chunk_size != action_b.chunk_size:
            changes.append({
                'field': 'chunk_size',
                'from': action_a.chunk_size,
                'to': action_b.chunk_size,
                'delta': action_b.chunk_size - action_a.chunk_size,
            })
        
        if action_a.compress != action_b.compress:
            changes.append({
                'field': 'compress',
                'from': action_a.compress,
                'to': action_b.compress,
            })
        
        if action_a.compress_method != action_b.compress_method:
            changes.append({
                'field': 'compress_method',
                'from': action_a.compress_method,
                'to': action_b.compress_method,
            })
        
        if action_a.framing != action_b.framing:
            changes.append({
                'field': 'framing',
                'from': action_a.framing,
                'to': action_b.framing,
            })
        
        magnitude = len(changes) / 6.0  # max 6 fields
        
        return {
            'changes': changes,
            'magnitude': magnitude,
            'improvement': action_b.net_value - action_a.net_value,
        }
    
    def tag(self, action: TransportAction, 
            label: str, metadata: Dict = None) -> Dict:
        """
        Tag a transport action with metadata.
        
        Returns: tagged action record
        """
        return {
            'action': {
                'chunk_size': action.chunk_size,
                'batch_size': action.batch_size,
                'compress': action.compress_method,
                'framing': action.framing,
                'retry': action.retry_policy,
                'priority': action.priority,
            },
            'rationale': {
                'mi': action.mi_score,
                'net_value': action.net_value,
                'regret': action.regret,
                'surprise': action.surprise,
            },
            'tag': label,
            'metadata': metadata or {},
            'timestamp': time.time(),
        }
    
    def ingest(self, data: bytes, action: TransportAction,
               outcome: TransportOutcome) -> Dict:
        """
        Ingest transport decision + outcome into organism.
        
        1. Record in MI signal
        2. Update ENE geometry
        3. Log to DAG
        4. Update metrics
        """
        features = extract_mi_features(data)
        mi = 1.0 - float(features[0])  # compressibility proxy (see select_action)

        # Compute actual compression gain in bpb (C3 fix: was passing mi for both)
        # features[0] = byte_entropy = H(X)/8; recover H(X) to avoid rebuilding histogram.
        baseline_bpb = float(features[0]) * 8.0
        n = len(data)
        if n > 0 and outcome.bytes_sent > 0:
            actual_bpb = (outcome.bytes_sent * 8) / n
        elif n > 0 and outcome.bytes_sent == 0:
            # FIXED: Send failed entirely — nothing transmitted despite n>0 bytes.
            # actual_bpb = baseline_bpb would produce actual_mi=0 → regret=0, which is
            # indistinguishable from a perfect zero-gain result. Assign worst-case bpb
            # so regret=8.0 (below the 10.0 cap) for any action when the send failed.
            actual_bpb = baseline_bpb + 8.0
        else:
            actual_bpb = baseline_bpb
        actual_mi = baseline_bpb - actual_bpb  # positive = compression helped

        # Pre-predict before learning (fixed: was after learn() — posterior prediction
        # finds the just-added point as nearest neighbour, collapsing surprise to ~0 always)
        # ENE-B fix: capture neighbors to detect cold-start. predict_mi returns (0.0, [])
        # when no points exist → treating 0.0 as a real prior produces false surprise.
        predicted_bpb_gain, _pred_neighbors = self.mi.predict_mi(features)

        # Record in MI
        self.mi.learn(
            z=features,
            mi=actual_mi,
            method=action.compress_method,
            baseline_bpb=baseline_bpb,
            actual_bpb=actual_bpb,
        )

        # Compute regret: decision quality in bpb units (C4 fix: was utility vs entropy)
        # Did we make the right call about compression?
        compressed = action.compress_method != 'none'
        if compressed:
            regret = max(0.0, -actual_mi)              # compressed but gained nothing
        else:
            regret = max(0.0, actual_bpb - baseline_bpb)  # missed compression opportunity

        # Write back to action (TO-2: action.regret/surprise were always 0.0)
        # Cap at 10.0: tiny payloads with large framing overhead produce regret >> 1
        # (e.g. 1-byte payload + ~100B frame → regret≈792) which saturates DRIFT
        # threshold and masks real compression failures on normal payloads.
        action.regret = min(regret, 10.0)
        # Surprise: normalised deviation of actual from predicted bpb gain, clamped [0,1].
        # predicted_bpb_gain was computed above BEFORE learn() — true prior prediction.
        # ENE-B fix: skip surprise on cold-start (_pred_neighbors empty → no prior existed).
        if _pred_neighbors:
            action.surprise = min(1.0, abs(actual_mi - predicted_bpb_gain) / 8.0)
        else:
            action.surprise = 0.0
        
        # Log to DAG
        self.metrics.append_dag(
            op='TRANSPORT',
            status='STABLE' if regret < 0.5 else 'DRIFT',
        )
        
        return {
            'mi_entropy': mi,         # normalized byte entropy [0,1]
            'mi_gain': actual_mi,     # actual bpb gain from compression
            'regret': regret,
            'action': action.compress_method,
            'success': outcome.success,
            'latency_ms': outcome.latency_ms,
        }
    
    def push(self, packet: bytes, host: str = '127.0.0.1',
             port: int = 8446) -> bool:
        """
        Push transport packet to remote organism server via Omnitoken.
        """
        import socket
        
        try:
            # Outside-network traversal uses a minimal shell + PQ-encrypted internals.
            internal_payload = {
                'packet_hex': packet.hex(),
                'target': {'host': host, 'port': port},
            }
            segmented = self.security.segment_action(
                action_type='transport_push',
                route=f'{host}:{port}',
                amount=float(len(packet)),
                internal_payload=internal_payload,
            )
            self.security.validate_segment(segmented.external_shell, segmented.internal_encrypted)
            wire_payload = json.dumps({
                'shell': segmented.external_shell,
                'internal': segmented.internal_encrypted,
            }).encode('utf-8')

            if segmented.dispatch_jitter_ms > 0:
                time.sleep(segmented.dispatch_jitter_ms / 1000.0)

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((host, port))
            sock.sendall(wire_payload)
            response = sock.recv(4096)
            sock.close()
            
            decoded = omnitoken_decode(response)
            return decoded is not None
        except Exception:
            return False
    
    def attest(self, action: TransportAction,
               outcome: TransportOutcome) -> Dict:
        """
        Attest transport decision via Omnitoken.
        
        Creates verifiable record of:
        - What was decided
        - Why (rationale)
        - What happened (outcome)
        """
        import socket
        
        tags = {
            'op': 'ATTEST',
            'sha256': hashlib.sha256(
                json.dumps({
                    'chunk_size': action.chunk_size,
                    'batch_size': action.batch_size,
                    'compress_method': action.compress_method,
                    'framing': action.framing,
                    'retry_policy': action.retry_policy,
                    'priority': action.priority,
                    'mi': action.mi_score,
                    'net_value': action.net_value,
                }, sort_keys=True).encode()
            ).hexdigest(),
            'method': action.compress_method,
            'mi': f'{action.mi_score:.4f}',
            'latency': f'{outcome.latency_ms:.2f}',
            'bytes': str(outcome.bytes_sent),
        }
        
        packet = omnitoken_encode(
            f'attest:transport:{action.compress_method}',
            action.net_value,
            tags
        )
        
        try:
            internal_payload = {
                'attestation_packet_hex': packet.hex(),
                'action': {
                    'chunk_size': action.chunk_size,
                    'batch_size': action.batch_size,
                    'compress_method': action.compress_method,
                    'framing': action.framing,
                },
                'outcome': {
                    'latency_ms': outcome.latency_ms,
                    'bytes_sent': outcome.bytes_sent,
                },
            }
            segmented = self.security.segment_action(
                action_type='transport_attest',
                route='127.0.0.1:8446',
                amount=float(outcome.bytes_sent),
                internal_payload=internal_payload,
            )
            self.security.validate_segment(segmented.external_shell, segmented.internal_encrypted)
            wire_payload = json.dumps({
                'shell': segmented.external_shell,
                'internal': segmented.internal_encrypted,
            }).encode('utf-8')

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(('127.0.0.1', 8446))
            sock.sendall(wire_payload)
            response = sock.recv(4096)
            sock.close()
            
            return omnitoken_decode(response) or {'error': 'no_response'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_stats(self) -> Dict:
        """Get transport organism statistics"""
        mi_stats = self.mi.get_stats()
        
        return {
            'mi_points': mi_stats.get('n_points', 0),
            'mi_avg': mi_stats.get('avg_mi', 0),
            'outcome_count': len(self.outcome_history),
            'metrics': self.metrics.get_dashboard(),
        }


def main():
    """Test transport organism"""
    from math_harness_compat import xp, AnyArray
    
    print("=" * 70)
    print(" TRANSPORT ORGANISM")
    print("=" * 70)
    
    org = TransportOrganism()
    
    # Test payloads
    payloads = [
        ("Constant", bytes([65] * 4096)),
        ("Pattern", bytes(range(32)) * 128),
        ("XML-like", b"<tag>value</tag>" * 256),
        ("Text", b"The quick brown fox jumps over the lazy dog. " * 100),
        ("Random", bytes(xp.random.randint(0, 256, 4096, dtype=xp.uint8))),
    ]
    
    print(f"\n{'Payload':<15} {'MI':>5} {'Method':>8} {'Chunk':>6} {'Compress':>9} {'NetVal':>7}  {'Gain':>8} {'Regret':>8}")
    print("-" * 80)
    
    for name, data in payloads:
        action = org.select_action(data)
        outcome = org.execute(data, action)
        ingested = org.ingest(data, action, outcome)

        compress_str = f"{action.compress_method}" if action.compress else "none"
        print(f"{name:<15} {action.mi_score:>5.2f} {action.compress_method:>8} "
              f"{action.chunk_size:>6} {compress_str:>9} {action.net_value:>7.3f} "
              f"gain={ingested['mi_gain']:>+.3f} regret={ingested['regret']:.3f}")
    
    # Stats
    stats = org.get_stats()
    print(f"\nMI points: {stats['mi_points']}")
    print(f"MI avg: {stats['mi_avg']:.3f}")
    print(f"Outcomes: {stats['outcome_count']}")
    
    print(f"\n✓ Transport organism operational")


if __name__ == '__main__':
    main()
