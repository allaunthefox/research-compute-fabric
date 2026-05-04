"""
canonical.py

Concrete canonical adapter module for the Math Universe.

This module defines a domain-agnostic contract for projecting raw signals into
a shared invariant state space, validating that projection, packing it into an
n-space vector, and assigning that vector to attractors and symbolic signatures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import acos, isfinite
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple, List


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a numeric value into a closed interval."""
    return max(low, min(high, value))


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide safely, returning a default value when the denominator is too small."""
    if abs(denominator) < 1e-12:
        return default
    return numerator / denominator


def l2_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute Euclidean distance between two vectors of equal length."""
    if len(a) != len(b):
        raise ValueError(f"Distance requires equal vector lengths, got {len(a)} and {len(b)}.")
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        raise ValueError(f"Cosine similarity requires equal vector lengths, got {len(a)} and {len(b)}.")
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return clamp(safe_div(dot, na * nb, default=0.0), -1.0, 1.0)


class ControlMode(str, Enum):
    """Canonical domain-agnostic control modes."""
    COMMIT = "COMMIT"
    HOLD = "HOLD"
    HALT = "HALT"
    DMT = "DMT"


class NormalizationMode(str, Enum):
    """Supported normalization styles for raw features."""
    MINMAX = "MINMAX"
    CENTERED = "CENTERED"
    PASSTHROUGH = "PASSTHROUGH"


@dataclass(frozen=True)
class FeatureSpec:
    """Contract for a single normalized raw feature."""
    name: str
    mode: NormalizationMode
    low: float = 0.0
    high: float = 1.0
    required: bool = True


@dataclass
class CanonicalState:
    """Shared invariant state consumed by the core controller."""
    phi: float
    delta: float
    delta_dot: float
    gamma: float
    chi: float
    tau: float
    theta: float = 0.0
    kappa: float = 0.0
    ang_momentum: float = 0.0
    radius_dev: float = 0.0
    confidence: float = 1.0
    domain: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalVectorSpec:
    """Defines which coordinates appear in the packed z_n vector."""
    dimensions: Tuple[str, ...] = (
        "phi",
        "delta",
        "delta_dot",
        "gamma",
        "chi",
        "tau",
        "theta",
        "kappa",
        "ang_momentum",
        "radius_dev",
        "confidence",
    )


@dataclass(frozen=True)
class Attractor:
    """A named reference point in canonical n-space."""
    name: str
    center: Tuple[float, ...]
    max_radius: Optional[float] = None


@dataclass
class AssignmentResult:
    """Continuous + discrete assignment result for a canonical state."""
    z_n: Tuple[float, ...]
    nearest_attractor: Optional[str]
    attractor_distance: Optional[float]
    attractor_confidence: float
    signature: Tuple[int, ...]
    quantized_bands: Dict[str, int]
    consistent: bool
    notes: Dict[str, Any] = field(default_factory=dict)


class RawAdapter(Protocol):
    """Protocol for domain-specific adapters."""
    feature_specs: Sequence[FeatureSpec]
    domain_name: str

    def to_canonical(
        self,
        normalized_observation: Mapping[str, float],
        normalized_reference: Optional[Mapping[str, float]] = None,
        history: Optional[Sequence[CanonicalState]] = None,
    ) -> CanonicalState:
        ...


class NormalizationContract:
    """Enforces raw-input normalization before canonical derivation."""

    def __init__(self, feature_specs: Sequence[FeatureSpec]) -> None:
        self.feature_specs: Tuple[FeatureSpec, ...] = tuple(feature_specs)

    def normalize(self, raw: Mapping[str, Any]) -> Dict[str, float]:
        """Normalize a raw observation according to the configured feature specs."""
        output: Dict[str, float] = {}

        for spec in self.feature_specs:
            if spec.required and spec.name not in raw:
                raise KeyError(f"Missing required raw feature: {spec.name}")
            if spec.name not in raw:
                continue

            raw_value = float(raw[spec.name])
            if not isfinite(raw_value):
                raise ValueError(f"Non-finite raw feature '{spec.name}': {raw_value}")

            if spec.mode == NormalizationMode.MINMAX:
                scaled = safe_div(raw_value - spec.low, spec.high - spec.low, default=0.0)
                output[spec.name] = clamp(scaled, 0.0, 1.0)
            elif spec.mode == NormalizationMode.CENTERED:
                center = (spec.high + spec.low) / 2.0
                half_span = max((spec.high - spec.low) / 2.0, 1e-12)
                scaled = safe_div(raw_value - center, half_span, default=0.0)
                output[spec.name] = clamp(scaled, -1.0, 1.0)
            elif spec.mode == NormalizationMode.PASSTHROUGH:
                output[spec.name] = raw_value
            else:
                raise ValueError(f"Unsupported normalization mode: {spec.mode}")

        return output


