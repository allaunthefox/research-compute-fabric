import Semantics.Autobalance
import Semantics.FixedPoint
import Semantics.Bind

namespace Semantics.OmniNetwork

open Semantics
open Semantics.Autobalance

/--
Transport: Defines the allowed communication channels.
-/
inductive Transport
  | tailscale -- Primary (Private 100.127.x.x)
  | i2p       -- Secondary (Covert/Sovereign)
  | local_bus -- Intra-node
deriving Repr, BEq, DecidableEq

/--
OmniNode: A research node within the distributed substrate.
Extends NodeState with transport and security metadata.
-/
structure OmniNode where
  base      : NodeState
  transport : Transport
  isTrusted : Bool
  key_hash  : String

/--
The Omni Invariant: A connection is lawful only if:
1. The transport is Tailscale or I2P.
2. The node is explicitly trusted.
3. The key_hash is present.
-/
def isLawfulPeer (n : OmniNode) : Bool :=
  n.isTrusted && (n.transport == .tailscale || n.transport == .i2p) && n.key_hash != ""

/--
Network Tension: Measures the 'force' required to bring the network to equilibrium.
Tension is the sum of deltas between all peer record counts.
-/
def networkTension (peers : List OmniNode) : Q16_16 :=
  -- If any node is out of sync (per Autobalance logic), tension rises.
  if isGrounded (peers.map (·.base)) then Q16_16.zero
  else Q16_16.one -- Constant tension for now; can be mapped to count delta

/--
The Omni Bind: Connects the network state to the research manifold.
-/
def omniBind (source : OmniNode) (target : OmniNode) (g : Metric) : Bind OmniNode OmniNode :=
  controlBind source target g 
    (fun _ _ _ => 0x00010000) -- Base cost of 1.0
    (fun _ => if isLawfulPeer target then "peer_authenticated" else "unlawful_peer_rejected")
    (fun _ => "omni_substrate_verified")

/--
Autonomy Rule: The network is authorized to execute Autobalance 
only when Tension > 0.
-/
def canAutobalance (peers : List OmniNode) : Prop :=
  (networkTension peers).toInt > 0

end Semantics.OmniNetwork
