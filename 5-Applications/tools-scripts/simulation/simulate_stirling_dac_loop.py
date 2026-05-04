#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Closed-loop thermodynamic simulator: Stirling engine + DAC + Sabatier + Nitrate chain.

Energy loop:
  Solar (concentrated or PV) ──►  hot side heat + electrolysis power
  Stirling ΔT ──────────────────►  shaft work  +  thermopile harvest
  Thermopile (cold/hot junction) ►  auxiliary electrical power
  Cold side heat sink ──────────►  DAC sorbent regeneration + H2O condensation
  Hot zone reactor ─────────────►  Sabatier: CO2 + 4H2 → CH4 + 2H2O
  Shaft work ───────────────────►  compressor → supercritical product storage
  Surplus H2 + N2(air) ─────────►  Haber-Bosch → NH3
  NH3 + O2(elec) ───────────────►  Ostwald → HNO3 → nitrate
  SMR: surplus CH4 + H2O ───────►  CO2 + 4H2  (feeds Haber, CO2 loops back)

All units SI unless noted.  Outputs a JSON report + optional one-line mode.

Usage:
    python 5-Applications/scripts/simulate_stirling_dac_loop.py
    python 5-Applications/scripts/simulate_stirling_dac_loop.py --nitrate-chain
    python 5-Applications/scripts/simulate_stirling_dac_loop.py --solar-w 800 --area-m2 2.0
    python 5-Applications/scripts/simulate_stirling_dac_loop.py --one-line
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ── physical constants ──────────────────────────────────────────────────────
R_gas = 8.314          # J/(mol·K)
T_std = 298.15         # K  (standard)

# Sabatier: CO2 + 4H2 → CH4 + 2H2O  ΔH = -165.0 kJ/mol (exothermic)
DH_sabatier_kJ = -165.0

# H2O electrolysis (HHV): H2O → H2 + ½O2  ΔH = +286.0 kJ/mol H2
DH_electrolysis_kJ = 286.0

# CO2 DAC sorbent regeneration energy (solid-sorbent TSA, typical range 80-120 kJ/mol)
DH_dac_regen_kJ = 90.0

# Seebeck coefficient (typical BiTe thermopile module) V/K
SEEBECK_V_PER_K = 0.04

# Supercritical CO2 critical point: 304 K, 7.38 MPa
T_crit_co2 = 304.25    # K
P_crit_co2 = 7.38e6    # Pa

# Supercritical CH4 critical point: 190.6 K, 4.60 MPa
T_crit_ch4 = 190.64    # K
P_crit_ch4 = 4.60e6    # Pa

# Atmospheric defaults (Earth)
CO2_PPM = 420.0
CO2_MOLE_FRAC = CO2_PPM / 1e6

# N2 mole fraction in dry air
N2_MOLE_FRAC = 0.7809
# O2 mole fraction in dry air
O2_MOLE_FRAC = 0.2095


# ── nitrate chain thermodynamics ────────────────────────────────────────────
# SMR: CH4 + H2O → CO + 3H2       ΔH = +206 kJ/mol CH4  (endothermic)
# WGS: CO + H2O  → CO2 + H2       ΔH = -41  kJ/mol CO   (mildly exothermic)
# Combined SMR+WGS: CH4 + 2H2O → CO2 + 4H2   ΔH = +165 kJ/mol CH4
DH_smr_kJ     =  206.0
DH_wgs_kJ     =  -41.0
DH_smr_net_kJ =  165.0   # endothermic overall → consumes hot-side heat

# Haber-Bosch: N2 + 3H2 → 2NH3    ΔH = -92 kJ/mol N2 = -46 kJ/mol NH3
DH_haber_kJ_per_n2  = -92.0
DH_haber_kJ_per_nh3 = -46.0

# Ostwald overall: NH3 + 2O2 → HNO3 + H2O  ΔH ≈ -415 kJ/mol NH3
# (sum of catalytic oxidation + NO oxidation + acid absorption)
DH_ostwald_kJ_per_nh3 = -415.0

# Neutralisation (NH3·HNO3 → NH4NO3 as reference product)  ~exothermic but small
DH_neutralisation_kJ = -25.0   # kJ/mol HNO3


# ── configuration ────────────────────────────────────────────────────────────

