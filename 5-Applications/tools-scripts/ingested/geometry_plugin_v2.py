# geometry_plugin_v2.py
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def safe_mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def norm(values: Sequence[float]) -> float:
    return math.sqrt(sum(v * v for v in values)) if values else 0.0


def gradient(values: Sequence[float]) -> List[float]:
    if len(values) < 2:
        return [0.0]
    return [values[i + 1] - values[i] for i in range(len(values) - 1)]


def to_u8_clamped(x: float) -> int:
    return int(clamp(round(x), 0, 255))


@dataclass
class GeometricTelemetry:
    z: List[float]
    angular_drift: float
    curvature: float
    radius_dev: float
    coherence: float
    angular_momentum: float
    speed: float
    turn_angle: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "angular_drift": self.angular_drift,
            "curvature": self.curvature,
            "radius_dev": self.radius_dev,
            "coherence": self.coherence,
            "angular_momentum": self.angular_momentum,
            "speed": self.speed,
            "turn_angle": self.turn_angle,
        }


class GeometricBridgePlugin:
    """
    Geometry-aware middle step for manifold preprocessing.

    Produces five descriptors:
      1. angular_drift
      2. curvature
      3. radius_dev
      4. coherence
      5. angular_momentum
    """

    def __init__(self) -> None:
        self.prev_z: Optional[List[float]] = None
        self.prev_dz: Optional[List[float]] = None

    def _build_state_vector(self, manifold: Dict[str, Any]) -> List[float]:
        phi = float(manifold.get("phi_corr", 0.0))
        tau = [float(x) for x in manifold.get("torsion_gradient", [])]
        radius = float(manifold.get("radius", 1.0))

        tau_mean = safe_mean(tau[:32])
        tau_energy = norm(tau[:32]) / max(1, min(32, len(tau[:32])))

        return [phi, tau_mean, tau_energy, radius]

    def _compute_angular_momentum(self, z: List[float]) -> Tuple[float, float, float]:
        if self.prev_z is None:
            self.prev_z = list(z)
            return 0.0, 0.0, 0.0

        dz = [z[i] - self.prev_z[i] for i in range(len(z))]
        speed = norm(dz)

        if self.prev_dz is None:
            self.prev_dz = list(dz)
            self.prev_z = list(z)
            return 0.0, speed, 0.0

        dot = sum(dz[i] * self.prev_dz[i] for i in range(len(dz)))
        denom = (norm(dz) * norm(self.prev_dz)) + 1e-9
        cos_theta = clamp(dot / denom, -1.0, 1.0)
        turn_angle = math.acos(cos_theta)

        radius = norm(z)
        angular_momentum = radius * speed * math.sin(turn_angle)

        self.prev_dz = list(dz)
        self.prev_z = list(z)

        return angular_momentum, speed, turn_angle

    def transform(self, manifold: Dict[str, Any]) -> Dict[str, Any]:
        phi = float(manifold.get("phi_corr", 0.0))
        tau = [float(x) for x in manifold.get("torsion_gradient", [])]
        radius = float(manifold.get("radius", 1.0))

        phi_clamped = clamp(phi, -1.0, 1.0)
        angular_drift = math.acos(phi_clamped)

        tau_grad = gradient(tau[:32])
        curvature = norm(tau_grad)

        radius_dev = abs(radius - 1.0)
        coherence = 1.0 / (1.0 + angular_drift * curvature)

        z = self._build_state_vector(manifold)
        angular_momentum, speed, turn_angle = self._compute_angular_momentum(z)

        telemetry = GeometricTelemetry(
            z=z,
            angular_drift=angular_drift,
            curvature=curvature,
            radius_dev=radius_dev,
            coherence=coherence,
            angular_momentum=angular_momentum,
            speed=speed,
            turn_angle=turn_angle,
        )

        return {
            "geometry_features": [
                angular_drift,
                curvature,
                radius_dev,
                coherence,
                angular_momentum,
            ],
            "geometry_debug": telemetry.as_dict(),
            "state_vector": z,
        }


class GeometryAdapter:
    """
    Encodes continuous geometric descriptors into clamped byte inputs.
    """

    def encode(self, features: Sequence[float], nodes_count: Optional[int] = None) -> List[int]:
        padded = list(features)

        if nodes_count is not None:
            if len(padded) < nodes_count:
                padded.extend([0.0] * (nodes_count - len(padded)))
            else:
                padded = padded[:nodes_count]

        scales = [80.0, 50.0, 255.0, 255.0, 120.0]
        encoded: List[int] = []

        for i, value in enumerate(padded):
            scale = scales[i] if i < len(scales) else 64.0
            encoded.append(to_u8_clamped(value * scale))

        return encoded


class GeometryPluginMixin:
    """
    Mixin for a CacheSieve-like object with:
      - self.nodes
      - self.phis
      - node.process(input_u8, phi_u8) -> state int
    """

    def attach_geometry_plugin(self, plugin: Optional[GeometricBridgePlugin] = None) -> None:
        self._geometry_plugin = plugin or GeometricBridgePlugin()
        self._geometry_adapter = GeometryAdapter()

    def triage_bucket_with_geometry(self, manifold: Dict[str, Any]):
        if not hasattr(self, "_geometry_plugin"):
            raise RuntimeError("Geometry plugin not attached. Call attach_geometry_plugin() first.")

        geom = self._geometry_plugin.transform(manifold)
        features = geom["geometry_features"]

        nodes_count = len(self.nodes)
        inputs = self._geometry_adapter.encode(features, nodes_count=nodes_count)

        states: List[int] = []
        for node, input_u8, phi_u8 in zip(self.nodes, inputs, self.phis):
            states.append(int(node.process(input_u8, phi_u8)))

        if not states:
            return False, 0.0, {
                **geom,
                "encoded_inputs": inputs,
                "node_states": [],
                "survival_reason": "no_nodes",
            }

        worst_state = max(states)
        mean_state = safe_mean(states)

        should_survive = worst_state < 2
        score = 1.0 - (mean_state / 3.0)

        telemetry = {
            **geom,
            "encoded_inputs": inputs,
            "node_states": states,
            "worst_state": worst_state,
            "mean_state": mean_state,
            "survival_reason": "ok" if should_survive else "unstable_or_reset",
        }

        return should_survive, score, telemetry


def apply_geometry_plugin(manifold: Dict[str, Any]) -> Dict[str, Any]:
    return GeometricBridgePlugin().transform(manifold)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, Any] = {}

    def register(self, name: str, plugin: Any) -> None:
        self._plugins[name] = plugin

    def get(self, name: str) -> Any:
        return self._plugins.get(name)


if __name__ == "__main__":
    demo = {
        "phi_corr": 0.72,
        "torsion_gradient": [0.10, 0.13, 0.18, 0.16, 0.20],
        "radius": 1.07,
    }
    print(apply_geometry_plugin(demo))
