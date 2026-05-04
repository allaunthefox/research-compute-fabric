import Semantics.SurfaceCore
import Semantics.WebInteractionSurface
import Semantics.JsonLSurfaceConnector
import Semantics.MetadataSurfaceComputation
import Semantics.WebRTCWaveformSync
import Semantics.PassiveComputation
import Semantics.PhiShellEncoding
import Semantics.GoldenAngleEncoding
import Semantics.FibonacciEncoding

/-!
# Surface

Canonical entry point for surface-facing semantics.

This module consolidates surface-facing semantics without moving legacy files.
New code should import `Semantics.Surface` and select a `SurfaceRole` instead of
importing transport-specific surfaces directly.
-/

namespace Semantics.Surface

/-- The finite set of surface roles admitted by the canonical surface area. -/
inductive SurfaceRole where
  | geometric
  | webInteraction
  | jsonlConnector
  | metadataComputation
  | webrtcWaveform
  | passiveComputation
  | phiShellEncoding
  | goldenAngleEncoding
  | fibonacciEncoding
  deriving Repr, DecidableEq, Inhabited

/-- The bind class associated with each surface role. -/
def bindClass : SurfaceRole → JsonLSurfaceConnector.BindClass
  | .geometric => .geometric
  | .webInteraction => .control
  | .jsonlConnector => .informational
  | .metadataComputation => .informational
  | .webrtcWaveform => .control
  | .passiveComputation => .control
  | .phiShellEncoding => .geometric
  | .goldenAngleEncoding => .geometric
  | .fibonacciEncoding => .informational

/-- Whether a surface role is an externally exposed transport boundary. -/
def isTransportBoundary : SurfaceRole → Bool
  | .geometric => false
  | .webInteraction => true
  | .jsonlConnector => true
  | .metadataComputation => true
  | .webrtcWaveform => true
  | .passiveComputation => true
  | .phiShellEncoding => false
  | .goldenAngleEncoding => false
  | .fibonacciEncoding => false

/-- Human-readable invariant tag for surface receipts and map rows. -/
def invariantTag : SurfaceRole → String
  | .geometric => "surface:geometric"
  | .webInteraction => "surface:web_interaction"
  | .jsonlConnector => "surface:jsonl_connector"
  | .metadataComputation => "surface:metadata_computation"
  | .webrtcWaveform => "surface:webrtc_waveform"
  | .passiveComputation => "surface:passive_computation"
  | .phiShellEncoding => "surface:phi_shell_encoding"
  | .goldenAngleEncoding => "surface:golden_angle_encoding"
  | .fibonacciEncoding => "surface:fibonacci_encoding"

/-- Consolidated record for routing through the canonical surface area. -/
structure SurfaceReceipt where
  role : SurfaceRole
  invariant : String
  transportBoundary : Bool
  bindClass : JsonLSurfaceConnector.BindClass
  deriving Repr, DecidableEq

/-- Build a receipt from a role. -/
def receiptFor (role : SurfaceRole) : SurfaceReceipt :=
  { role := role
    invariant := invariantTag role
    transportBoundary := isTransportBoundary role
    bindClass := bindClass role }

/-- Re-export the geometric surface type through the canonical surface area. -/
abbrev GeometricSurface := SurfaceCore.Surface

/-- Re-export the web task type through the canonical surface area. -/
abbrev WebTask := WebInteractionSurface.WebTask

/-- Re-export the JSONL event type through the canonical surface area. -/
abbrev JsonLEvent := JsonLSurfaceConnector.JsonLEvent

/-- Re-export the metadata surface type through the canonical surface area. -/
abbrev MetadataSurface := MetadataSurfaceComputation.MetadataSurface

/-- Re-export the WebRTC waveform event type through the canonical surface area. -/
abbrev SurfaceWaveEvent := WebRTCWaveformSync.SurfaceWaveEvent

/-- Re-export the passive transit computation type through the canonical surface area. -/
abbrev TransitComputation := PassiveComputation.TransitComputation

/-- Re-export the φ-shell path type through the canonical surface area. -/
abbrev PhiShellPath := PhiShellEncoding.PhiShellPath

/-- Re-export the golden-angle WaveProbe sample type through the canonical surface area. -/
abbrev WaveProbeSample := GoldenAngleEncoding.WaveProbeSample

/-- Re-export the Fibonacci representation type through the canonical surface area. -/
abbrev ZeckendorfRep := FibonacciEncoding.ZeckendorfRep

theorem receiptForBindClass (role : SurfaceRole) :
    (receiptFor role).bindClass = bindClass role := by
  cases role <;> rfl

theorem transportBoundaryIff (role : SurfaceRole) :
    (receiptFor role).transportBoundary = isTransportBoundary role := by
  cases role <;> rfl

theorem jsonlConnectorIsInformational :
    (receiptFor .jsonlConnector).bindClass = JsonLSurfaceConnector.BindClass.informational := by
  rfl

theorem geometricSurfaceIsNotTransport :
    (receiptFor .geometric).transportBoundary = false := by
  rfl

theorem metadataComputationIsInformational :
    (receiptFor .metadataComputation).bindClass =
      JsonLSurfaceConnector.BindClass.informational := by
  rfl

theorem webrtcWaveformIsTransport :
    (receiptFor .webrtcWaveform).transportBoundary = true := by
  rfl

theorem passiveComputationIsTransport :
    (receiptFor .passiveComputation).transportBoundary = true := by
  rfl

theorem phiShellEncodingIsGeometric :
    (receiptFor .phiShellEncoding).bindClass =
      JsonLSurfaceConnector.BindClass.geometric := by
  rfl

theorem goldenAngleEncodingIsGeometric :
    (receiptFor .goldenAngleEncoding).bindClass =
      JsonLSurfaceConnector.BindClass.geometric := by
  rfl

theorem fibonacciEncodingIsInformational :
    (receiptFor .fibonacciEncoding).bindClass =
      JsonLSurfaceConnector.BindClass.informational := by
  rfl

#eval (receiptFor .geometric).invariant -- expected: "surface:geometric"
#eval (receiptFor .jsonlConnector).transportBoundary -- expected: true
#eval (receiptFor .metadataComputation).invariant -- expected: "surface:metadata_computation"
#eval (receiptFor .passiveComputation).invariant -- expected: "surface:passive_computation"
#eval (receiptFor .goldenAngleEncoding).invariant -- expected: "surface:golden_angle_encoding"

end Semantics.Surface