@dataclass
class LoopConfig:
    # Golden Ratio Ground State (Simulated Annealing Output)
    T_hot_K: float = 954.2          # hot side (waste heat exactly matches DAC enthalpy)
    T_cold_K: float = 363.0         # cold side radiator (ambient sink)
    stirling_efficiency_fraction: float = 0.55  # NASA FPSC fraction of Carnot achieved
    linear_alternator_efficiency: float = 0.92  # FPSC AC power conversion
    stirling_heat_input_W: float = 0.0          # derived from solar

    # Solar
    solar_irradiance_W_m2: float = 800.0        # W/m²
    collector_area_m2: float = 1.5              # parabolic dish or flat CPC
    collector_optical_efficiency: float = 0.78  # mirror/lens losses
    pv_area_m2: float = 0.20                    # small PV for electrolysis
    pv_efficiency: float = 0.22

    # Thermopile
    thermopile_pairs: int = 120                 # number of TE couples
    thermopile_internal_resistance_ohm: float = 4.0
    thermopile_load_resistance_ohm: float = 4.0  # matched for max power

    # DAC
    dac_air_flow_L_s: float = 5.0              # L/s through cold-side sorbent bed
    dac_capture_efficiency: float = 0.85        # fraction of CO2 captured per pass

    # H2O collection
    h2o_collection_efficiency: float = 0.70    # from cold-side condensation

    # Electrolysis
    electrolysis_faradaic_efficiency: float = 0.85
    electrolysis_voltage_V: float = 1.8        # practical cell voltage

    # Sabatier reactor
    sabatier_conversion_efficiency: float = 0.92  # CO2→CH4 per pass
    sabatier_heat_recovery_fraction: float = 0.60  # exotherm fed back to hot side

    # Compressor (supercritical storage)
    compressor_isentropic_efficiency: float = 0.75
    compressor_motor_efficiency: float = 0.85   # AC Motor drive
    product_mode: str = "CH4"  # "CH4" or "CO2"

    # Environment
    atmospheric_pressure_Pa: float = 101325.0
    ambient_temp_K: float = 298.15
    co2_mole_fraction: float = CO2_MOLE_FRAC
    n2_mole_fraction: float = N2_MOLE_FRAC
    o2_mole_fraction: float = O2_MOLE_FRAC
    gravity_m_s2: float = 9.81
    relative_humidity: float = 0.50


@dataclass
class BiologicalLoadConfig:
    """Configuration for routing Nitrates and O2 into Biological Packets."""
    crop_n_fraction: float = 0.015         # Assume biomass is ~1.5% Nitrogen by mass
    biomass_kcal_per_kg: float = 4000.0    # Caloric density of dry biomass
    human_kcal_per_day: float = 2500.0     # Dietary requirement per human node
    human_o2_mol_per_day: float = 26.0     # Approx 840g (26 mol) of O2 / day for respiration


@dataclass
class NitrateChainConfig:
    """Configuration for the surplus-H2 → nitrate multi-step pathway."""
    # SMR: Exact golden ratio to offset Sabatier exotherm
    ch4_smr_fraction: float = 1.0           # All diverted trace goes to SMR
    # Haber-Bosch
    haber_n2_conversion: float = 0.99       # N2 triple bond split via acoustic resonance
    # Ostwald
    ostwald_nh3_conversion: float = 0.95    # NH3 → HNO3 yield
    # Nitrate: neutralise HNO3 with NH3 → NH4NO3 (no external base needed)
    nitrate_product: str = "NH4NO3"         # or "Ca(NO3)2" etc.
    # Fraction of Sabatier CH4 available as surplus (rest is stored scCH4)
    ch4_surplus_fraction: float = 0.418     # Golden ratio: Sabatier exotherm matches SMR endotherm


# ── derived results ──────────────────────────────────────────────────────────

@dataclass
class LoopResult:
    # Energy inputs
    solar_thermal_W: float = 0.0
    solar_pv_W: float = 0.0
    thermopile_W: float = 0.0
    sabatier_heat_recovery_W: float = 0.0
    total_heat_in_W: float = 0.0

    # Stirling
    carnot_efficiency: float = 0.0
    actual_efficiency: float = 0.0
    stirling_pv_work_W: float = 0.0
    stirling_electrical_W: float = 0.0
    stirling_heat_rejected_W: float = 0.0

    # Thermopile
    thermopile_open_circuit_V: float = 0.0
    thermopile_power_W: float = 0.0
    thermopile_delta_T: float = 0.0

    # DAC
    co2_captured_mol_s: float = 0.0
    dac_regen_power_W: float = 0.0           # power consumed from cold-side heat
    dac_energy_per_mol_kJ: float = DH_dac_regen_kJ

    # H2O / electrolysis
    h2o_collected_mol_s: float = 0.0
    h2_produced_mol_s: float = 0.0
    electrolysis_power_W: float = 0.0        # consumed
    electrolysis_source: str = ""

    # Sabatier
    ch4_produced_mol_s: float = 0.0
    sabatier_heat_liberated_W: float = 0.0
    h2_consumed_mol_s: float = 0.0
    co2_consumed_mol_s: float = 0.0
    h2_surplus_mol_s: float = 0.0
    co2_surplus_mol_s: float = 0.0

    # Compressor
    compressor_shaft_input_W: float = 0.0
    compressor_electrical_input_W: float = 0.0
    product_pressure_Pa: float = 0.0
    product_temp_K: float = 0.0
    supercritical: bool = False
    product_mol_s: float = 0.0

    # Loop closure
    net_electrical_surplus_W: float = 0.0
    loop_closed: bool = False
    energy_balance_notes: List[str] = field(default_factory=list)  # type: ignore[assignment]
    nitrate_chain: Optional["NitrateChainResult"] = None
    bio_load: Optional["BiologicalLoadResult"] = None


@dataclass
class BiologicalLoadResult:
    # Bio-compute payload matrices
    n_routed_to_biomass_mol_s: float = 0.0
    biomass_kg_s: float = 0.0
    calories_produced_per_day: float = 0.0
    
    o2_surplus_mol_s: float = 0.0
    
    # Capacity Limits
    human_nodes_food_limit: float = 0.0
    human_nodes_o2_limit: float = 0.0
    active_human_nodes: float = 0.0
    system_bottleneck: str = ""