class InvariantChecker:
    """Validates canonical states and assignment consistency."""

    def __init__(self, phi_bounds: Tuple[float, float] = (-1.0, 1.0)) -> None:
        self.phi_bounds = phi_bounds

    def validate_state(self, state: CanonicalState) -> List[str]:
        """Validate a canonical state and return a list of issues."""
        issues: List[str] = []

        values = {
            "phi": state.phi,
            "delta": state.delta,
            "delta_dot": state.delta_dot,
            "gamma": state.gamma,
            "chi": state.chi,
            "tau": state.tau,
            "theta": state.theta,
            "kappa": state.kappa,
            "ang_momentum": state.ang_momentum,
            "radius_dev": state.radius_dev,
            "confidence": state.confidence,
        }

        for name, value in values.items():
            if not isfinite(value):
                issues.append(f"{name} is non-finite: {value}")

        if not (self.phi_bounds[0] <= state.phi <= self.phi_bounds[1]):
            issues.append(f"phi out of bounds: {state.phi}")
        if state.delta < 0.0:
            issues.append(f"delta must be non-negative, got {state.delta}")
        if not (0.0 <= state.chi <= 1.0):
            issues.append(f"chi must be in [0, 1], got {state.chi}")
        if not (0.0 <= state.confidence <= 1.0):
            issues.append(f"confidence must be in [0, 1], got {state.confidence}")

        expected_theta = acos(clamp(state.phi, -1.0, 1.0))
        if abs(state.theta - expected_theta) > 0.25:
            issues.append(
                f"theta appears inconsistent with phi: theta={state.theta:.4f}, expected≈{expected_theta:.4f}"
            )

        return issues

    def assert_valid_state(self, state: CanonicalState) -> None:
        """Raise an exception if a state fails invariant checks."""
        issues = self.validate_state(state)
        if issues:
            raise ValueError("Invalid CanonicalState:\n- " + "\n- ".join(issues))

    def validate_assignment(self, result: AssignmentResult) -> List[str]:
        """Validate an assignment result and return any issues found."""
        issues: List[str] = []

        if len(result.z_n) == 0:
            issues.append("z_n is empty")
        if len(result.signature) != len(result.quantized_bands):
            issues.append("signature length does not match quantized band count")
        if not (0.0 <= result.attractor_confidence <= 1.0):
            issues.append(f"attractor_confidence out of range: {result.attractor_confidence}")

        return issues


class ZNPacker:
    """Packs a canonical state into a stable n-dimensional vector."""

    def __init__(self, spec: Optional[CanonicalVectorSpec] = None) -> None:
        self.spec = spec or CanonicalVectorSpec()

    def pack(self, state: CanonicalState) -> Tuple[float, ...]:
        """Pack a state into an ordered tuple according to the configured vector spec."""
        vector: List[float] = []
        for dim in self.spec.dimensions:
            if not hasattr(state, dim):
                raise AttributeError(f"CanonicalState has no attribute '{dim}' required by packer.")
            vector.append(float(getattr(state, dim)))
        return tuple(vector)


