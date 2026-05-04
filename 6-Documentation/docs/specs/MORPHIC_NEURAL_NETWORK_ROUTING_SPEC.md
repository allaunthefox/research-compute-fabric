# Morphic Neural Network Routing Layer

**Version:** 0.1  
**Status:** Draft routing layer  
**Scope:** Low-level adaptive routing between LUT admission and GCL codons

---

## Architecture Position

The Morphic Neural Network (MNN) sits between the ultra-compressed LUT admission and the GCL codon/action layer:

```
surface shell (UDP/onion/Ethernet/serial/ipv923u)
  ↓
scale-invariant 1D scalar
  ↓
LUT admission (ultra-compressed codon lookup)
  ↓
MNN routing layer (adaptive path formation)
  ↓
GCL codon/action (lawful state transition)
```

The MNN is **not** a deep learning classifier. [BEAUTIFUL_PROVISIONAL - It is a proposed low-level morphic router that reshapes the path from admitted intent to GCL action based on:]

- Packet goal (what the scalar encodes)
- Local node state (memory, load, recovery mode)
- Carrier/shell conditions (latency, loss, trust)
- Recovery pressure (how badly the node needs stability)
- Cost (energy, time, bandwidth budget)

---

## Core Design Principles

### 1. Morphic, Not Static

The MNN does not have fixed routing tables. It has a morphic topology that reshapes itself based on the current manifold state. A packet that routes locally under normal conditions may route to the atlas under recovery pressure.

### 2. Goal-Aware

The scalar encodes not just an operation, but a goal. The MNN interprets this goal and selects a path that satisfies it:

- [BEAUTIFUL_PROVISIONAL - **health goal**: fastest local response - requires benchmark evidence]
- [BEAUTIFUL_PROVISIONAL - **attest goal**: cryptographic verification path - requires implementation evidence]
- [BEAUTIFUL_PROVISIONAL - **compress goal**: bandwidth-optimized path - requires benchmark evidence]
- [BEAUTIFUL_PROVISIONAL - **recover goal**: stability-first path - requires implementation evidence]
- [BEAUTIFUL_PROVISIONAL - **route goal**: atlas-forward path - requires implementation evidence]

### 3. State-Constrained

The MNN sees the node's actual resource state:

- Memory budget (MB or bytes)
- CPU load (0.0 to 1.0)
- Recovery mode flag
- Trust score (0.0 to 1.0)
- Carrier quality (latency, loss rate)

A low-memory node may reject a compress operation even if the LUT admits it. A node in recovery mode may route all attestation to the atlas even if local verification is possible.

### 4. Carrier-Agnostic

The MNN does not care whether the packet arrived via UDP, Ethernet, onion, serial, or future IPv923U. It only sees:

- Admitted scalar (domain, scalar value)
- Carrier quality metrics (derived from shell binding)
- Trust score (derived from shell binding)

### 5. Cost-Aware

Every routing decision has a cost:

- Energy cost (CPU cycles)
- Time cost (latency)
- Bandwidth cost (bytes transmitted)
- Recovery cost (risk of state corruption)

The MNN minimizes total cost while satisfying the goal and constraints.

---

## Data Structures

### Scalar Input

```python
{
    "domain": u8,      # 0-255: operation domain
    "scalar": u8,      # 0-255: specific operation within domain
}
```

### Node State

```python
{
    "memory_budget_mb": float,
    "memory_used_mb": float,
    "cpu_load": float,        # 0.0 to 1.0
    "recovery_mode": bool,
    "trust_score": float,     # 0.0 to 1.0
    "uptime_seconds": float,
}
```

### Carrier Metrics

```python
{
    "shell": str,             # "udp", "ethernet", "onion", "serial", "ipv923u", etc.
    "latency_ms": float,
    "loss_rate": float,       # 0.0 to 1.0
    "bandwidth_kbps": float,
    "encrypted": bool,
}
```

### Routing Decision

```python
{
    "action": str,            # "local", "atlas", "reject", "defer"
    "gcl_codon": u8,          # final GCL operation code
    "cost": {
        "energy": float,
        "time": float,
        "bandwidth": float,
    },
    "reason": str,
}
```

---

## Morphic Routing Algorithm

### Step 1: Goal Extraction

The scalar is mapped to a goal:

```python
def scalar_to_goal(domain: u8, scalar: u8) -> str:
    # Domain 0: health/status
    if domain == 0:
        return "health"
    # Domain 1: attestation
    if domain == 1:
        return "attest"
    # Domain 2: compression
    if domain == 2:
        return "compress"
    # Domain 3: routing
    if domain == 3:
        return "route"
    # Domain 4: recovery
    if domain == 4:
        return "recover"
    return "unknown"
```