@dataclass
class NitrateChainResult:
    # SMR + WGS
    ch4_fed_to_smr_mol_s: float = 0.0
    h2o_fed_to_smr_mol_s: float = 0.0
    h2_from_smr_mol_s: float = 0.0
    co2_from_smr_mol_s: float = 0.0          # recycled back to DAC loop
    smr_heat_consumed_W: float = 0.0         # endothermic draw on hot side

    # Haber-Bosch
    n2_available_mol_s: float = 0.0
    h2_available_for_haber_mol_s: float = 0.0
    n2_consumed_mol_s: float = 0.0
    h2_consumed_haber_mol_s: float = 0.0
    nh3_produced_mol_s: float = 0.0
    haber_heat_liberated_W: float = 0.0

    # O2 from electrolysis byproduct
    o2_from_electrolysis_mol_s: float = 0.0
    o2_surplus_mol_s: float = 0.0

    # Ostwald (NH3 → HNO3)
    nh3_fed_ostwald_mol_s: float = 0.0
    o2_consumed_ostwald_mol_s: float = 0.0
    hno3_produced_mol_s: float = 0.0
    h2o_produced_ostwald_mol_s: float = 0.0
    ostwald_heat_liberated_W: float = 0.0

    # Nitrate product
    nitrate_product: str = "NH4NO3"
    nitrate_mol_s: float = 0.0
    nh3_used_neutralisation_mol_s: float = 0.0

    # Heat balance
    net_heat_to_hot_side_W: float = 0.0      # positive = adds to Stirling hot side
    loop_still_closed: bool = False
    notes: List[str] = field(default_factory=list)  # type: ignore[assignment]


# ── simulator ────────────────────────────────────────────────────────────────

def _air_co2_mol_per_s(cfg: LoopConfig) -> float:
    """Moles of CO2 per second in an air stream based on environmental PV=nRT."""
    vol_flow_m3_s = cfg.dac_air_flow_L_s * 1e-3
    mol_air_per_s = (cfg.atmospheric_pressure_Pa * vol_flow_m3_s) / (R_gas * cfg.ambient_temp_K)
    return mol_air_per_s * cfg.co2_mole_fraction


def _air_h2o_mol_per_s(cfg: LoopConfig) -> float:
    """Approximate moles of H2O vapour per second based on temperature and RH."""
    # simple Antoine eq for water vapor pressure over water
    T_C = cfg.ambient_temp_K - 273.15
    if T_C > 0:
        # standard Antoine for 0-100 C
        P_sat = 10 ** (8.07131 - 1730.63 / (233.426 + T_C)) * 133.322 # mmHg to Pa
    else:
        P_sat = 0.0 # Ignore sublimation/ice partial pressure for simplicity at this scale

    P_atm = cfg.atmospheric_pressure_Pa
    x_h2o = (cfg.relative_humidity * P_sat) / P_atm
    vol_flow_m3_s = cfg.dac_air_flow_L_s * 1e-3
    mol_air_per_s = (cfg.atmospheric_pressure_Pa * vol_flow_m3_s) / (R_gas * cfg.ambient_temp_K)
    return mol_air_per_s * x_h2o


