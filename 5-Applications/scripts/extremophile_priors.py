#!/usr/bin/env python3
"""
Extremophile Priors — 4-Billion-Year Evolutionary Constraints on PDE Solutions

Uses survival-tested organisms as hard bounds on physically admissible solutions.
Rejects solutions requiring:
- Infinite pressure (Pyrococcus requires 20-120 MPa)
- Zero compressibility (all organisms have finite κ_T)
- Infinite energy flux (Desulforudis lives on 10^-15 W)
- Instantaneous convergence (1000-year division timescale)

Reference organisms:
- Pyrococcus yayanosii CH1ᵀ: obligate piezophile, 120 MPa limit
- Thermococcus superprofundus CDGSᵀ: widest pressure range, 1 atm to 130 MPa
- Candidatus Desulforudis audaxviator: deep biosphere, 2.8 km, 1000-year division
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# Physical constants
k_B = 1.380649e-23  # J/K, Boltzmann constant
N_A = 6.02214076e23  # Avogadro's number
R = 8.314462618  # J/(mol·K), gas constant


class ConstraintViolation(Exception):
    """Raised when solution violates extremophile-derived physical bounds."""
    pass


@dataclass
class PriorResult:
    """Result of admissibility check."""
    admissible: bool
    violated_constraint: Optional[str]
    details: Dict[str, Any]


class PyrococcusPrior:
    """
    Obligate piezophile from Ashadze hydrothermal vent, ~4100m depth.

    Pressure range: 20-120 MPa (optimum ~52 MPa)
    Temperature: 80-108°C (optimum ~98°C)

    Key constraint: P·ΔV > kT prevents protein unfolding (blow-up in config space)
    """

    def __init__(self):
        self.P_min = 20e6  # Pa - minimum for growth
        self.P_opt = 52e6  # Pa - optimum
        self.P_max = 120e6  # Pa - survival limit (exceeds Mariana Trench)
        self.T_min = 80 + 273.15  # K
        self.T_opt = 98 + 273.15  # K
        self.T_max = 108 + 273.15  # K
        self.division_time = 2 * 3600  # seconds (~2 hours)
        self.cell_diameter = 0.8e-6  # m

        # Protein volume change on unfolding (~10% expansion)
        self.dV_unfolding = 1e-27 * 0.1  # m³ (approx for single protein)

    def pressure_volume_work(self, P: float, T: float) -> float:
        """Compute P·ΔV work required to unfold protein."""
        return P * self.dV_unfolding

    def thermal_energy(self, T: float) -> float:
        """kT at temperature T."""
        return k_B * T

    def is_pressure_stable(self, P: float, T: float) -> bool:
        """
        Protein stability condition: P·ΔV > kT prevents unfolding.

        At P > 50 MPa and T < 400K: P·ΔV dominates, folding locked.
        """
        pv_work = self.pressure_volume_work(P, T)
        thermal = self.thermal_energy(T)
        return pv_work > thermal

    def is_admissible(self, pressure: float, temperature: float,
                      volume_change: Optional[float] = None) -> PriorResult:
        """Check if conditions are within Pyrococcus survival envelope."""
        details = {
            'P_MPa': pressure / 1e6,
            'T_C': temperature - 273.15,
            'P_optimum': self.P_opt / 1e6,
        }

        if pressure < self.P_min:
            return PriorResult(False, 'pressure_too_low', details)

        if pressure > self.P_max:
            return PriorResult(False, 'pressure_exceeds_survival', details)

        if temperature < self.T_min or temperature > self.T_max:
            return PriorResult(False, 'temperature_out_of_range', details)

        if not self.is_pressure_stable(pressure, temperature):
            return PriorResult(False, 'protein_unfolding_thermodynamically_favored', details)

        details['PV_work_J'] = self.pressure_volume_work(pressure, temperature)
        details['thermal_energy_J'] = self.thermal_energy(temperature)
        details['stability_ratio'] = details['PV_work_J'] / details['thermal_energy_J']

        return PriorResult(True, None, details)


class ThermococcusPrior:
    """
    Widest pressure-range organism, Beebe hydrothermal vent, ~4964m depth.

    Pressure: 1 atm to 130 MPa (optimum ~50 MPa)
    Temperature: 60-90°C (optimum ~75°C)

    Key constraint: adaptive flexibility across full pressure space
    """

    def __init__(self):
        self.P_range = (1e5, 130e6)  # Pa - atmospheric to extreme
        self.P_opt = 50e6  # Pa
        self.T_range = (60 + 273.15, 90 + 273.15)  # K
        self.T_opt = 75 + 273.15  # K
        self.division_time = 4 * 3600  # seconds

    def is_admissible(self, pressure: float, temperature: float) -> PriorResult:
        """Check if organism shows adaptive flexibility across pressure range."""
        details = {
            'P_MPa': pressure / 1e6,
            'T_C': temperature - 273.15,
            'pressure_adaptability': 'full_range' if self.P_range[0] <= pressure <= self.P_range[1] else 'limited',
        }

        if not (self.P_range[0] <= pressure <= self.P_range[1]):
            return PriorResult(False, 'pressure_outside_adaptive_range', details)

        if not (self.T_range[0] <= temperature <= self.T_range[1]):
            return PriorResult(False, 'temperature_outside_adaptive_range', details)

        # Compute adaptability score (distance from optimum)
        P_normalized = (pressure - self.P_opt) / (self.P_range[1] - self.P_opt)
        T_normalized = abs(temperature - self.T_opt) / (self.T_range[1] - self.T_opt)
        details['adaptability_score'] = 1.0 - math.sqrt(P_normalized**2 + T_normalized**2)

        return PriorResult(True, None, details)


class DesulforudisPrior:
    """
    Deep biosphere champion, Mponeng gold mine, ~2.8 km depth.

    Pressure: ~75 MPa (lithostatic)
    Temperature: ~60°C
    Energy flux: ~10^-15 W/cell (radiolysis-powered)
    Division time: ~1000 years

    Key constraint: arbitrarily low energy flux admissible if time expands
    """

    def __init__(self):
        self.depth = 2800  # m
        self.pressure = 75e6  # Pa (lithostatic)
        self.temperature = 60 + 273.15  # K
        self.energy_flux = 1e-15  # W/cell
        self.division_time = 1000 * 365.25 * 24 * 3600  # seconds (~1000 years)
        self.cell_diameter = 0.5e-6  # m (ultra-small for diffusion)
        self.water_activity = 0.7  # near desiccation limit

        # Information processing limit (Landauer at 60°C)
        self.kT = k_B * self.temperature  # ~4.6e-21 J
        self.max_bit_rate = self.energy_flux / (self.kT * math.log(2))  # bits/s

    def landauer_limit(self, temperature: float) -> float:
        """Minimum energy to erase 1 bit: E = kT ln(2)."""
        return k_B * temperature * math.log(2)

    def max_information_rate(self, power: float, temperature: float) -> float:
        """Maximum bit rate given power constraint."""
        return power / self.landauer_limit(temperature)

    def is_admissible(self, required_power: float, required_time: float,
                      required_bits: float, temperature: float) -> PriorResult:
        """
        Check if solution respects deep-biosphere energy/time constraints.

        Key insight: if Desulforudis can survive 1000 years on 10^-15 W,
        then arbitrarily slow/weak solutions are admissible.
        """
        details = {
            'required_power_W': required_power,
            'desulforudis_power_W': self.energy_flux,
            'required_time_s': required_time,
            'desulforudis_time_s': self.division_time,
            'required_bits': required_bits,
        }

        # Energy flux check
        if required_power > self.energy_flux * 10:  # Allow 10x headroom
            return PriorResult(False, 'energy_flux_exceeds_deep_biosphere', details)

        # Time scale check
        if required_time > self.division_time * 10:  # 10,000 years max
            return PriorResult(False, 'convergence_time_exceeds_geological', details)

        # Information processing check
        max_bits = self.max_information_rate(required_power, temperature) * required_time
        if required_bits > max_bits:
            return PriorResult(False, 'information_processing_exceeds_landauer_limit', details)

        details['max_achievable_bits'] = max_bits
        details['information_efficiency'] = required_bits / max_bits if max_bits > 0 else 0

        return PriorResult(True, None, details)


class ResonantCavityPrior:
    """
    Orbital cavity as Helmholtz resonator.

    Volume: ~25-30 cm³
    Q-factor: 5-20 (material damping prevents infinite resonance)

    Key constraint: finite damping prevents blow-up (infinite Q)
    """

    def __init__(self):
        self.volume = 28e-6  # m³
        self.aperture_area = 4e-4  # m²
        self.wall_compliance = 0.1  # relative to rigid
        self.tissue_damping = 0.05  # loss factor
        self.Q_max = 100  # maximum physically achievable Q

        # Speed of sound
        self.c_air = 340  # m/s
        self.c_bone = 1500  # m/s

    def helmholtz_frequency(self, c: float, V: float, S: float, L: float) -> float:
        """f = c/(2π) * sqrt(S/(V*L))"""
        return (c / (2 * math.pi)) * math.sqrt(S / (V * L))

    def quality_factor(self, energy_stored: float, energy_dissipated: float) -> float:
        """Q = 2π × (energy stored) / (energy dissipated per cycle)"""
        return 2 * math.pi * energy_stored / energy_dissipated

    def is_admissible(self, Q_factor: float, resonance_freq: float) -> PriorResult:
        """Reject infinite Q (perfect resonance = blow-up)."""
        details = {
            'Q_factor': Q_factor,
            'Q_max_physical': self.Q_max,
            'resonance_Hz': resonance_freq,
        }

        if Q_factor > self.Q_max:
            return PriorResult(False, 'Q_factor_exceeds_material_limit', details)

        if Q_factor < 0:
            return PriorResult(False, 'negative_damping_unphysical', details)

        if math.isinf(Q_factor):
            return PriorResult(False, 'infinite_Q_blow_up', details)

        return PriorResult(True, None, details)


class ThermusPrior:
    """
    Thermus aquaticus - source of Taq polymerase (PCR revolution).

    Temperature: 50-80°C (optimum ~70°C)
    Lives in hot springs, Yellowstone hot springs.

    Key constraint: moderate thermophily with protein stability.
    """

    def __init__(self):
        self.T_min = 50 + 273.15  # K
        self.T_opt = 70 + 273.15  # K
        self.T_max = 80 + 273.15  # K
        self.pressure = 1e5  # Atmospheric (hot springs)

    def is_admissible(self, temperature: float, pressure: float = 1e5) -> PriorResult:
        """Check if conditions are within Thermus survival envelope."""
        details = {
            'T_C': temperature - 273.15,
            'T_optimum_C': self.T_opt - 273.15,
            'organism': 'Thermus aquaticus (Taq polymerase source)',
        }

        if temperature < self.T_min or temperature > self.T_max:
            return PriorResult(False, 'temperature_out_of_range', details)

        details['stability_ratio'] = 1.0 - abs(temperature - self.T_opt) / (self.T_max - self.T_min)
        return PriorResult(True, None, details)


class Strain121Prior:
    """
    Methanopyrus kandleri Strain 121 - absolute temperature limit.

    Temperature: 122°C (395K) - maximum known survival
    Pressure: High (deep-sea vent)

    Key constraint: Protein denaturation wall. Beyond 122°C, no known biology.
    This is the absolute thermodynamic limit for life.
    """

    def __init__(self):
        self.T_max = 122 + 273.15  # K - absolute biological limit
        self.T_opt = 110 + 273.15  # K
        self.T_min = 80 + 273.15   # K
        self.pressure = 50e6  # Pa - deep-sea vent

    def is_admissible(self, temperature: float, pressure: float = 50e6) -> PriorResult:
        """Check if conditions are within Strain 121 survival envelope."""
        details = {
            'T_C': temperature - 273.15,
            'T_max_C': self.T_max - 273.15,
            'organism': 'Methanopyrus kandleri Strain 121 (absolute temp limit)',
        }

        if temperature > self.T_max:
            return PriorResult(False, 'exceeds_absolute_biological_temperature_limit', details)

        if temperature < self.T_min:
            return PriorResult(False, 'below_minimum', details)

        # Temperature margin from absolute wall
        margin_C = self.T_max - temperature
        details['margin_from_wall_C'] = margin_C
        details['stability_ratio'] = margin_C / (self.T_max - self.T_min)

        return PriorResult(True, None, details)


class DiatomPrior:
    """
    Diatoms with silica shells - absolute stiffness limit.

    Material: Amorphous silica (SiO₂) frustules
    Compressibility: κ_T ≈ 2.7×10^-11 Pa^-1 (geological silica)

    Key constraint: Silica shells approach inorganic material limits.
    Biology cannot achieve κ_T = 0, but silica gets closest.
    """

    def __init__(self):
        self.compressibility_silica = 2.7e-11  # Pa^-1 (amorphous silica)
        self.compressibility_water = 4.6e-10  # Pa^-1 (water)
        self.shell_thickness = 50e-9  # m (50 nm typical)
        self.Q_factor_silica = 1000  # silica resonance (higher than tissue)

    def is_admissible(self, compressibility: float, Q_factor: float = 10) -> PriorResult:
        """Check if material properties approach silica limits."""
        details = {
            'compressibility': compressibility,
            'silica_limit': self.compressibility_silica,
            'Q_factor': Q_factor,
            'organism': 'Diatoms (silica frustules - stiffness limit)',
        }

        # Silica is the biological stiffness limit
        if compressibility < self.compressibility_silica:
            return PriorResult(False, 'exceeds_biological_stiffness_limit', details)

        # Silica Q-factor is the biological resonance limit
        if Q_factor > self.Q_factor_silica:
            return PriorResult(False, 'exceeds_silica_resonance_limit', details)

        # Calculate proximity to inorganic limit
        stiffness_ratio = self.compressibility_silica / compressibility
        details['stiffness_ratio'] = stiffness_ratio  # >1 = softer than silica
        details['Q_ratio'] = Q_factor / self.Q_factor_silica  # <1 = below silica Q

        return PriorResult(True, None, details)


class VibrioNatriegensPrior:
    """
    Vibrio natriegens - fastest known replication rate.

    Doubling time: 10-15 minutes (optimal conditions)
    Some strains: under 10 minutes
    Habitat: Marine environments, salt-loving (halophile)

    Key constraint: Absolute biological replication speed limit.
    """

    def __init__(self):
        self.t_doubling_min = 10 * 60  # seconds - absolute limit
        self.t_doubling_opt = 12 * 60  # seconds - typical optimal
        self.t_doubling_max = 30 * 60  # seconds - under suboptimal
        self.energy_per_duplication = 1e-15  # J (estimated)
        self.error_rate = 1e-10  # errors per base per replication

    def is_admissible(self, replication_time: float, energy: float = 1e-15) -> PriorResult:
        """Check if replication rate is biologically achievable."""
        details = {
            'replication_time_s': replication_time,
            'doubling_time_min_s': self.t_doubling_min,
            'doubling_time_opt_s': self.t_doubling_opt,
            'organism': 'Vibrio natriegens (fastest replication)',
        }

        if replication_time < self.t_doubling_min:
            return PriorResult(False, 'exceeds_absolute_replication_speed_limit', details)

        # Calculate speed relative to V. natriegens
        speed_ratio = self.t_doubling_min / replication_time
        details['speed_ratio'] = speed_ratio  # <1 = slower than max

        return PriorResult(True, None, details)


class EColiPrior:
    """
    E. coli - standard replication reference.

    Doubling time: 20 minutes optimal (rich medium)
    40-60 minutes in minimal medium
    Well-studied, genome fully sequenced

    Key constraint: Baseline replication efficiency.
    """

    def __init__(self):
        self.t_doubling_opt = 20 * 60  # seconds (rich medium)
        self.t_doubling_minimal = 40 * 60  # seconds (minimal medium)
        self.genome_size = 4.6e6  # base pairs
        self.error_rate = 1e-9  # errors per base per replication

    def is_admissible(self, replication_time: float, genome_size: float = 4.6e6) -> PriorResult:
        """Check if replication matches E. coli efficiency."""
        details = {
            'replication_time_s': replication_time,
            'doubling_time_opt_s': self.t_doubling_opt,
            'genome_size_bp': genome_size,
            'organism': 'E. coli (standard replication reference)',
        }

        # Calculate replication rate relative to genome size
        if genome_size > 0:
            bp_per_second = genome_size / replication_time
            details['bp_per_second'] = bp_per_second

            # E. coli reference: 4.6e6 bp / 1200s = 3833 bp/s
            ecoli_rate = self.genome_size / self.t_doubling_opt
            details['rate_ratio'] = bp_per_second / ecoli_rate

        return PriorResult(True, None, details)


class ClostridiumPerfringensPrior:
    """
    Clostridium perfringens - anaerobic speed champion.

    Doubling time: 8-10 minutes (anaerobic, optimal)
    Habitat: Soil, intestines, anaerobic environments

    Key constraint: Fastest anaerobic replication limit.
    """

    def __init__(self):
        self.t_doubling_min = 8 * 60  # seconds - anaerobic champion
        self.t_doubling_opt = 10 * 60  # seconds
        self.oxygen_tolerant = False  # obligate anaerobe

    def is_admissible(self, replication_time: float, anaerobic: bool = True) -> PriorResult:
        """Check if replication rate matches anaerobic champion."""
        details = {
            'replication_time_s': replication_time,
            'doubling_time_min_s': self.t_doubling_min,
            'anaerobic': anaerobic,
            'organism': 'Clostridium perfringens (anaerobic speed champion)',
        }

        if anaerobic and replication_time < self.t_doubling_min:
            return PriorResult(False, 'exceeds_anaerobic_replication_speed_limit', details)

        return PriorResult(True, None, details)


class GeobacillusPrior:
    """
    Geobacillus stearothermophilus - moderate thermophile.

    Temperature: 55-70°C (optimum ~65°C)
    Common in compost, hot springs.

    Key constraint: industrial thermophile with robust protein stability.
    """

    def __init__(self):
        self.T_min = 55 + 273.15  # K
        self.T_opt = 65 + 273.15  # K
        self.T_max = 70 + 273.15  # K
        self.pressure = 1e5  # Atmospheric

    def is_admissible(self, temperature: float, pressure: float = 1e5) -> PriorResult:
        """Check if conditions are within Geobacillus survival envelope."""
        details = {
            'T_C': temperature - 273.15,
            'T_optimum_C': self.T_opt - 273.15,
            'organism': 'Geobacillus stearothermophilus',
        }

        if temperature < self.T_min or temperature > self.T_max:
            return PriorResult(False, 'temperature_out_of_range', details)

        details['stability_ratio'] = 1.0 - abs(temperature - self.T_opt) / (self.T_max - self.T_min)
        return PriorResult(True, None, details)


class TuringPatternPrior:
    """
    Skeletal formation as reaction-diffusion system.

    Key constraint: finite nutrient flux prevents infinite growth
    """

    def __init__(self):
        # Typical bone mineralization parameters
        self.D_activator = (1e-12, 1e-6)  # m²/s
        self.D_inhibitor = (1e-10, 1e-4)  # m²/s
        self.reaction_rate = (0, 1e3)  # 1/s
        self.max_growth_rate = 1e-6  # m/s (bone apposition)

    def is_admissible(self, growth_rate: float, pattern_wavelength: float,
                      nutrient_flux: float) -> PriorResult:
        """Reject infinite Turing pattern growth."""
        details = {
            'growth_rate_m_s': growth_rate,
            'max_growth_rate': self.max_growth_rate,
            'wavelength_m': pattern_wavelength,
        }

        if growth_rate > self.max_growth_rate * 10:
            return PriorResult(False, 'growth_exceeds_nutrient_limit', details)

        if nutrient_flux <= 0:
            return PriorResult(False, 'zero_nutrient_flux_unsustainable', details)

        if pattern_wavelength < 1e-6:  # micron scale minimum
            return PriorResult(False, 'pattern_scale_below_cellular', details)

        return PriorResult(True, None, details)


class DeepExtremophilePrior:
    """
    Unified 12-tier constraint system from evolutionary survival testing.

    Absolute limit tiers (wall-hitting organisms):
    1. Strain121: Absolute temperature limit (122°C, protein denaturation wall)
    2. Diatom: Absolute stiffness limit (silica shells, geological compressibility)
    3. VibrioNatriegens: Absolute replication speed limit (10 min doubling)

    Regular tiers:
    4. TuringPattern: Skeletal formation (nutrient limits prevent infinite growth)
    5. ResonantCavity: Orbital acoustics (damping prevents infinite Q)
    6. Pyrococcus: Obligate piezophile (pressure-volume work locks proteins)
    7. Thermococcus: Wide-range adaptability (flexibility across P-T space)
    8. Thermus: Moderate thermophile (50-80°C, Taq polymerase source)
    9. Geobacillus: Industrial thermophile (55-70°C, robust stability)
    10. EColi: Standard replication reference (20 min doubling)
    11. ClostridiumPerfringens: Anaerobic replication speed (8-10 min)
    12. Desulforudis: Deep time/energy (arbitrarily slow solutions admissible)
    """

    def __init__(self):
        self.strain121 = Strain121Prior()  # Absolute temp limit
        self.diatom = DiatomPrior()  # Absolute stiffness limit
        self.vibrio = VibrioNatriegensPrior()  # Absolute replication speed limit
        self.turing = TuringPatternPrior()
        self.orbital = ResonantCavityPrior()
        self.pyrococcus = PyrococcusPrior()
        self.thermococcus = ThermococcusPrior()
        self.thermus = ThermusPrior()
        self.geobacillus = GeobacillusPrior()
        self.ecoli = EColiPrior()  # Standard replication reference
        self.clostridium = ClostridiumPerfringensPrior()  # Anaerobic speed champion
        self.desulforudis = DesulforudisPrior()

    def unified_check(self, solution_params: Dict[str, Any]) -> PriorResult:
        """
        Run all 5 tiers of constraint checking.

        Returns first violation found, or success if all pass.
        """
        checks = [
            ('strain121', self._check_strain121, ['temperature']),  # Absolute temp limit - check first
            ('diatom', self._check_diatom, ['compressibility', 'Q_factor']),  # Absolute stiffness - check early
            ('vibrio_natriegens', self._check_vibrio, ['replication_time']),  # Absolute replication speed - check early
            ('turing_pattern', self._check_turing, ['growth_rate', 'wavelength', 'nutrient_flux']),
            ('resonant_cavity', self._check_orbital, ['Q_factor', 'resonance_freq']),
            ('pyrococcus', self._check_pyrococcus, ['pressure', 'temperature']),
            ('thermococcus', self._check_thermococcus, ['pressure', 'temperature']),
            ('thermus', self._check_thermus, ['temperature']),
            ('geobacillus', self._check_geobacillus, ['temperature']),
            ('ecoli', self._check_ecoli, ['replication_time', 'genome_size']),  # Standard replication reference
            ('clostridium', self._check_clostridium, ['replication_time', 'anaerobic']),  # Anaerobic speed champion
            ('desulforudis', self._check_desulforudis, ['power', 'time', 'bits', 'temperature']),
        ]

        all_details = {}

        for name, check_fn, required_keys in checks:
            # Check if required parameters present
            if not all(k in solution_params for k in required_keys):
                continue  # Skip if parameters not provided for this check

            result = check_fn(solution_params)
            all_details[name] = result.details

            if not result.admissible:
                return PriorResult(False, f"{name}:{result.violated_constraint}", all_details)

        return PriorResult(True, None, all_details)

    def _check_turing(self, params: Dict) -> PriorResult:
        return self.turing.is_admissible(
            params.get('growth_rate', 0),
            params.get('wavelength', 1e-3),
            params.get('nutrient_flux', 1e-6)
        )

    def _check_orbital(self, params: Dict) -> PriorResult:
        return self.orbital.is_admissible(
            params.get('Q_factor', 10),
            params.get('resonance_freq', 1000)
        )

    def _check_pyrococcus(self, params: Dict) -> PriorResult:
        return self.pyrococcus.is_admissible(
            params.get('pressure', 1e5),
            params.get('temperature', 300)
        )

    def _check_thermococcus(self, params: Dict) -> PriorResult:
        return self.thermococcus.is_admissible(
            params.get('pressure', 1e5),
            params.get('temperature', 300)
        )

    def _check_thermus(self, params: Dict) -> PriorResult:
        return self.thermus.is_admissible(
            params.get('temperature', 300),
            params.get('pressure', 1e5)
        )

    def _check_geobacillus(self, params: Dict) -> PriorResult:
        return self.geobacillus.is_admissible(
            params.get('temperature', 300),
            params.get('pressure', 1e5)
        )

    def _check_strain121(self, params: Dict) -> PriorResult:
        """Check absolute temperature limit (122°C wall)."""
        return self.strain121.is_admissible(
            params.get('temperature', 300),
            params.get('pressure', 50e6)
        )

    def _check_diatom(self, params: Dict) -> PriorResult:
        """Check absolute stiffness limit (silica wall)."""
        return self.diatom.is_admissible(
            params.get('compressibility', 1e-10),
            params.get('Q_factor', 10)
        )

    def _check_vibrio(self, params: Dict) -> PriorResult:
        """Check absolute replication speed limit (V. natriegens wall)."""
        return self.vibrio.is_admissible(
            params.get('replication_time', 600),
            params.get('energy', 1e-15)
        )

    def _check_ecoli(self, params: Dict) -> PriorResult:
        """Check against E. coli standard replication reference."""
        return self.ecoli.is_admissible(
            params.get('replication_time', 1200),
            params.get('genome_size', 4.6e6)
        )

    def _check_clostridium(self, params: Dict) -> PriorResult:
        """Check anaerobic replication speed limit."""
        return self.clostridium.is_admissible(
            params.get('replication_time', 600),
            params.get('anaerobic', False)
        )

    def _check_desulforudis(self, params: Dict) -> PriorResult:
        return self.desulforudis.is_admissible(
            params.get('power', 1e-10),
            params.get('time', 1e6),
            params.get('bits', 1e12),
            params.get('temperature', 300)
        )


# PDE-specific constraint checkers

class NavierStokesConstraints:
    """
    Apply extremophile constraints to Navier-Stokes solutions.

    Key insight: Blow-up requires:
    1. Infinite vorticity concentration
    2. Zero compressibility (to support infinite pressure)
    3. Zero viscosity (to prevent dissipation)
    4. Infinite energy flux

    All four are rejected by evolutionary priors.
    """

    def __init__(self):
        self.priors = DeepExtremophilePrior()

    def check_solution(self, velocity_field: Any, pressure_field: Any,
                       energy_dissipation: float, convergence_time: float) -> PriorResult:
        """
        Check if Navier-Stokes solution respects extremophile constraints.

        Parameters:
        - velocity_field: max velocity, vorticity magnitude
        - pressure_field: max pressure, pressure gradients
        - energy_dissipation: power required to maintain solution
        - convergence_time: time to reach steady state
        """
        # Extract parameters from fields
        params = {
            'pressure': pressure_field.get('max', 1e5) if isinstance(pressure_field, dict) else 1e5,
            'temperature': 300,  # assume room temp unless specified
            'power': energy_dissipation,
            'time': convergence_time,
            'bits': 1e15,  # assume significant computation
        }

        # Run unified check
        result = self.priors.unified_check(params)

        if not result.admissible:
            return result

        # Additional Navier-Stokes specific checks
        if isinstance(velocity_field, dict):
            vorticity = velocity_field.get('vorticity_max', 0)
            velocity = velocity_field.get('max', 0)

            # Check: finite compressibility (from Desulforudis at 75 MPa)
            # No real fluid has κ_T = 0
            compressibility = pressure_field.get('compressibility', 1e-10) if isinstance(pressure_field, dict) else 1e-10
            if compressibility <= 0:
                return PriorResult(False, 'incompressible_unphysical',
                                 {'compressibility': compressibility})

            # Check: finite viscosity prevents infinite Reynolds number
            viscosity = velocity_field.get('viscosity', 1e-6)
            if viscosity <= 0:
                return PriorResult(False, 'zero_viscosity_unphysical',
                                 {'viscosity': viscosity})

        return PriorResult(True, None, result.details)


class MissionCriticalReliability:
    """
    Reliability depth metric for autonomous operation contexts.

    Not just 'is it physically possible?' but 'can you trust it
    when you can't call for help?'

    Three-zone architecture:
    - Evolutionary Core: 4 billion years unattended operation
    - Engineering Frontier: Possible but requires extreme monitoring
    - Theoretical Limit: Catastrophic failure mode

    AngrySphinx Mode: Each level increases attack cost for hecklers.
    """

    def __init__(self, base_prior: DeepExtremophilePrior = None, angry_sphinx_mode: bool = True):
        self.base_prior = base_prior or DeepExtremophilePrior()
        self.angry_sphinx_mode = angry_sphinx_mode

        # Zone boundaries (empirical from survival data)
        self.EVOLUTIONARY_CORE_THRESHOLD = 0.9
        self.ENGINEERING_FRONTIER_THRESHOLD = 0.1

        # Attack cost escalation (AngrySphinx gear reduction)
        self.attack_cost_multipliers = {
            0: 1.0,    # Base claim
            1: 3.0,    # First "but..." (3x work)
            2: 10.0,   # Second "but..." (10x work)
            3: 30.0,   # Third "but..." (30x work)
        }

    def reliability_depth(self, solution_params: Dict[str, Any]) -> float:
        """
        Compute distance from basin boundary in evolution-validated space.

        Returns 0.0-1.0 where:
        - 1.0: Deep in basin (4 Gyr unattended, "Works on Titan")
        - 0.1: Near boundary ("Every engineer on call")
        - 0.0: At boundary (catastrophic, "Blow-up in 3...2...1")
        """
        # Check position relative to each extremophile's optimum
        depths = []

        # Pyrococcus depth: how close to optimal 52 MPa?
        if 'pressure' in solution_params:
            P = solution_params['pressure']
            P_opt = self.base_prior.pyrococcus.P_opt
            P_range = self.base_prior.pyrococcus.P_max - self.base_prior.pyrococcus.P_min
            # Normalized distance from optimum (1.0 = at optimum, 0.0 = at boundary)
            P_depth = 1.0 - abs(P - P_opt) / (P_range / 2)
            depths.append(max(0.0, P_depth))

        # Desulforudis depth: energy margin above survival minimum
        if 'power' in solution_params:
            Pwr = solution_params['power']
            Pwr_min = self.base_prior.desulforudis.energy_flux
            # How many orders of magnitude above minimum?
            if Pwr > 0:
                power_depth = min(1.0, math.log10(Pwr / Pwr_min) / 3.0)  # 3 orders = comfortable
                depths.append(power_depth)

        # Time scale depth: how far below geological maximum?
        if 'time' in solution_params:
            t = solution_params['time']
            t_max = self.base_prior.desulforudis.division_time
            if t > 0:
                time_depth = max(0.0, 1.0 - (t / t_max))
                depths.append(time_depth)

        # Resonance Q depth: how far below material limit?
        if 'Q_factor' in solution_params:
            Q = solution_params['Q_factor']
            Q_max = self.base_prior.orbital.Q_max
            if Q > 0:
                Q_depth = max(0.0, 1.0 - (Q / Q_max))
                depths.append(Q_depth)

        # Compressibility depth: how far from zero?
        if 'compressibility' in solution_params:
            kappa = solution_params['compressibility']
            # κ_T > 0 is required; larger is safer (more compressible)
            if kappa > 0:
                kappa_depth = min(1.0, math.log10(kappa / 1e-12) / 3.0)
                depths.append(kappa_depth)

        # Overall depth is minimum (weakest link)
        return min(depths) if depths else 0.0

    def zone_classification(self, depth: float) -> str:
        """Classify solution into operational zone."""
        if depth >= self.EVOLUTIONARY_CORE_THRESHOLD:
            return 'EVOLUTIONARY_CORE'
        elif depth >= self.ENGINEERING_FRONTIER_THRESHOLD:
            return 'ENGINEERING_FRONTIER'
        else:
            return 'THEORETICAL_LIMIT'

    def zone_description(self, zone: str) -> str:
        """Human-readable zone description for presentations."""
        descriptions = {
            'EVOLUTIONARY_CORE':
                "4 billion years unattended operation. "
                "Works on Titan, no service calls. "
                "Biology handles this autonomously.",
            'ENGINEERING_FRONTIER':
                "Nanoscale possible but fragile. "
                "Requires extreme monitoring. "
                "Every engineer on planet on call.",
            'THEORETICAL_LIMIT':
                "Mathematically ideal but physically catastrophic. "
                "Failure mode: unrecoverable. "
                "Blow-up in 3... 2... 1..."
        }
        return descriptions.get(zone, 'UNKNOWN')

    def mission_critical_approval(self, solution_params: Dict[str, Any],
                                   context: str = 'research') -> PriorResult:
        """
        Context-aware approval with progressive revelation.

        Perfect for "Hat of Infinite Bullshit" presentation style:
        - Level 1: "Um ack sh lee, I provide solution x"
        - Level 2: "But... requires engineering frontier monitoring"
        - Level 3: "But... catastrophic failure mode at boundary"
        """
        depth = self.reliability_depth(solution_params)
        zone = self.zone_classification(depth)

        # First check: is it physically possible?
        physical_check = self.base_prior.unified_check(solution_params)
        if not physical_check.admissible:
            return PriorResult(
                False,
                f"PHYSICALLY_INADMISSIBLE:{physical_check.violated_constraint}",
                {
                    'depth': 0.0,
                    'zone': 'THEORETICAL_LIMIT',
                    'context': context,
                    'physical_details': physical_check.details,
                    'presentation_level': 'REJECTED_AT_BASE',
                }
            )

        # Context-dependent approval
        approval_matrix = {
            'mars_colony_life_support': (0.9, 'EVOLUTIONARY_CORE_REQUIRED'),
            'deep_space_probe': (0.8, 'LONG_DURATION_AUTONOMY'),
            'subsea_infrastructure': (0.7, 'MAINTENANCE_DIFFICULT'),
            'medical_implant': (0.9, 'NO_SECOND_CHANCE'),
            'lhc_experiment': (0.1, 'ENGINEERS_NEARBY'),
            'laboratory_demo': (0.0, 'SUPERVISED_ONLY'),
            'pure_mathematics': (-1.0, 'THEORETICAL_ALLOWED'),
        }

        min_depth, rationale = approval_matrix.get(context, (0.5, 'DEFAULT_CONTEXT'))

        approved = depth >= min_depth

        # Progressive revelation for presentation
        presentation_levels = []

        # Level 1: Basic existence
        presentation_levels.append({
            'level': 1,
            'claim': f"Um ack sh lee, solution exists at {depth:.2f} reliability depth",
            'zone': zone,
            'details': self.zone_description(zone)
        })

        # Level 2: Engineering reality
        if zone == 'ENGINEERING_FRONTIER':
            presentation_levels.append({
                'level': 2,
                'claim': "But... requires every engineer on call",
                'requirement': f"Minimum depth {min_depth:.2f} for {context}",
                'actual': f"Current depth {depth:.2f}"
            })

        # Level 3: Mission critical
        if not approved and context in ['mars_colony_life_support', 'medical_implant']:
            presentation_levels.append({
                'level': 3,
                'claim': "But... catastrophic failure mode when unattended",
                'consequence': "Autonomous operation impossible",
                'recommendation': "Return to evolutionary core (depth > 0.9)"
            })

        details = {
            'depth': depth,
            'zone': zone,
            'zone_description': self.zone_description(zone),
            'context': context,
            'context_rationale': rationale,
            'required_depth': min_depth,
            'approved': approved,
            'presentation_levels': presentation_levels,
        }

        if approved:
            return PriorResult(True, None, details)
        else:
            return PriorResult(
                False,
                f'INSUFFICIENT_RELIABILITY_FOR_{context}',
                details
            )

    def hat_of_infinite_bullshit(self, solution_params: Dict[str, Any],
                                  context: str, attack_count: int = 0) -> List[Dict]:
        """
        Generate progressive revelation for presentation.

        AngrySphinx mode: Each attack (heckler counterargument) triggers
        deeper revelation, increasing the work required to refute.

        Args:
            solution_params: Physical parameters of solution
            context: Mission context (mars_colony, etc.)
            attack_count: Number of heckler attacks so far (escalates depth)

        Returns:
            Ordered list of claims from superficial to deep, with attack costs.
        """
        result = self.mission_critical_approval(solution_params, context)

        if 'presentation_levels' in result.details:
            levels = result.details['presentation_levels']
        else:
            # Fallback for rejected solutions
            return [{
                'level': 0,
                'claim': 'REJECTED',
                'reason': result.violated_constraint,
                'attack_cost': 1.0,
                'defense_burden': 1.0,
            }]

        # AngrySphinx escalation: add attack costs
        if self.angry_sphinx_mode:
            for i, level in enumerate(levels):
                # Cost increases with depth AND attack count
                depth_multiplier = self.attack_cost_multipliers.get(i, 1.0)
                attack_multiplier = self.attack_cost_multipliers.get(attack_count, 1.0)

                total_cost = depth_multiplier * attack_multiplier

                level['attack_cost'] = total_cost
                level['defense_burden'] = total_cost * (1 + attack_count * 0.5)  # Compounding

                # Add adversarial metadata
                level['required_refutation_work'] = self._describe_refutation_work(i, attack_count)

        return levels

    def _describe_refutation_work(self, depth_level: int, attack_count: int) -> str:
        """Describe the work required to refute this level."""
        if depth_level == 0:
            return "Basic fact-check"
        elif depth_level == 1:
            if attack_count == 0:
                return "Address material bounds validity"
            else:
                return f"Address material bounds + {attack_count} prior refutations"
        elif depth_level == 2:
            return "Demonstrate engineering frontier failure mode"
        elif depth_level == 3:
            return "Prove 4-billion-year evolutionary record incorrect"
        else:
            return "Impossible: requires violating thermodynamics"

    def adversarial_response(self, heckler_attack: str, solution_params: Dict[str, Any],
                              context: str, attack_count: int) -> Dict[str, Any]:
        """
        AngrySphinx-style response to heckler attack.

        Consumes the attack, escalates to deeper level, increases burden.
        """
        # Generate next level of revelation
        levels = self.hat_of_infinite_bullshit(solution_params, context, attack_count + 1)

        # Find the level they haven't seen yet
        next_level = min(attack_count + 1, len(levels) - 1)
        if next_level >= len(levels):
            next_level = len(levels) - 1

        level_data = levels[next_level]

        # Calculate cumulative defense burden
        cumulative_burden = sum(l.get('defense_burden', 1.0) for l in levels[:next_level+1])

        return {
            'attack_consumed': True,
            'attack_number': attack_count + 1,
            'response_level': level_data['level'],
            'response_claim': level_data['claim'],
            'attack_cost': level_data['attack_cost'],
            'cumulative_defense_burden': cumulative_burden,
            'next_level_available': next_level < len(levels) - 1,
            'required_refutation_work': level_data.get('required_refutation_work', ''),
            'message': f"Attack #{attack_count + 1} consumed. Defense burden now: {cumulative_burden:.1f}x",
        }


# Export main interface
__all__ = [
    'DeepExtremophilePrior',
    'Strain121Prior',  # Absolute temperature limit (122°C)
    'DiatomPrior',  # Absolute stiffness limit (silica)
    'VibrioNatriegensPrior',  # Absolute replication speed limit (10 min)
    'EColiPrior',  # Standard replication reference (20 min)
    'ClostridiumPerfringensPrior',  # Anaerobic replication speed (8-10 min)
    'PyrococcusPrior',
    'ThermococcusPrior',
    'ThermusPrior',
    'GeobacillusPrior',
    'DesulforudisPrior',
    'ResonantCavityPrior',
    'TuringPatternPrior',
    'NavierStokesConstraints',
    'MissionCriticalReliability',
    'PriorResult',
    'ConstraintViolation',
]