### Step 2: Constraint Check

Check if the node can satisfy the goal given current state:

```python
def can_satisfy(goal: str, state: dict, carrier: dict) -> bool:
    # Recovery mode: only health and recover goals
    if state["recovery_mode"]:
        return goal in ("health", "recover")
    
    # Memory constraint: compress needs buffer
    if goal == "compress":
        required = 1024  # 1KB buffer minimum
        return (state["memory_budget_mb"] - state["memory_used_mb"]) * 1024 > required
    
    # Trust constraint: attest needs high trust
    if goal == "attest":
        return state["trust_score"] > 0.5
    
    # Carrier constraint: route needs reliable carrier
    if goal == "route":
        return carrier["loss_rate"] < 0.1
    
    return True
```

### Step 3: Path Selection

Select the best path based on cost minimization:

```python
def select_path(goal: str, state: dict, carrier: dict) -> dict:
    if not can_satisfy(goal, state, carrier):
        return {
            "action": "reject",
            "gcl_codon": 0xFF,  # reject codon
            "cost": {"energy": 0, "time": 0, "bandwidth": 0},
            "reason": "constraint-violation",
        }
    
    # Recovery mode: always defer to atlas
    if state["recovery_mode"] and goal != "health":
        return {
            "action": "atlas",
            "gcl_codon": goal_to_codon(goal),
            "cost": {"energy": [BEAUTIFUL_PROVISIONAL - 10 - requires measurement evidence], "time": carrier["latency_ms"], "bandwidth": [BEAUTIFUL_PROVISIONAL - 512 - requires measurement evidence]},
            "reason": "recovery-defer",
        }
    
    # High trust + good carrier: local execution
    if state["trust_score"] > 0.8 and carrier["loss_rate"] < 0.05:
        return {
            "action": "local",
            "gcl_codon": goal_to_codon(goal),
            "cost": {"energy": [BEAUTIFUL_PROVISIONAL - 1 - requires measurement evidence], "time": [BEAUTIFUL_PROVISIONAL - 1 - requires measurement evidence], "bandwidth": 0},
            "reason": "local-trusted",
        }
    
    # Moderate trust: local with verification
    if state["trust_score"] > 0.5:
        return {
            "action": "local",
            "gcl_codon": goal_to_codon(goal),
            "cost": {"energy": [BEAUTIFUL_PROVISIONAL - 2 - requires measurement evidence], "time": [BEAUTIFUL_PROVISIONAL - 2 - requires measurement evidence], "bandwidth": 0},
            "reason": "local-verified",
        }
    
    # Low trust: defer to atlas
    return {
        "action": "atlas",
        "gcl_codon": goal_to_codon(goal),
        "cost": {"energy": [BEAUTIFUL_PROVISIONAL - 5 - requires measurement evidence], "time": carrier["latency_ms"], "bandwidth": [BEAUTIFUL_PROVISIONAL - 256 - requires measurement evidence]},
        "reason": "low-trust-defer",
    }
```

### Step 4: Morphic Adaptation

The MNN adapts its routing based on historical outcomes:

```python
class MorphicRouter:
    def __init__(self):
        self.history = {}  # (goal, state_signature) -> success_rate
        self.state_signature_cache = {}
    
    def state_signature(self, state: dict, carrier: dict) -> str:
        # Coarse-grained state signature for morphic learning
        key = (
            int(state["recovery_mode"]),
            int(state["trust_score"] * 10),  # 0-10
            int(carrier["loss_rate"] * 10),   # 0-10
        )
        return str(key)
    
    def update_history(self, goal: str, state: dict, carrier: dict, success: bool):
        sig = self.state_signature(state, carrier)
        key = (goal, sig)
        if key not in self.history:
            self.history[key] = {"success": 0, "total": 0}
        self.history[key]["total"] += 1
        if success:
            self.history[key]["success"] += 1
    
    def get_success_rate(self, goal: str, state: dict, carrier: dict) -> float:
        sig = self.state_signature(state, carrier)
        key = (goal, sig)
        if key not in self.history:
            return 0.5  # neutral prior
        h = self.history[key]
        return h["success"] / h["total"]
    
    def route_with_adaptation(self, domain: u8, scalar: u8, state: dict, carrier: dict) -> dict:
        goal = scalar_to_goal(domain, scalar)
        base_decision = select_path(goal, state, carrier)
        
        # If historical success rate is low, be more conservative
        success_rate = self.get_success_rate(goal, state, carrier)
        if success_rate < 0.3 and base_decision["action"] == "local":
            # Fallback to atlas for low-success local paths
            return {
                "action": "atlas",
                "gcl_codon": goal_to_codon(goal),
                "cost": {"energy": [BEAUTIFUL_PROVISIONAL - 5 - requires measurement evidence], "time": carrier["latency_ms"], "bandwidth": [BEAUTIFUL_PROVISIONAL - 256 - requires measurement evidence]},
                "reason": "low-success-defer",
            }
        
        return base_decision
```