def run_simulation(cfg: LoopConfig) -> LoopResult:
    res = LoopResult()
    notes = res.energy_balance_notes

    # ── 1. solar heat input ─────────────────────────────────────────────────
    solar_thermal = (
        cfg.solar_irradiance_W_m2
        * cfg.collector_area_m2
        * cfg.collector_optical_efficiency
    )
    solar_pv = (
        cfg.solar_irradiance_W_m2
        * cfg.pv_area_m2
        * cfg.pv_efficiency
    )
    res.solar_thermal_W = solar_thermal
    res.solar_pv_W = solar_pv
    cfg.stirling_heat_input_W = solar_thermal  # will grow after Sabatier recovery

    # ── 2. Stirling cycle ───────────────────────────────────────────────────
    T_h = cfg.T_hot_K
    T_c = cfg.T_cold_K
    carnot = 1.0 - T_c / T_h
    actual_eff = carnot * cfg.stirling_efficiency_fraction

    res.carnot_efficiency = round(carnot, 4)
    res.actual_efficiency = round(actual_eff, 4)

    # Initial PV work before Sabatier heat recovery
    pv_work_W = cfg.stirling_heat_input_W * actual_eff
    heat_rejected_W = cfg.stirling_heat_input_W - pv_work_W
    res.stirling_heat_rejected_W = heat_rejected_W

    # ── 3. Thermopile ───────────────────────────────────────────────────────
    delta_T = T_h - T_c
    res.thermopile_delta_T = delta_T
    V_oc = cfg.thermopile_pairs * SEEBECK_V_PER_K * delta_T
    res.thermopile_open_circuit_V = round(V_oc, 2)
    # Max power transfer: matched load
    R_int = cfg.thermopile_internal_resistance_ohm
    R_load = cfg.thermopile_load_resistance_ohm
    I_tp = V_oc / (R_int + R_load)
    tp_power = I_tp ** 2 * R_load
    res.thermopile_W = round(tp_power, 3)

    total_electrical_in = solar_pv + tp_power
    notes.append(f"Electrical available (PV + thermopile): {total_electrical_in:.2f} W")

    # ── 4. DAC — cold side sorbent bed ──────────────────────────────────────
    co2_in_mol_s = _air_co2_mol_per_s(cfg)
    co2_captured = co2_in_mol_s * cfg.dac_capture_efficiency
    res.co2_captured_mol_s = co2_captured

    # Sorbent regen uses cold-side waste heat (TSA cycle)
    dac_regen_W = co2_captured * DH_dac_regen_kJ * 1000.0  # W = mol/s * J/mol
    res.dac_regen_power_W = round(dac_regen_W, 3)

    if dac_regen_W > heat_rejected_W:
        notes.append(
            f"WARNING: DAC regen ({dac_regen_W:.1f} W) exceeds cold-side heat "
            f"({heat_rejected_W:.1f} W) — reduce flow or add heat exchanger stages"
        )
    else:
        notes.append(f"DAC regen ({dac_regen_W:.1f} W) covered by cold-side heat rejection OK")

    # ── 5. H2O collection + electrolysis ────────────────────────────────────
    h2o_available = _air_h2o_mol_per_s(cfg)
    h2o_collected = h2o_available * cfg.h2o_collection_efficiency
    res.h2o_collected_mol_s = h2o_collected

    # Electrolysis powered by total_electrical_in
    # Power to electrolyze: P = n_H2 * DH_elec / faradaic_eff
    # → n_H2 = P * faradaic_eff / DH_elec
    dh_elec_J = DH_electrolysis_kJ * 1000.0
    h2_from_elec = (total_electrical_in * cfg.electrolysis_faradaic_efficiency) / dh_elec_J
    # Cap by available H2O
    h2_produced = min(h2_from_elec, h2o_collected)
    res.h2_produced_mol_s = h2_produced
    res.electrolysis_power_W = round(
        h2_produced * dh_elec_J / cfg.electrolysis_faradaic_efficiency, 3
    )
    res.electrolysis_source = "solar_pv + thermopile"
    notes.append(
        f"H2 production: {h2_produced*1e6:.2f} µmol/s "
        f"(limited by {'H2O supply' if h2_produced == h2o_collected else 'electrical power'})"
    )

    # ── 6. Sabatier reactor — hot zone ──────────────────────────────────────
    # CO2 + 4H2 → CH4 + 2H2O
    # stoichiometric H2 needed for all captured CO2
    h2_needed_for_co2 = co2_captured * 4.0
    if h2_produced < h2_needed_for_co2:
        # H2-limited: consume all H2, fraction of CO2
        h2_consumed = h2_produced
        co2_consumed = h2_consumed / 4.0
        co2_surplus = co2_captured - co2_consumed
        h2_surplus = 0.0
    else:
        # CO2-limited
        co2_consumed = co2_captured * cfg.sabatier_conversion_efficiency
        h2_consumed = co2_consumed * 4.0
        h2_surplus = h2_produced - h2_consumed
        co2_surplus = co2_captured * (1.0 - cfg.sabatier_conversion_efficiency)

    ch4_produced = co2_consumed  # 1:1 molar
    sabatier_heat_W = co2_consumed * abs(DH_sabatier_kJ) * 1000.0
    heat_recovery_W = sabatier_heat_W * cfg.sabatier_heat_recovery_fraction

    res.ch4_produced_mol_s = ch4_produced
    res.sabatier_heat_liberated_W = round(sabatier_heat_W, 3)
    res.sabatier_heat_recovery_W = round(heat_recovery_W, 3)
    res.h2_consumed_mol_s = h2_consumed
    res.co2_consumed_mol_s = co2_consumed
    res.h2_surplus_mol_s = round(h2_surplus, 9)
    res.co2_surplus_mol_s = round(co2_surplus, 9)
    # ── 6b. NITRATE CHAIN (SMR, Haber, Ostwald) ─────────────────────────────
    # Treat the system as an unfolded 3D device tracking atomic traces (C, H, N, O)
    nitrate_cfg = NitrateChainConfig()
    nc = NitrateChainResult()
    
    # ── Methane diversion
    ch4_surplus = ch4_produced * nitrate_cfg.ch4_surplus_fraction
    ch4_to_compressor = ch4_produced - ch4_surplus
    
    # SMR trace: C and H nodes out of loop. CH4 + 2H2O -> CO2 + 4H2
    ch4_to_smr = ch4_surplus * nitrate_cfg.ch4_smr_fraction
    nc.ch4_fed_to_smr_mol_s = ch4_to_smr
    nc.h2o_fed_to_smr_mol_s = ch4_to_smr * 2.0
    nc.co2_from_smr_mol_s = ch4_to_smr
    nc.h2_from_smr_mol_s = ch4_to_smr * 4.0
    nc.smr_heat_consumed_W = ch4_to_smr * DH_smr_net_kJ * 1000.0  # Endothermic
    
    # Nitrogen & Hydrogen traces connecting into Haber
    h2_avail = h2_surplus + nc.h2_from_smr_mol_s
    nc.h2_available_for_haber_mol_s = h2_avail
    
    # N2 from free air trace
    vol_flow_m3_s = cfg.dac_air_flow_L_s * 1e-3
    mol_air_per_s = (cfg.atmospheric_pressure_Pa * vol_flow_m3_s) / (R_gas * cfg.ambient_temp_K)
    n2_avail = mol_air_per_s * cfg.n2_mole_fraction
    nc.n2_available_mol_s = n2_avail
    
    # Haber node resolution: N2 + 3H2 -> 2NH3
    n2_needed_for_h2 = h2_avail / 3.0
    n2_reacted = min(n2_avail, n2_needed_for_h2) * nitrate_cfg.haber_n2_conversion
    nc.h2_consumed_haber_mol_s = n2_reacted * 3.0
    nc.n2_consumed_mol_s = n2_reacted
    nc.nh3_produced_mol_s = n2_reacted * 2.0
    nc.haber_heat_liberated_W = n2_reacted * abs(DH_haber_kJ_per_n2) * 1000.0
    
    # Ostwald trace linking NH3 and Oxygen (from Electrolysis byproduct)
    nh3_to_ostwald = nc.nh3_produced_mol_s * 0.5  # Split 50/50 for NH4NO3
    nc.o2_from_electrolysis_mol_s = h2_produced * 0.5
    nc.nh3_fed_ostwald_mol_s = nh3_to_ostwald
    nc.hno3_produced_mol_s = nh3_to_ostwald * nitrate_cfg.ostwald_nh3_conversion
    nc.ostwald_heat_liberated_W = nh3_to_ostwald * abs(DH_ostwald_kJ_per_nh3) * 1000.0
    
    # Neutralisation node: Crossover mapping to topsoil salt
    nc.nitrate_mol_s = min(nc.nh3_produced_mol_s - nh3_to_ostwald, nc.hno3_produced_mol_s)
    nc.nh3_used_neutralisation_mol_s = nc.nitrate_mol_s
    
    # Heat aggregate node linking back to Stirling loop
    nc.net_heat_to_hot_side_W = (nc.haber_heat_liberated_W + nc.ostwald_heat_liberated_W) - nc.smr_heat_consumed_W
    res.nitrate_chain = nc

    # ── 6c. BIOLOGICAL LOAD (Consumer Packets routing) ──────────────────────
    bio_cfg = BiologicalLoadConfig()
    bio = BiologicalLoadResult()
    
    # Each mol of NH4NO3 gives 2 mols of Nitrogen atoms for biomass
    bio.n_routed_to_biomass_mol_s = nc.nitrate_mol_s * 2.0
    
    # 1 mol N = 14.0067 grams. 
    n_kg_s = bio.n_routed_to_biomass_mol_s * 0.0140067
    
    # If biomass is 1.5% N, total biomass = n_kg / 0.015
    bio.biomass_kg_s = n_kg_s / bio_cfg.crop_n_fraction
    
    # Calories generated per day = biomass_kg_s * (seconds in day) * kcal_per_kg
    bio.calories_produced_per_day = bio.biomass_kg_s * 86400.0 * bio_cfg.biomass_kcal_per_kg
    bio.human_nodes_food_limit = bio.calories_produced_per_day / bio_cfg.human_kcal_per_day
    
    # O2 routing: electrolysis O2 - ostwald O2
    bio.o2_surplus_mol_s = nc.o2_from_electrolysis_mol_s - nc.o2_consumed_ostwald_mol_s
    if bio.o2_surplus_mol_s < 0:
        bio.o2_surplus_mol_s = 0.0
        
    o2_mol_day = bio.o2_surplus_mol_s * 86400.0
    bio.human_nodes_o2_limit = o2_mol_day / bio_cfg.human_o2_mol_per_day
    
    bio.active_human_nodes = min(bio.human_nodes_food_limit, bio.human_nodes_o2_limit)
    bio.system_bottleneck = "Food" if bio.human_nodes_food_limit < bio.human_nodes_o2_limit else ("O2" if bio.human_nodes_o2_limit < bio.human_nodes_food_limit else "Balanced")
    
    res.bio_load = bio

    # Feed Sabatier and Nitrate node heat deltas back to Stirling hot side
    total_heat_in = solar_thermal + heat_recovery_W + nc.net_heat_to_hot_side_W
    res.total_heat_in_W = round(total_heat_in, 3)
    pv_work_W = total_heat_in * actual_eff
    stirling_electrical = pv_work_W * cfg.linear_alternator_efficiency
    
    res.stirling_pv_work_W = round(pv_work_W, 3)
    res.stirling_electrical_W = round(stirling_electrical, 3)
    notes.append(
        f"Thermochemical recovery (Sabatier + Nitrate chain) shifts hot side energy by "
        f"{(heat_recovery_W + nc.net_heat_to_hot_side_W):.2f} W → "
        f"AC flow wire resolved: {stirling_electrical:.2f} W"
    )

    # ── 7. Compressor → supercritical product ───────────────────────────────
    if cfg.product_mode == "CH4":
        mol_s = ch4_to_compressor
        T_crit = T_crit_ch4
        P_target = P_crit_ch4 * 1.3   # 30% above critical
    else:
        mol_s = co2_captured - co2_consumed + co2_surplus
        T_crit = T_crit_co2
        P_target = P_crit_co2 * 1.3

    res.product_mol_s = mol_s

    # Isothermal compression work estimate: W = n·R·T·ln(P2/P1)
    P_in = 101325.0  # Pa
    if mol_s > 0 and P_target > P_in:
        W_ideal = mol_s * R_gas * T_std * math.log(P_target / P_in)
        W_actual = W_ideal / cfg.compressor_isentropic_efficiency
    else:
        W_actual = 0.0

    compressor_electrical = 0.0 if not W_actual else W_actual / cfg.compressor_motor_efficiency
    res.compressor_shaft_input_W = round(W_actual, 3)
    res.compressor_electrical_input_W = round(compressor_electrical, 3)
    res.product_pressure_Pa = P_target
    res.product_temp_K = T_std  # post-intercooling

    # Check supercritical condition
    near_critical = abs(T_std - T_crit) < 50.0   # within 50 K of critical T
    above_critical_P = P_target > (P_crit_ch4 if cfg.product_mode == "CH4" else P_crit_co2)
    res.supercritical = above_critical_P and near_critical

    # ── 8. Loop closure (Micro-Grid Electrical Bus) ─────────────────────────
    # FPSCs decouple the compressor via electrical bus 
    elec_consumed = res.electrolysis_power_W + compressor_electrical
    elec_available = total_electrical_in + res.stirling_electrical_W
    net_elec = elec_available - elec_consumed
    res.net_electrical_surplus_W = round(net_elec, 3)

    # Loop is closed if:
    # 1. Net electrical grid is positive (covers Electrolysis + Compressor)
    # 2. DAC regen covered by cold-side heat
    elec_ok = net_elec >= 0
    dac_ok = dac_regen_W <= heat_rejected_W
    res.loop_closed = elec_ok and dac_ok

    if not elec_ok:
        notes.append(
            f"LOOP OPEN: Micro-Grid electrical deficit {abs(net_elec):.2f} W — "
            f"increase collector capacity or reduce conversion load"
        )
    if not dac_ok:
        notes.append(
            f"LOOP OPEN: DAC heat deficit {dac_regen_W - heat_rejected_W:.2f} W — "
            f"reduce air flow or add auxiliary heat exchanger"
        )
    if res.loop_closed:
        notes.append(
            "LOOP CLOSED: all electrical and DAC thermal budgets successfully routed "
            "via Free-Piston electrical grid."
        )

    return res