class AssignmentEngine:
    """Assigns a canonical vector to attractors and discrete structural signatures."""

    def __init__(
        self,
        vector_spec: Optional[CanonicalVectorSpec] = None,
        attractors: Optional[Sequence[Attractor]] = None,
        quantization_bands: Optional[Mapping[str, Tuple[float, float, float]]] = None,
    ) -> None:
        self.vector_spec = vector_spec or CanonicalVectorSpec()
        self.attractors: Tuple[Attractor, ...] = tuple(attractors or ())
        self.quantization_bands: Dict[str, Tuple[float, float, float]] = dict(quantization_bands or {})

    def _nearest_attractor(self, z_n: Sequence[float]) -> Tuple[Optional[str], Optional[float], float, Dict[str, Any]]:
        """Find the nearest attractor and derive a confidence score."""
        if not self.attractors:
            return None, None, 0.0, {"reason": "no_attractors_configured"}

        distances: List[Tuple[Attractor, float]] = []
        for attractor in self.attractors:
            if len(attractor.center) != len(z_n):
                raise ValueError(
                    f"Attractor '{attractor.name}' has dimension {len(attractor.center)} but z_n has dimension {len(z_n)}."
                )
            distances.append((attractor, l2_distance(z_n, attractor.center)))

        best_attractor, best_distance = min(distances, key=lambda item: item[1])

        if best_attractor.max_radius is not None and best_attractor.max_radius > 0.0:
            confidence = clamp(1.0 - (best_distance / best_attractor.max_radius), 0.0, 1.0)
            notes = {"radius_based": True, "max_radius": best_attractor.max_radius}
        else:
            confidence = safe_div(1.0, 1.0 + best_distance, default=0.0)
            notes = {"radius_based": False}

        return best_attractor.name, best_distance, confidence, notes

    def _quantize_dimension(self, dim_name: str, value: float) -> int:
        """Quantize a single dimension into one of four bands."""
        t0, t1, t2 = self.quantization_bands.get(dim_name, (0.25, 0.50, 0.75))
        if value < t0:
            return 0
        if value < t1:
            return 1
        if value < t2:
            return 2
        return 3

    def assign(self, z_n: Sequence[float]) -> AssignmentResult:
        """Assign a packed vector to both continuous and discrete representations."""
        nearest_name, nearest_distance, attractor_conf, attractor_notes = self._nearest_attractor(z_n)

        quantized_bands: Dict[str, int] = {}
        signature: List[int] = []
        for dim_name, value in zip(self.vector_spec.dimensions, z_n):
            band = self._quantize_dimension(dim_name, float(value))
            quantized_bands[dim_name] = band
            signature.append(band)

        low_band_ratio = safe_div(sum(1 for s in signature if s == 0), len(signature), default=0.0)
        consistent = not (attractor_conf < 0.15 and low_band_ratio > 0.75)

        notes = dict(attractor_notes)
        notes["low_band_ratio"] = low_band_ratio
        notes["consistency_rule"] = "flag if attractor_conf < 0.15 and >75% of bands are zero"

        return AssignmentResult(
            z_n=tuple(float(v) for v in z_n),
            nearest_attractor=nearest_name,
            attractor_distance=nearest_distance,
            attractor_confidence=attractor_conf,
            signature=tuple(signature),
            quantized_bands=quantized_bands,
            consistent=consistent,
            notes=notes,
        )


class CanonicalPipeline:
    """End-to-end helper for normalization, invariant checking, packing, and assignment."""

    def __init__(
        self,
        adapter: RawAdapter,
        checker: Optional[InvariantChecker] = None,
        packer: Optional[ZNPacker] = None,
        assignment_engine: Optional[AssignmentEngine] = None,
    ) -> None:
        self.adapter = adapter
        self.contract = NormalizationContract(adapter.feature_specs)
        self.checker = checker or InvariantChecker()
        self.packer = packer or ZNPacker()
        self.assignment_engine = assignment_engine or AssignmentEngine(vector_spec=self.packer.spec)

    def process(
        self,
        raw_observation: Mapping[str, Any],
        raw_reference: Optional[Mapping[str, Any]] = None,
        history: Optional[Sequence[CanonicalState]] = None,
        strict: bool = True,
    ) -> Tuple[CanonicalState, AssignmentResult]:
        """Run the full canonical processing sequence."""
        normalized_obs = self.contract.normalize(raw_observation)
        normalized_ref = self.contract.normalize(raw_reference) if raw_reference is not None else None

        state = self.adapter.to_canonical(
            normalized_observation=normalized_obs,
            normalized_reference=normalized_ref,
            history=history,
        )

        state_issues = self.checker.validate_state(state)
        if strict and state_issues:
            raise ValueError("Canonical state failed invariant checks:\n- " + "\n- ".join(state_issues))

        z_n = self.packer.pack(state)
        assignment = self.assignment_engine.assign(z_n)

        assignment_issues = self.checker.validate_assignment(assignment)
        if strict and assignment_issues:
            raise ValueError("Assignment failed invariant checks:\n- " + "\n- ".join(assignment_issues))

        if state_issues or assignment_issues:
            assignment.notes["state_issues"] = state_issues
            assignment.notes["assignment_issues"] = assignment_issues

        return state, assignment