---

## GCL Codon Mapping

The MNN outputs a GCL codon that the GCL layer executes:

```python
def goal_to_codon(goal: str) -> u8:
    mapping = {
        "health": 0x00,
        "status": 0x01,
        "metrics": 0x02,
        "attest": 0x03,
        "compress": 0x04,
        "rgflow": 0x05,
        "route": 0x06,
        "recover": 0x0D,
    }
    return mapping.get(goal, 0xFF)  # 0xFF = reject/unknown
```

---

## Integration with IBM II Controller

The IBM II Ethernet controller already admits packets via LUT. The MNN layer is inserted after LUT admission:

```python
def ibmii_process_packet(frame: bytes, router: MorphicRouter, state: dict) -> dict:
    # 1. Validate Ethernet frame
    if not validate_ethernet(frame):
        return {"error": "invalid-ethernet"}
    
    # 2. Extract LUT payload (domain, scalar)
    payload = extract_lut_payload(frame)
    domain, scalar = payload["domain"], payload["scalar"]
    
    # 3. LUT admission check
    if not lut_admit(domain, scalar):
        return {"error": "lut-reject"}
    
    # 4. Carrier metrics
    carrier = {
        "shell": "ethernet",
        "latency_ms": 1.0,  # local Ethernet
        "loss_rate": 0.0,
        "bandwidth_kbps": 100000,
        "encrypted": False,
    }
    
    # 5. MNN routing
    decision = router.route_with_adaptation(domain, scalar, state, carrier)
    
    # 6. Emit GCL codon
    if decision["action"] != "reject":
        emit_gcl_codon(decision["gcl_codon"])
    
    return decision
```

---

## Memory Constraints

For 8 KB RAM targets, the MNN must be ultra-minimal:

- **No floating point**: Use fixed-point (Q8.8 or Q16.16)
- **No dynamic allocation**: Pre-allocate routing tables
- **Tiny history**: Keep only last 16 state signatures
- **Coarse signatures**: 3-bit quantization instead of 10-bit
- **Table lookup**: Replace complex scoring with precomputed tables

### 8 KB MNN Layout

[BEAUTIFUL_PROVISIONAL - Memory layout requires synthesis verification evidence]

```
ROM/Flash:
  goal_to_codon table (256 bytes)
  constraint_check table (512 bytes)
  path_selection table (1024 bytes)

RAM:
  router state (64 bytes)
  history cache (128 bytes)
  scratch buffer (256 bytes)
  free margin (512 bytes)
```

---

## Future Extensions

[BEAUTIFUL_PROVISIONAL - All future extensions are conceptual without implementation evidence]

### 1. Multi-Goal Packets

[BEAUTIFUL_PROVISIONAL - A scalar may encode multiple goals with priorities. The MNN routes each goal independently and merges the results - requires implementation evidence]

### 2. Manifold-Aware Routing

[BEAUTIFUL_PROVISIONAL - The MNN could query the geometric topology to understand the current manifold curvature and adjust routing accordingly (e.g., route around high-curvature regions) - requires manifold topology integration evidence]

### 3. Learned Morphic Topology

[BEAUTIFUL_PROVISIONAL - Instead of hand-coded rules, the MNN could learn a morphic topology from experience, using a tiny reinforcement learning algorithm that fits within the memory budget - requires ML implementation evidence]

### 4. Hierarchical MNN

[BEAUTIFUL_PROVISIONAL - For larger nodes (32 KB+ RAM), a hierarchical MNN could have:]
- [BEAUTIFUL_PROVISIONAL - Local MNN for fast local decisions - requires implementation evidence]
- [BEAUTIFUL_PROVISIONAL - Regional MNN for cluster-level routing - requires implementation evidence]
- [BEAUTIFUL_PROVISIONAL - Atlas MNN for global coordination - requires implementation evidence]

---

## Status

- **Spec**: v0.1 draft [BEAUTIFUL_PROVISIONAL - design specification without implementation evidence]
- **Implementation**: Pending
- **Integration**: Pending with IBM II controller
- **Testing**: Pending
- **Evidence Status**: All cost values, performance claims, and memory layouts require benchmark verification and synthesis evidence

---

**Cross-references:**
- OMNITOKEN_GCL_REDESIGN.md (layer OT5: GCL dispatch)
- EMBEDDED_NODE_SURFACE_SPEC.md (node surface architecture)
- TINY_IP_CONTIKI_SURFACE_SPEC.md (carrier shell layer)