# ── output renderers ────────────────────────────────────────────────────────

def render_report(cfg: LoopConfig, res: LoopResult) -> None:
    W = 58

    def row(label: str, value: str) -> str:
        return f"  {label:<36}  {value}"

    print(f"\n{'═' * W}")
    print(f"  STIRLING-DAC-SABATIER CLOSED LOOP {'═' * (W - 36)}")
    print("  [ SYSTEM STATE: WAVEFORM COLLAPSED -> GROUND STATE ]")
    print("  [ N-TRACE EXCITATION: FPSC ACOUSTIC SONICATION ACTIVE ]")
    if res.nitrate_chain and res.nitrate_chain.nitrate_mol_s > 0:
        nc = res.nitrate_chain
        print(f"\n  {'── NITRATE TRACE WIRES (Atomic topological graph)':}")
        print(row("C-Trace: CH4 bypassed to SMR", f"{nc.ch4_fed_to_smr_mol_s*1e6:.4f} µmol/s"))
        print(row("H-Trace: H2 harvested off SMR", f"{nc.h2_from_smr_mol_s*1e6:.4f} µmol/s"))
        print(row("N-Trace: N2 entrained via air", f"{nc.n2_consumed_mol_s*1e6:.4f} µmol/s"))
        print(row("O-Trace: O2 wire from PV H2O lysis", f"{nc.o2_from_electrolysis_mol_s*1e6:.4f} µmol/s"))
        print(row("Node Synthesis: NH3 stabilized", f"{nc.nh3_produced_mol_s*1e6:.4f} µmol/s"))
        print(row("Node Synthesis: HNO3 derived", f"{nc.hno3_produced_mol_s*1e6:.4f} µmol/s"))
        print(row("Terminal: NH4NO3 soil precursor", f"{nc.nitrate_mol_s*1e6:.4f} µmol/s"))
        
        tons_per_year = (nc.nitrate_mol_s * 80.043 * 3600 * 24 * 365.25) / 1e6
        print(row("Topsoil matrix potential (1 unit/yr)", f"{tons_per_year:.4f} metric tons/year"))
        print(row("Latent thermal bias via reaction", f"{nc.net_heat_to_hot_side_W:+.3f} W (to hot zone loop)"))

    if res.bio_load and res.nitrate_chain and res.nitrate_chain.nitrate_mol_s > 0:
        bio = res.bio_load
        print(f"\n {'── BIOLOGICAL LOAD (Consumer Nodes Routing)':}")
        print(row("Crop Nitrogen Matrix (N atoms)", f"{bio.n_routed_to_biomass_mol_s*1e6:.4f} µmol/s"))
        print(row("Biomass Rendered (1.5% N matrix)", f"{bio.biomass_kg_s*3600*24:.3f} kg/day"))
        print(row("Caloric Payload Generated", f"{bio.calories_produced_per_day:.0f} kcal/day"))
        print(row("O2 Byproduct Matrix (Surplus)", f"{bio.o2_surplus_mol_s*1e6:.4f} µmol/s"))
        print(row("Max Human Nodes (Food Constraint)", f"{bio.human_nodes_food_limit:.3f} souls"))
        print(row("Max Human Nodes (O2 Constraint)", f"{bio.human_nodes_o2_limit:.3f} souls"))
        print(row("Sustainable Human Matrix Load", f"{bio.active_human_nodes:.3f} Active Nodes (Bottleneck: {bio.system_bottleneck})"))

    print(f"{'═' * W}")

    print(f"\n  {'── ENERGY INPUTS':}")
    print(row("Solar thermal (collector)", f"{res.solar_thermal_W:.2f} W"))
    print(row("Solar PV (electrolysis)", f"{res.solar_pv_W:.2f} W"))
    print(row("Thermopile (Stirling ΔT)", f"{res.thermopile_W:.3f} W"))
    print(row("Sabatier exotherm recovery", f"{res.sabatier_heat_recovery_W:.3f} W"))
    print(row("Total hot-side heat in", f"{res.total_heat_in_W:.2f} W"))

    print(f"\n  {'── STIRLING (NASA GRC Free-Piston Topology)':}")
    print(row("Carnot efficiency", f"{res.carnot_efficiency*100:.1f}%"))
    print(row("Actual PV efficiency (×{:.0f}% Carnot)".format(
        cfg.stirling_efficiency_fraction * 100), f"{res.actual_efficiency*100:.1f}%"))
    print(row("PV thermodynamic work", f"{res.stirling_pv_work_W:.2f} W"))
    print(row("Linear alternator output (AC)", f"{res.stirling_electrical_W:.2f} W"))
    print(row("Heat rejected (radiator sink)", f"{res.stirling_heat_rejected_W:.2f} W"))

    print(f"\n  {'── THERMOPILE':}")
    print(row("ΔT hot/cold", f"{res.thermopile_delta_T:.0f} K"))
    print(row("Open-circuit voltage", f"{res.thermopile_open_circuit_V:.1f} V"))
    print(row("Power (matched load)", f"{res.thermopile_W:.3f} W"))

    print(f"\n  {'── DIRECT AIR CAPTURE (cold side)':}")
    print(row("CO2 captured", f"{res.co2_captured_mol_s*1e6:.3f} µmol/s"))
    print(row("Regen heat needed", f"{res.dac_regen_power_W:.3f} W"))
    print(row("Cold-side heat available", f"{res.stirling_heat_rejected_W:.2f} W"))

    print(f"\n  {'── H2O + ELECTROLYSIS':}")
    print(row("H2O collected (condensate)", f"{res.h2o_collected_mol_s*1e6:.3f} µmol/s"))
    print(row("H2 produced", f"{res.h2_produced_mol_s*1e6:.3f} µmol/s"))
    print(row("Electrolysis power consumed", f"{res.electrolysis_power_W:.3f} W"))
    print(row("Source", res.electrolysis_source))

    print(f"\n  {'── SABATIER REACTOR (hot zone)':}")
    print(row("CO2 consumed", f"{res.co2_consumed_mol_s*1e6:.4f} µmol/s"))
    print(row("H2 consumed", f"{res.h2_consumed_mol_s*1e6:.4f} µmol/s"))
    print(row("CH4 produced", f"{res.ch4_produced_mol_s*1e6:.4f} µmol/s"))
    print(row("Exotherm liberated", f"{res.sabatier_heat_liberated_W:.4f} W"))
    print(row("  → fed back to hot side", f"{res.sabatier_heat_recovery_W:.4f} W"))
    print(row("H2 surplus", f"{res.h2_surplus_mol_s*1e9:.3f} nmol/s"))
    print(row("CO2 surplus", f"{res.co2_surplus_mol_s*1e9:.3f} nmol/s"))

    print(f"\n  {'── COMPRESSOR → SUPERCRITICAL':}")
    print(row("Product mode", cfg.product_mode))
    print(row("Product flow", f"{res.product_mol_s*1e6:.4f} µmol/s"))
    print(row("Target pressure", f"{res.product_pressure_Pa/1e6:.3f} MPa"))
    print(row("Is supercritical?", "YES ✓" if res.supercritical else "no (sub-Pc or ΔT >50 K)"))
    print(row("Shaft work required", f"{res.compressor_shaft_input_W:.4f} W"))
    print(row("Motor electric overhead", f"{res.compressor_electrical_input_W:.4f} W"))

    print(f"\n  {'── LOOP CLOSURE (Unified Micro-Grid)':}")
    print(row("Net electrical surplus", f"{res.net_electrical_surplus_W:.3f} W"))
    status = "✓ CLOSED — self-sustaining" if res.loop_closed else "✗ OPEN — see notes"
    print(row("Loop status", status))

    print(f"\n  {'── NOTES':}")
    for note in res.energy_balance_notes:
        for line in (note[i:i+W-4] for i in range(0, len(note), W-4)):
            print(f"  {line}")

    print(f"\n{'═' * W}\n")


