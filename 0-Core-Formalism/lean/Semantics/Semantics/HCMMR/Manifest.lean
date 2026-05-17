/-
HCMMR Manifest.lean — Single import entry point for the HCMMR Operadic Meta-Calculus.

Import this file to access the full typed-gate diagnostic system:
- Core typeclass definitions (Gate, GateChain, EigenmassOperator, Residual, DiagnosticReceipt)
- Bridge adapters to existing Semantics modules (FAMM, SigmaGate, ReceiptCore, etc.)
- Laws 14–21 (Motion, Field, Entropy, Observer, Constants, VoidScar, Shock, ThermalBoundary)
- Kernel utilities (Recamán, FAMM Scar Memory, Prime Gear Cache, SNR Anomaly Detector,
                   HyperEigenSpectrum λ_YAH, BoundaryEigenFire B_∂ / GeodesicPromotion)

Version: v0.1 → v0.2 bridge (per v0_2_Roadmap.md)
-/
import Semantics.HCMMR.Core
import Semantics.HCMMR.Bridge
import Semantics.HCMMR.Laws.Law14_Motion
import Semantics.HCMMR.Laws.Law15_Field
import Semantics.HCMMR.Laws.Law15E_SignalDetection
import Semantics.HCMMR.Laws.Law16_Entropy
import Semantics.HCMMR.Laws.Law17_Observer
import Semantics.HCMMR.Laws.Law18_Constants
import Semantics.HCMMR.Laws.Law19_VoidScar
import Semantics.HCMMR.Laws.Law20_Shock
import Semantics.HCMMR.Laws.Law21_ThermalBoundary
import Semantics.HCMMR.Kernels.RecamanFieldStep
import Semantics.HCMMR.Kernels.FAMMScarMemory
import Semantics.HCMMR.Kernels.PrimeGearCache
import Semantics.HCMMR.Kernels.SNRAnomalyDetector
import Semantics.HCMMR.Kernels.HyperEigenSpectrum
import Semantics.HCMMR.Kernels.BoundaryEigenFire
import Semantics.HCMMR.Kernels.EntropyCollapseDetector