class GenericSimilarityAdapter:
    """A simple reference adapter showing how a domain can plug into the pipeline."""

    domain_name = "generic"

    feature_specs: Sequence[FeatureSpec] = (
        FeatureSpec("f1", NormalizationMode.MINMAX, 0.0, 1.0),
        FeatureSpec("f2", NormalizationMode.MINMAX, 0.0, 1.0),
        FeatureSpec("f3", NormalizationMode.MINMAX, 0.0, 1.0),
        FeatureSpec("f4", NormalizationMode.MINMAX, 0.0, 1.0),
    )

    def to_canonical(
        self,
        normalized_observation: Mapping[str, float],
        normalized_reference: Optional[Mapping[str, float]] = None,
        history: Optional[Sequence[CanonicalState]] = None,
    ) -> CanonicalState:
        """Derive a canonical state using generic formulas."""
        keys = [spec.name for spec in self.feature_specs]
        obs_vec = [float(normalized_observation[k]) for k in keys]

        if normalized_reference is None:
            ref_vec = [0.5 for _ in keys]
        else:
            ref_vec = [float(normalized_reference[k]) for k in keys]

        phi = cosine_similarity(obs_vec, ref_vec)
        delta = l2_distance(obs_vec, ref_vec)

        prev_delta = history[-1].delta if history else delta
        prev_delta_dot = history[-1].delta_dot if history else 0.0

        delta_dot = delta - prev_delta
        gamma = delta_dot - prev_delta_dot

        mean_abs = safe_div(sum(abs(v) for v in obs_vec), len(obs_vec), default=0.0)
        peak_abs = max(abs(v) for v in obs_vec) if obs_vec else 0.0
        chi = clamp(safe_div(peak_abs, peak_abs + mean_abs + 1e-12, default=0.0), 0.0, 1.0)

        tau = abs(gamma) + (1.0 - ((phi + 1.0) / 2.0)) + delta

        theta = acos(clamp(phi, -1.0, 1.0))
        kappa = abs(gamma)
        ang_momentum = abs(delta_dot) * kappa
        radius_dev = delta

        return CanonicalState(
            phi=phi,
            delta=delta,
            delta_dot=delta_dot,
            gamma=gamma,
            chi=chi,
            tau=tau,
            theta=theta,
            kappa=kappa,
            ang_momentum=ang_momentum,
            radius_dev=radius_dev,
            confidence=clamp((phi + 1.0) / 2.0, 0.0, 1.0),
            domain=self.domain_name,
            metadata={"obs_vec": obs_vec, "ref_vec": ref_vec},
        )


if __name__ == "__main__":
    adapter = GenericSimilarityAdapter()
    packer = ZNPacker(
        CanonicalVectorSpec(
            dimensions=(
                "phi",
                "delta",
                "delta_dot",
                "gamma",
                "chi",
                "tau",
                "theta",
                "kappa",
                "ang_momentum",
            )
        )
    )

    attractors = [
        Attractor(
            name="stable_core",
            center=(1.0, 0.0, 0.0, 0.0, 0.6, 0.1, 0.0, 0.0, 0.0),
            max_radius=2.0,
        ),
        Attractor(
            name="stress_front",
            center=(0.0, 0.8, 0.4, 0.5, 0.4, 1.2, 1.2, 0.5, 0.6),
            max_radius=2.5,
        ),
    ]

    engine = AssignmentEngine(
        vector_spec=packer.spec,
        attractors=attractors,
        quantization_bands={
            "phi": (-0.25, 0.25, 0.75),
            "delta": (0.10, 0.30, 0.60),
            "delta_dot": (-0.10, 0.10, 0.30),
            "gamma": (-0.10, 0.10, 0.30),
            "chi": (0.25, 0.50, 0.75),
            "tau": (0.20, 0.50, 0.90),
            "theta": (0.30, 0.80, 1.30),
            "kappa": (0.05, 0.20, 0.50),
            "ang_momentum": (0.05, 0.20, 0.50),
        },
    )

    pipeline = CanonicalPipeline(adapter=adapter, packer=packer, assignment_engine=engine)

    raw_obs = {"f1": 0.90, "f2": 0.20, "f3": 0.70, "f4": 0.10}
    raw_ref = {"f1": 0.80, "f2": 0.20, "f3": 0.75, "f4": 0.15}

    state, assignment = pipeline.process(raw_observation=raw_obs, raw_reference=raw_ref, strict=True)

    print("CanonicalState:")
    print(state)
    print()
    print("AssignmentResult:")
    print(assignment)