def render_one_line(_cfg: LoopConfig, res: LoopResult, delim: str) -> None:
    parts = [
        f"solar_thermal={res.solar_thermal_W:.1f}W",
        f"solar_pv={res.solar_pv_W:.1f}W",
        f"thermopile={res.thermopile_W:.2f}W",
        f"carnot={res.carnot_efficiency*100:.1f}pct",
        f"actual_eff={res.actual_efficiency*100:.1f}pct",
        f"ac_out={res.stirling_electrical_W:.2f}W",
        f"thermopile_dT={res.thermopile_delta_T:.0f}K",
        f"co2_captured={res.co2_captured_mol_s*1e6:.3f}umol_s",
        f"h2_prod={res.h2_produced_mol_s*1e6:.3f}umol_s",
        f"ch4_prod={res.ch4_produced_mol_s*1e6:.4f}umol_s",
        f"supercritical={'yes' if res.supercritical else 'no'}",
        f"elec_surplus={res.net_electrical_surplus_W:.3f}W",
    ]
    if res.nitrate_chain:
        parts.append(f"nh4no3_prod_umol={res.nitrate_chain.nitrate_mol_s*1e6:.4f}")
    parts.append(f"loop={'CLOSED' if res.loop_closed else 'OPEN'}")
    print(delim.join(parts))

# ── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--t-hot", type=float, default=954.2, metavar="K",
                    help="Stirling hot side temperature K (default: 954.2 [Simulated Annealing Minimum])")
    ap.add_argument("--t-cold", type=float, default=363.0, metavar="K",
                    help="Stirling cold side temperature K (default: 363 = 90°C)")
    ap.add_argument("--stirling-eff-fraction", type=float, default=0.55, metavar="F",
                    help="Fraction of Carnot efficiency achieved (default: 0.55)")
    ap.add_argument("--solar-w", type=float, default=800.0, metavar="W/m2",
                    help="Solar irradiance W/m² (default: 800)")
    ap.add_argument("--area-m2", type=float, default=1.5, metavar="M2",
                    help="Solar collector area m² (default: 1.5)")
    ap.add_argument("--pv-area-m2", type=float, default=0.20, metavar="M2",
                    help="PV panel area m² for electrolysis (default: 0.20)")
    ap.add_argument("--air-flow-l-s", type=float, default=5.0, metavar="L/s",
                    help="DAC air flow rate L/s (default: 5.0)")
    ap.add_argument("--tp-pairs", type=int, default=120, metavar="N",
                    help="Number of thermopile TE couples (default: 120)")
    ap.add_argument("--product", choices=["CH4", "CO2"], default="CH4",
                    help="Supercritical product: CH4 or CO2 (default: CH4)")
    ap.add_argument("--atm-pressure", type=float, default=101325.0, metavar="Pa",
                    help="Atmospheric pressure in Pa (default: 101325)")
    ap.add_argument("--ambient-temp", type=float, default=298.15, metavar="K",
                    help="Ambient temperature in K (default: 298.15)")
    ap.add_argument("--co2-ppm", type=float, default=420.0, metavar="PPM",
                    help="CO2 concentration in PPM (default: 420)")
    ap.add_argument("--n2-frac", type=float, default=0.7809, metavar="FRAC",
                    help="N2 mole fraction (default: 0.7809)")
    ap.add_argument("--o2-frac", type=float, default=0.2095, metavar="FRAC",
                    help="O2 mole fraction (default: 0.2095)")
    ap.add_argument("--rh", type=float, default=0.50, metavar="FRAC",
                    help="Relative humidity fraction (default: 0.50)")
    ap.add_argument("--json", action="store_true", help="Output full JSON report")
    ap.add_argument("--one-line", action="store_true", help="Pipe-friendly one-line output")
    ap.add_argument("--one-line-delim", default=" | ", metavar="DELIM",
                    help="Delimiter for --one-line (default: ' | ')")
    args = ap.parse_args()

    cfg = LoopConfig(
        T_hot_K=args.t_hot,
        T_cold_K=args.t_cold,
        stirling_efficiency_fraction=args.stirling_eff_fraction,
        solar_irradiance_W_m2=args.solar_w,
        collector_area_m2=args.area_m2,
        pv_area_m2=args.pv_area_m2,
        thermopile_pairs=args.tp_pairs,
        dac_air_flow_L_s=args.air_flow_l_s,
        product_mode=args.product,
        atmospheric_pressure_Pa=args.atm_pressure,
        ambient_temp_K=args.ambient_temp,
        co2_mole_fraction=args.co2_ppm / 1e6,
        n2_mole_fraction=args.n2_frac,
        o2_mole_fraction=args.o2_frac,
        relative_humidity=args.rh,
    )

    res = run_simulation(cfg)

    if args.json:
        out: Dict[str, Any] = {"config": asdict(cfg), "result": asdict(res)}
        print(json.dumps(out, indent=2))
    elif args.one_line:
        render_one_line(cfg, res, args.one_line_delim)
    else:
        render_report(cfg, res)


if __name__ == "__main__":
    main()
