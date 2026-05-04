#!/usr/bin/env python3
"""
Pure Software Topology Mapper

Extracts topology from hardware using only software methods:
- Sensor data from sysfs (voltage, current, temperature)
- PCB specifications for wire length calculations
- Voltage measurements for topology inference
- Timing measurements for topology inference
- All available data to reconstruct topology

No external hardware required - pure software approach.
"""

import os
import sys
import time
import json
import math
import subprocess
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# Topology Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SensorReading:
    """Sensor reading from sysfs"""
    timestamp: float
    sensor_type: str
    sensor_name: str
    value: float
    unit: str
    path: str

@dataclass
class WireSegment:
    """Wire segment with physical properties"""
    name: str
    length_mm: float
    resistance_ohm: float
    capacitance_pf: float
    inductance_nh: float
    impedance_ohm: float
    propagation_delay_ps: float

@dataclass
class Component:
    """Component with physical properties"""
    name: str
    type: str
    location: Tuple[float, float]  # (x, y) in mm
    voltage_mv: float
    current_ma: float
    temperature_c: float
    power_mw: float

@dataclass
class TopologyNode:
    """Node in the topology graph"""
    id: str
    component: Component
    connections: List[str]
    voltage_mv: float
    current_ma: float
    timing_ps: float

@dataclass
class TopologyEdge:
    """Edge in the topology graph"""
    source: str
    target: str
    wire_segment: WireSegment
    voltage_drop_mv: float
    current_ma: float
    timing_ps: float
    impedance_ohm: float

@dataclass
class TopologyGraph:
    """Complete topology graph"""
    nodes: Dict[str, TopologyNode]
    edges: List[TopologyEdge]
    wire_segments: Dict[str, WireSegment]
    components: Dict[str, Component]
    sensor_readings: List[SensorReading]
    timestamp: float

# ═══════════════════════════════════════════════════════════════════════════
# PCB Specifications (from substrate_pcb_spec.md)
# ═══════════════════════════════════════════════════════════════════════════

class PCBSpecifications:
    """PCB specifications from substrate_pcb_spec.md"""
    
    # PCB Stackup (4-Layer, 1.6mm)
    STACKUP = {
        "L1": {"name": "Top", "function": "Logic Plane", "copper_um": 35},
        "Dielectric1": {"material": "Rogers 4350B", "thickness_mm": 0.254},
        "L2": {"name": "Inner 1", "function": "GND Plane", "copper_um": 35},
        "Dielectric2": {"material": "Rogers 4350B", "thickness_mm": 0.5},
        "L3": {"name": "Inner 2", "function": "Power / Bus", "copper_um": 35},
        "Dielectric3": {"material": "Rogers 4350B", "thickness_mm": 0.254},
        "L4": {"name": "Bottom", "function": "Safety / Thermal", "copper_um": 35}
    }
    
    # Trace-Logic Netlist
    NETLIST = {
        "NET_ALU_SUM": {
            "type": "Interferometric trace junction",
            "description": "Length-tuned to λ/2 for destructive interference and λ for constructive",
            "function": "Addition/Subtraction"
        },
        "NET_DELAY_LINE": {
            "type": "Looped traces",
            "description": "Acting as synchronous registers",
            "formula": "l = v_p * t_delay"
        },
        "NET_CLK_REF": {
            "type": "Synchronous Clock Wavefront",
            "description": "Used to gate the trace logic"
        },
        "NET_VETO": {
            "type": "Physical isolation gap",
            "description": "If logic states diverge, signal is shunted to GND"
        }
    }
    
    # Component Placement
    COMPONENTS = {
        "U1": {"name": "Central Logic Node", "location": (10.0, 10.0), "function": "Central logic"},
        "U2": {"name": "SRAM", "location": (20.0, 10.0), "function": "High-speed memory"},
        "U5": {"name": "DAC", "location": (15.0, 20.0), "function": "16-bit DAC"},
        "J1": {"name": "USB-C", "location": (5.0, 5.0), "function": "Power delivery"}
    }
    
    # Fabrication Parameters
    FABRICATION = {
        "min_trace_mm": 0.1,
        "min_gap_mm": 0.1,
        "min_hole_mm": 0.2,
        "copper_thickness_um": 35,
        "dielectric": "Rogers 4350B"
    }
    
    # Physical Constants
    COPPER_RESISTIVITY = 0.0172  # Ω·mm²/m at 20°C
    ROGERS_4350B_DIELECTRIC_CONSTANT = 3.48
    SPEED_OF_LIGHT = 299792458  # m/s
    COPPER_TRACE_WIDTH_MM = 0.15  # Typical trace width

# ═══════════════════════════════════════════════════════════════════════════
# EFI Data Extraction
# ═══════════════════════════════════════════════════════════════════════════

class EFIExtractor:
    """Extract EFI information from sysfs"""
    
    def __init__(self):
        self.sysfs_base = Path("/sys/firmware")
        self.efi_data: Dict = {}
    
    def extract_efi_systab(self) -> Dict:
        """Extract EFI system table information"""
        systab_path = self.sysfs_base / "efi" / "systab"
        systab_data = {}
        
        if systab_path.exists():
            try:
                content = systab_path.read_text()
                for line in content.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        systab_data[key.strip()] = value.strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        return systab_data
    
    def extract_efi_vars(self) -> Dict:
        """Extract EFI variables"""
        efivars_path = self.sysfs_base / "efi" / "efivars"
        efivars_data = {}
        
        if efivars_path.exists():
            for var_file in efivars_path.iterdir():
                if var_file.is_file():
                    try:
                        # Read variable GUID and attributes
                        var_name = var_file.name
                        efivars_data[var_name] = {
                            "path": str(var_file),
                            "size": var_file.stat().st_size
                        }
                    except (IOError, OSError):
                        pass
        
        return efivars_data
    
    def extract_acpi_tables(self) -> Dict:
        """Extract ACPI table information"""
        acpi_path = self.sysfs_base / "acpi"
        acpi_data = {}
        
        if acpi_path.exists():
            # Extract ACPI tables
            tables_path = acpi_path / "tables"
            if tables_path.exists():
                for table_file in tables_path.iterdir():
                    if table_file.is_file():
                        try:
                            table_name = table_file.name
                            acpi_data[table_name] = {
                                "path": str(table_file),
                                "size": table_file.stat().st_size
                            }
                        except (IOError, OSError):
                            pass
            
            # Extract DSDT
            dsdt_path = acpi_path / "DSDT"
            if dsdt_path.exists():
                try:
                    acpi_data["DSDT"] = {
                        "path": str(dsdt_path),
                        "size": dsdt_path.stat().st_size
                    }
                except (IOError, OSError):
                    pass
        
        return acpi_data
    
    def extract_dmi_info(self) -> Dict:
        """Extract DMI/SMBIOS information from dmidecode"""
        dmi_data = {}
        
        try:
            result = subprocess.run(
                ["dmidecode", "-t", "system"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                dmi_data["system"] = result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            result = subprocess.run(
                ["dmidecode", "-t", "baseboard"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                dmi_data["baseboard"] = result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return dmi_data
    
    def extract_all_efi(self) -> Dict:
        """Extract all EFI information"""
        self.efi_data = {
            "systab": self.extract_efi_systab(),
            "efivars": self.extract_efi_vars(),
            "acpi": self.extract_acpi_tables(),
            "dmi": self.extract_dmi_info()
        }
        return self.efi_data

# ═══════════════════════════════════════════════════════════════════════════
# PCIe Data Extraction
# ═══════════════════════════════════════════════════════════════════════════

class PCIeExtractor:
    """Extract PCIe information from sysfs"""
    
    def __init__(self):
        self.sysfs_base = Path("/sys/bus/pci")
        self.pcie_data: Dict = {}
    
    def extract_pci_devices(self) -> Dict:
        """Extract all PCI devices"""
        pci_devices = {}
        pci_path = self.sysfs_base / "devices"
        
        if pci_path.exists():
            for device in pci_path.iterdir():
                if device.is_dir():
                    device_id = device.name
                    device_info = self.extract_pci_device_info(device)
                    pci_devices[device_id] = device_info
        
        return pci_devices
    
    def extract_pci_device_info(self, device_path: Path) -> Dict:
        """Extract information for a single PCI device"""
        device_info = {"path": str(device_path)}
        
        # Extract vendor and device IDs
        vendor_file = device_path / "vendor"
        device_file = device_path / "device"
        
        if vendor_file.exists():
            try:
                device_info["vendor"] = vendor_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        if device_file.exists():
            try:
                device_info["device"] = device_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract class information
        class_file = device_path / "class"
        if class_file.exists():
            try:
                device_info["class"] = class_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract PCIe link information
        link_info = self.extract_pcie_link_info(device_path)
        if link_info:
            device_info["link"] = link_info
        
        # Extract power information
        power_info = self.extract_pcie_power_info(device_path)
        if power_info:
            device_info["power"] = power_info
        
        # Extract driver information
        driver_path = device_path / "driver"
        if driver_path.exists() and driver_path.is_symlink():
            try:
                device_info["driver"] = driver_path.resolve().name
            except (IOError, OSError):
                pass
        
        return device_info
    
    def extract_pcie_link_info(self, device_path: Path) -> Optional[Dict]:
        """Extract PCIe link information"""
        link_info = {}
        
        # Link width
        link_width_file = device_path / "max_link_width"
        if link_width_file.exists():
            try:
                link_info["max_link_width"] = link_width_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        current_link_width_file = device_path / "current_link_width"
        if current_link_width_file.exists():
            try:
                link_info["current_link_width"] = current_link_width_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Link speed
        link_speed_file = device_path / "max_link_speed"
        if link_speed_file.exists():
            try:
                link_info["max_link_speed"] = link_speed_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        current_link_speed_file = device_path / "current_link_speed"
        if current_link_speed_file.exists():
            try:
                link_info["current_link_speed"] = current_link_speed_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        return link_info if link_info else None
    
    def extract_pcie_power_info(self, device_path: Path) -> Optional[Dict]:
        """Extract PCIe power information"""
        power_info = {}
        
        # Power limit
        power_limit_file = device_path / "power_limit"
        if power_limit_file.exists():
            try:
                power_info["power_limit"] = power_limit_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Power state
        power_state_file = device_path / "power_state"
        if power_state_file.exists():
            try:
                power_info["power_state"] = power_state_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        return power_info if power_info else None
    
    def extract_lspci_info(self) -> Dict:
        """Extract PCI information using lspci command"""
        lspci_data = {}
        
        try:
            result = subprocess.run(
                ["lspci", "-v"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lspci_data["verbose"] = result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            result = subprocess.run(
                ["lspci", "-nn"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lspci_data["numeric"] = result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return lspci_data
    
    def extract_all_pcie(self) -> Dict:
        """Extract all PCIe information"""
        self.pcie_data = {
            "devices": self.extract_pci_devices(),
            "lspci": self.extract_lspci_info()
        }
        return self.pcie_data

# ═══════════════════════════════════════════════════════════════════════════
# Power Supply Data Extraction
# ═══════════════════════════════════════════════════════════════════════════

class PowerSupplyExtractor:
    """Extract power supply and power flow information from sysfs"""
    
    def __init__(self):
        self.sysfs_base = Path("/sys/class/power_supply")
        self.power_supply_data: Dict = {}
    
    def extract_power_supplies(self) -> Dict:
        """Extract all power supply information"""
        power_supplies = {}
        
        if self.sysfs_base.exists():
            for supply in self.sysfs_base.iterdir():
                if supply.is_dir():
                    supply_name = supply.name
                    supply_info = self.extract_power_supply_info(supply)
                    power_supplies[supply_name] = supply_info
        
        return power_supplies
    
    def extract_power_supply_info(self, supply_path: Path) -> Dict:
        """Extract information for a single power supply"""
        supply_info = {"path": str(supply_path)}
        
        # Extract power supply type
        type_file = supply_path / "type"
        if type_file.exists():
            try:
                supply_info["type"] = type_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract voltage information
        voltage_now_file = supply_path / "voltage_now"
        if voltage_now_file.exists():
            try:
                voltage_uv = int(voltage_now_file.read_text().strip())
                supply_info["voltage_now_mv"] = voltage_uv / 1000.0
            except (ValueError, IOError):
                pass
        
        voltage_min_file = supply_path / "voltage_min_design"
        if voltage_min_file.exists():
            try:
                voltage_uv = int(voltage_min_file.read_text().strip())
                supply_info["voltage_min_mv"] = voltage_uv / 1000.0
            except (ValueError, IOError):
                pass
        
        voltage_max_file = supply_path / "voltage_max_design"
        if voltage_max_file.exists():
            try:
                voltage_uv = int(voltage_max_file.read_text().strip())
                supply_info["voltage_max_mv"] = voltage_uv / 1000.0
            except (ValueError, IOError):
                pass
        
        # Extract current information
        current_now_file = supply_path / "current_now"
        if current_now_file.exists():
            try:
                current_ua = int(current_now_file.read_text().strip())
                supply_info["current_now_ma"] = current_ua / 1000.0
            except (ValueError, IOError):
                pass
        
        # Extract power information
        power_now_file = supply_path / "power_now"
        if power_now_file.exists():
            try:
                power_uw = int(power_now_file.read_text().strip())
                supply_info["power_now_mw"] = power_uw / 1000.0
            except (ValueError, IOError):
                pass
        
        # Extract capacity information (for batteries)
        capacity_file = supply_path / "capacity"
        if capacity_file.exists():
            try:
                supply_info["capacity_percent"] = int(capacity_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        capacity_level_file = supply_path / "capacity_level"
        if capacity_level_file.exists():
            try:
                supply_info["capacity_level"] = capacity_level_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract status
        status_file = supply_path / "status"
        if status_file.exists():
            try:
                supply_info["status"] = status_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract health information
        health_file = supply_path / "health"
        if health_file.exists():
            try:
                supply_info["health"] = health_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract technology (for batteries)
        technology_file = supply_path / "technology"
        if technology_file.exists():
            try:
                supply_info["technology"] = technology_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract online status
        online_file = supply_path / "online"
        if online_file.exists():
            try:
                supply_info["online"] = online_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract presence status
        present_file = supply_path / "present"
        if present_file.exists():
            try:
                supply_info["present"] = present_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        return supply_info
    
    def extract_power_flow(self) -> Dict:
        """Extract power flow information"""
        power_flow = {}
        
        # Extract from powercap if available
        powercap_path = Path("/sys/class/powercap")
        if powercap_path.exists():
            for domain in powercap_path.iterdir():
                if domain.is_dir():
                    domain_name = domain.name
                    domain_info = {}
                    
                    # Extract energy
                    energy_file = domain / "energy_uj"
                    if energy_file.exists():
                        try:
                            energy_uj = int(energy_file.read_text().strip())
                            domain_info["energy_uj"] = energy_uj
                            domain_info["energy_j"] = energy_uj / 1000000.0
                        except (ValueError, IOError):
                            pass
                    
                    # Extract max energy range
                    max_energy_file = domain / "max_energy_range_uj"
                    if max_energy_file.exists():
                        try:
                            max_energy_uj = int(max_energy_file.read_text().strip())
                            domain_info["max_energy_range_uj"] = max_energy_uj
                            domain_info["max_energy_range_j"] = max_energy_uj / 1000000.0
                        except (ValueError, IOError):
                            pass
                    
                    # Extract power limit
                    power_limit_file = domain / "constraint_0_power_limit_uw"
                    if power_limit_file.exists():
                        try:
                            power_limit_uw = int(power_limit_file.read_text().strip())
                            domain_info["power_limit_uw"] = power_limit_uw
                            domain_info["power_limit_mw"] = power_limit_uw / 1000.0
                        except (ValueError, IOError):
                            pass
                    
                    if domain_info:
                        power_flow[domain_name] = domain_info
        
        return power_flow
    
    def extract_all_power_supply(self) -> Dict:
        """Extract all power supply information"""
        self.power_supply_data = {
            "power_supplies": self.extract_power_supplies(),
            "power_flow": self.extract_power_flow()
        }
        return self.power_supply_data

# ═══════════════════════════════════════════════════════════════════════════
# CPU Topology Data Extraction
# ═══════════════════════════════════════════════════════════════════════════

class CPUTopologyExtractor:
    """Extract CPU topology, cache, voltage, and wire length information"""
    
    def __init__(self):
        self.sysfs_base = Path("/sys/devices/system/cpu")
        self.cpu_data: Dict = {}
    
    def extract_cpu_topology(self) -> Dict:
        """Extract CPU topology information"""
        cpu_topology = {}
        
        if self.sysfs_base.exists():
            for cpu in self.sysfs_base.iterdir():
                if cpu.is_dir() and cpu.name.startswith("cpu"):
                    cpu_id = cpu.name
                    cpu_info = self.extract_cpu_info(cpu)
                    cpu_topology[cpu_id] = cpu_info
        
        return cpu_topology
    
    def extract_cpu_info(self, cpu_path: Path) -> Dict:
        """Extract information for a single CPU"""
        cpu_info = {"path": str(cpu_path)}
        
        # Extract core ID
        core_id_file = cpu_path / "topology" / "core_id"
        if core_id_file.exists():
            try:
                cpu_info["core_id"] = int(core_id_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        # Extract physical package ID
        physical_package_id_file = cpu_path / "topology" / "physical_package_id"
        if physical_package_id_file.exists():
            try:
                cpu_info["physical_package_id"] = int(physical_package_id_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        # Extract thread siblings
        thread_siblings_file = cpu_path / "topology" / "thread_siblings_list"
        if thread_siblings_file.exists():
            try:
                cpu_info["thread_siblings"] = thread_siblings_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract core siblings
        core_siblings_file = cpu_path / "topology" / "core_siblings_list"
        if core_siblings_file.exists():
            try:
                cpu_info["core_siblings"] = core_siblings_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract CPU frequency
        cpuinfo_max_freq_file = cpu_path / "cpufreq" / "cpuinfo_max_freq"
        if cpuinfo_max_freq_file.exists():
            try:
                cpu_info["max_freq_khz"] = int(cpuinfo_max_freq_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        cpuinfo_min_freq_file = cpu_path / "cpufreq" / "cpuinfo_min_freq"
        if cpuinfo_min_freq_file.exists():
            try:
                cpu_info["min_freq_khz"] = int(cpuinfo_min_freq_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        scaling_cur_freq_file = cpu_path / "cpufreq" / "scaling_cur_freq"
        if scaling_cur_freq_file.exists():
            try:
                cpu_info["cur_freq_khz"] = int(scaling_cur_freq_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        # Extract CPU online status
        online_file = cpu_path / "online"
        if online_file.exists():
            try:
                cpu_info["online"] = online_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        return cpu_info
    
    def extract_cache_topology(self) -> Dict:
        """Extract cache topology information"""
        cache_topology = {}
        
        cache_path = self.sysfs_base / "cpu0" / "cache"
        if not cache_path.exists():
            # Try alternative path
            cache_path = Path("/sys/devices/system/cpu/cpu0/cache")
        
        if cache_path.exists():
            for cache_level in cache_path.iterdir():
                if cache_level.is_dir() and cache_level.name.startswith("index"):
                    cache_id = cache_level.name
                    cache_info = self.extract_cache_info(cache_level)
                    cache_topology[cache_id] = cache_info
        
        return cache_topology
    
    def extract_cache_info(self, cache_path: Path) -> Dict:
        """Extract information for a single cache"""
        cache_info = {"path": str(cache_path)}
        
        # Extract cache level
        level_file = cache_path / "level"
        if level_file.exists():
            try:
                cache_info["level"] = int(level_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        # Extract cache type
        type_file = cache_path / "type"
        if type_file.exists():
            try:
                cache_info["type"] = type_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract cache size
        size_file = cache_path / "size"
        if size_file.exists():
            try:
                cache_info["size"] = size_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract cache line size
        coherency_line_size_file = cache_path / "coherency_line_size"
        if coherency_line_size_file.exists():
            try:
                cache_info["coherency_line_size"] = int(coherency_line_size_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        # Extract number of sets
        number_of_sets_file = cache_path / "number_of_sets"
        if number_of_sets_file.exists():
            try:
                cache_info["number_of_sets"] = int(number_of_sets_file.read_text().strip())
            except (ValueError, IOError):
                pass
        
        # Extract shared CPU map
        shared_cpu_map_file = cache_path / "shared_cpu_map"
        if shared_cpu_map_file.exists():
            try:
                cache_info["shared_cpu_map"] = shared_cpu_map_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        # Extract shared CPU list
        shared_cpu_list_file = cache_path / "shared_cpu_list"
        if shared_cpu_list_file.exists():
            try:
                cache_info["shared_cpu_list"] = shared_cpu_list_file.read_text().strip()
            except (IOError, UnicodeDecodeError):
                pass
        
        return cache_info
    
    def extract_cpu_voltage(self) -> Dict:
        """Extract CPU voltage information"""
        cpu_voltage = {}
        
        # Extract from RAPL if available
        rapl_path = Path("/sys/class/powercap/intel-rapl")
        if rapl_path.exists():
            for domain in rapl_path.iterdir():
                if domain.is_dir() and "intel-rapl" in domain.name:
                    voltage_file = domain / "voltage_now"
                    if voltage_file.exists():
                        try:
                            voltage_uv = int(voltage_file.read_text().strip())
                            cpu_voltage[domain.name] = {
                                "voltage_now_uv": voltage_uv,
                                "voltage_now_mv": voltage_uv / 1000.0
                            }
                        except (ValueError, IOError):
                            pass
        
        return cpu_voltage
    
    def calculate_cpu_wire_lengths(self) -> Dict:
        """Calculate CPU wire lengths based on die layout"""
        wire_lengths = {}
        
        # Typical CPU die wire lengths (approximate based on process node)
        # 7nm process: ~0.007µm per gate, typical wire length between cores ~1-2mm
        # 14nm process: ~0.014µm per gate, typical wire length between cores ~2-4mm
        # We'll use conservative estimates
        
        wire_lengths["core_to_core"] = 2.0  # mm (typical distance between cores)
        wire_lengths["l1_to_l2"] = 0.5  # mm (L1 to L2 cache distance)
        wire_lengths["l2_to_l3"] = 1.0  # mm (L2 to L3 cache distance)
        wire_lengths["l3_to_mem"] = 5.0  # mm (L3 to memory controller distance)
        wire_lengths["core_to_l3"] = 1.5  # mm (core to L3 cache distance)
        
        return wire_lengths
    
    def extract_lscpu_info(self) -> Dict:
        """Extract CPU information using lscpu command"""
        lscpu_data = {}
        
        try:
            result = subprocess.run(
                ["lscpu", "-J"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                try:
                    lscpu_data["json"] = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            result = subprocess.run(
                ["lscpu"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lscpu_data["text"] = result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return lscpu_data
    
    def extract_all_cpu_topology(self) -> Dict:
        """Extract all CPU topology information"""
        self.cpu_data = {
            "cpu_topology": self.extract_cpu_topology(),
            "cache_topology": self.extract_cache_topology(),
            "cpu_voltage": self.extract_cpu_voltage(),
            "wire_lengths": self.calculate_cpu_wire_lengths(),
            "lscpu": self.extract_lscpu_info()
        }
        return self.cpu_data

# ═══════════════════════════════════════════════════════════════════════════
# Sensor Data Extraction
# ═══════════════════════════════════════════════════════════════════════════

class SensorExtractor:
    """Extract sensor data from sysfs"""
    
    def __init__(self):
        self.sysfs_base = Path("/sys")
        self.sensor_readings: List[SensorReading] = []
    
    def extract_voltage_sensors(self) -> List[SensorReading]:
        """Extract voltage sensors from hwmon"""
        readings = []
        hwmon_path = self.sysfs_base / "class" / "hwmon"
        
        if hwmon_path.exists():
            for hwmon in hwmon_path.iterdir():
                if hwmon.is_dir():
                    for sensor in hwmon.iterdir():
                        if sensor.is_file() and "in" in sensor.name and "input" in sensor.name:
                            try:
                                value_mv = float(sensor.read_text().strip())
                                readings.append(SensorReading(
                                    timestamp=time.time(),
                                    sensor_type="voltage",
                                    sensor_name=sensor.name,
                                    value=value_mv,
                                    unit="mV",
                                    path=str(sensor)
                                ))
                            except (ValueError, IOError):
                                pass
        
        return readings
    
    def extract_current_sensors(self) -> List[SensorReading]:
        """Extract current sensors from hwmon"""
        readings = []
        hwmon_path = self.sysfs_base / "class" / "hwmon"
        
        if hwmon_path.exists():
            for hwmon in hwmon_path.iterdir():
                if hwmon.is_dir():
                    for sensor in hwmon.iterdir():
                        if sensor.is_file() and "curr" in sensor.name and "input" in sensor.name:
                            try:
                                value_ma = float(sensor.read_text().strip())
                                readings.append(SensorReading(
                                    timestamp=time.time(),
                                    sensor_type="current",
                                    sensor_name=sensor.name,
                                    value=value_ma,
                                    unit="mA",
                                    path=str(sensor)
                                ))
                            except (ValueError, IOError):
                                pass
        
        return readings
    
    def extract_temperature_sensors(self) -> List[SensorReading]:
        """Extract temperature sensors from hwmon"""
        readings = []
        hwmon_path = self.sysfs_base / "class" / "hwmon"
        
        if hwmon_path.exists():
            for hwmon in hwmon_path.iterdir():
                if hwmon.is_dir():
                    for sensor in hwmon.iterdir():
                        if sensor.is_file() and "temp" in sensor.name and "input" in sensor.name:
                            try:
                                value_mc = float(sensor.read_text().strip())
                                value_c = value_mc / 1000.0  # Convert m°C to °C
                                readings.append(SensorReading(
                                    timestamp=time.time(),
                                    sensor_type="temperature",
                                    sensor_name=sensor.name,
                                    value=value_c,
                                    unit="°C",
                                    path=str(sensor)
                                ))
                            except (ValueError, IOError):
                                pass
        
        return readings
    
    def extract_power_supply(self) -> List[SensorReading]:
        """Extract power supply sensors"""
        readings = []
        power_supply_path = self.sysfs_base / "class" / "power_supply"
        
        if power_supply_path.exists():
            for supply in power_supply_path.iterdir():
                if supply.is_dir():
                    voltage_file = supply / "voltage_now"
                    current_file = supply / "current_now"
                    
                    if voltage_file.exists():
                        try:
                            voltage_uv = int(voltage_file.read_text().strip())
                            voltage_mv = voltage_uv / 1000.0
                            readings.append(SensorReading(
                                timestamp=time.time(),
                                sensor_type="voltage",
                                sensor_name=f"{supply.name}_voltage",
                                value=voltage_mv,
                                unit="mV",
                                path=str(voltage_file)
                            ))
                        except (ValueError, IOError):
                            pass
                    
                    if current_file.exists():
                        try:
                            current_ua = int(current_file.read_text().strip())
                            current_ma = current_ua / 1000.0
                            readings.append(SensorReading(
                                timestamp=time.time(),
                                sensor_type="current",
                                sensor_name=f"{supply.name}_current",
                                value=current_ma,
                                unit="mA",
                                path=str(current_file)
                            ))
                        except (ValueError, IOError):
                            pass
        
        return readings
    
    def extract_rapl_energy(self) -> List[SensorReading]:
        """Extract RAPL energy measurements"""
        readings = []
        powercap_path = self.sysfs_base / "class" / "powercap"
        
        if powercap_path.exists():
            for domain in powercap_path.iterdir():
                if domain.is_dir():
                    energy_file = domain / "energy_uj"
                    if energy_file.exists():
                        try:
                            energy_uj = int(energy_file.read_text().strip())
                            energy_j = energy_uj / 1000000.0
                            readings.append(SensorReading(
                                timestamp=time.time(),
                                sensor_type="energy",
                                sensor_name=f"{domain.name}_energy",
                                value=energy_j,
                                unit="J",
                                path=str(energy_file)
                            ))
                        except (ValueError, IOError):
                            pass
        
        return readings
    
    def extract_all_sensors(self) -> List[SensorReading]:
        """Extract all sensor readings"""
        self.sensor_readings = []
        self.sensor_readings.extend(self.extract_voltage_sensors())
        self.sensor_readings.extend(self.extract_current_sensors())
        self.sensor_readings.extend(self.extract_temperature_sensors())
        self.sensor_readings.extend(self.extract_power_supply())
        self.sensor_readings.extend(self.extract_rapl_energy())
        return self.sensor_readings

# ═══════════════════════════════════════════════════════════════════════════
# Wire Length Calculations
# ═══════════════════════════════════════════════════════════════════════════

class WireLengthCalculator:
    """Calculate wire properties from PCB specifications"""
    
    def __init__(self):
        self.pcb = PCBSpecifications()
    
    def calculate_resistance(self, length_mm: float, width_mm: float = 0.15) -> float:
        """Calculate resistance of a copper trace"""
        # R = ρ * L / (W * t)
        # ρ = 0.0172 Ω·mm²/m (copper resistivity)
        # L = length in mm
        # W = width in mm
        # t = thickness in mm (35μm = 0.035mm)
        thickness_mm = self.pcb.COPPER_TRACE_WIDTH_MM  # 35μm = 0.035mm
        resistance = (self.pcb.COPPER_RESISTIVITY * length_mm) / (width_mm * thickness_mm)
        return resistance
    
    def calculate_capacitance(self, length_mm: float) -> float:
        """Calculate capacitance of a trace over ground plane"""
        # C = ε_r * ε_0 * (W * L) / d
        # ε_r = 3.48 (Rogers 4350B)
        # ε_0 = 8.854e-12 F/m
        # W = width in m
        # L = length in m
        # d = dielectric thickness in m (0.254mm = 0.000254m)
        width_m = self.pcb.COPPER_TRACE_WIDTH_MM / 1000.0
        length_m = length_mm / 1000.0
        dielectric_thickness_m = 0.000254  # 0.254mm
        
        capacitance = (self.pcb.ROGERS_4350B_DIELECTRIC_CONSTANT * 8.854e-12 * 
                      width_m * length_m) / dielectric_thickness_m
        return capacitance * 1e12  # Convert to pF
    
    def calculate_inductance(self, length_mm: float) -> float:
        """Calculate inductance of a trace"""
        # L = 2 * l * (ln(2*l/W) - 1) for microstrip
        # l = length in m
        # W = width in m
        length_m = length_mm / 1000.0
        width_m = self.pcb.COPPER_TRACE_WIDTH_MM / 1000.0
        
        inductance = 2 * length_m * (math.log(2 * length_m / width_m) - 1)
        return inductance * 1e9  # Convert to nH
    
    def calculate_impedance(self, resistance: float, capacitance_pf: float, 
                            inductance_nh: float, frequency_hz: float = 1e9) -> float:
        """Calculate characteristic impedance"""
        # Z = sqrt(R + jωL) / (G + jωC)
        # Simplified: Z = sqrt(L/C) at high frequency
        capacitance_f = capacitance_pf * 1e-12
        inductance_h = inductance_nh * 1e-9
        
        if frequency_hz > 1e6:
            impedance = math.sqrt(inductance_h / capacitance_f)
        else:
            impedance = resistance
        
        return impedance
    
    def calculate_propagation_delay(self, length_mm: float) -> float:
        """Calculate propagation delay through trace"""
        # t = l / v_p
        # v_p = c / sqrt(ε_r) for microstrip
        # l = length in m
        # c = speed of light
        # ε_r = dielectric constant
        length_m = length_mm / 1000.0
        velocity = self.pcb.SPEED_OF_LIGHT / math.sqrt(self.pcb.ROGERS_4350B_DIELECTRIC_CONSTANT)
        delay_s = length_m / velocity
        return delay_s * 1e12  # Convert to ps
    
    def create_wire_segment(self, name: str, length_mm: float) -> WireSegment:
        """Create a wire segment with all calculated properties"""
        resistance = self.calculate_resistance(length_mm)
        capacitance = self.calculate_capacitance(length_mm)
        inductance = self.calculate_inductance(length_mm)
        impedance = self.calculate_impedance(resistance, capacitance, inductance)
        delay = self.calculate_propagation_delay(length_mm)
        
        return WireSegment(
            name=name,
            length_mm=length_mm,
            resistance_ohm=resistance,
            capacitance_pf=capacitance,
            inductance_nh=inductance,
            impedance_ohm=impedance,
            propagation_delay_ps=delay
        )
    
    def calculate_wire_length_from_components(self, component1: str, component2: str) -> float:
        """Calculate wire length between two components based on PCB placement"""
        loc1 = self.pcb.COMPONENTS.get(component1)
        loc2 = self.pcb.COMPONENTS.get(component2)
        
        if loc1 and loc2:
            x1, y1 = loc1["location"]
            x2, y2 = loc2["location"]
            length_mm = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            return length_mm
        
        return 10.0  # Default length if components not found

# ═══════════════════════════════════════════════════════════════════════════
# Voltage-Based Topology Inference
# ═══════════════════════════════════════════════════════════════════════════

class VoltageTopologyInference:
    """Infer topology from voltage measurements"""
    
    def __init__(self, wire_calculator: WireLengthCalculator):
        self.wire_calc = wire_calculator
    
    def calculate_voltage_drop(self, current_ma: float, resistance_ohm: float) -> float:
        """Calculate voltage drop across a wire segment"""
        # V = I * R
        current_a = current_ma / 1000.0
        voltage_drop_v = current_a * resistance_ohm
        return voltage_drop_v * 1000  # Convert to mV
    
    def infer_connection_from_voltage(self, voltage_mv: float, current_ma: float) -> bool:
        """Infer if two components are connected based on voltage/current"""
        # If voltage is present and current is flowing, likely connected
        if voltage_mv > 100 and current_ma > 1.0:
            return True
        return False
    
    def infer_wire_length_from_voltage_drop(self, voltage_drop_mv: float, 
                                           current_ma: float) -> float:
        """Infer wire length from voltage drop"""
        # V = I * R = I * (ρ * L / (W * t))
        # L = V * (W * t) / (I * ρ)
        if current_ma == 0:
            return 0.0
        
        voltage_drop_v = voltage_drop_mv / 1000.0
        current_a = current_ma / 1000.0
        width_mm = PCBSpecifications.COPPER_TRACE_WIDTH_MM
        thickness_mm = 0.035  # 35μm
        
        length_mm = (voltage_drop_v * width_mm * thickness_mm) / (current_a * PCBSpecifications.COPPER_RESISTIVITY)
        return length_mm

# ═══════════════════════════════════════════════════════════════════════════
# Timing-Based Topology Inference
# ═══════════════════════════════════════════════════════════════════════════

class TimingTopologyInference:
    """Infer topology from timing measurements"""
    
    def __init__(self, wire_calculator: WireLengthCalculator):
        self.wire_calc = wire_calculator
    
    def infer_wire_length_from_timing(self, timing_ps: float) -> float:
        """Infer wire length from timing delay"""
        # t = l / v_p
        # l = t * v_p
        # v_p = c / sqrt(ε_r)
        timing_s = timing_ps / 1e12
        velocity = PCBSpecifications.SPEED_OF_LIGHT / math.sqrt(PCBSpecifications.ROGERS_4350B_DIELECTRIC_CONSTANT)
        length_m = timing_s * velocity
        return length_m * 1000  # Convert to mm
    
    def calculate_clock_skew(self, timing_ps: float, frequency_hz: float) -> float:
        """Calculate clock skew in degrees"""
        # skew = (t / T) * 360
        period_s = 1.0 / frequency_hz
        timing_s = timing_ps / 1e12
        skew_deg = (timing_s / period_s) * 360
        return skew_deg
    
    def infer_synchronous_connection(self, timing_ps: float, clock_period_ps: float) -> bool:
        """Infer if components are synchronously connected"""
        # If timing is close to clock period or multiple, likely synchronous
        if abs(timing_ps - clock_period_ps) < clock_period_ps * 0.1:
            return True
        if abs(timing_ps - 2 * clock_period_ps) < clock_period_ps * 0.1:
            return True
        return False

# ═══════════════════════════════════════════════════════════════════════════
# Complete Topology Mapper
# ═══════════════════════════════════════════════════════════════════════════

class PureSoftwareTopologyMapper:
    """Complete pure software topology mapper"""
    
    def __init__(self):
        self.sensor_extractor = SensorExtractor()
        self.efi_extractor = EFIExtractor()
        self.pcie_extractor = PCIeExtractor()
        self.power_supply_extractor = PowerSupplyExtractor()
        self.cpu_topology_extractor = CPUTopologyExtractor()
        self.wire_calculator = WireLengthCalculator()
        self.voltage_inference = VoltageTopologyInference(self.wire_calculator)
        self.timing_inference = TimingTopologyInference(self.wire_calculator)
        self.topology_graph = TopologyGraph(
            nodes={},
            edges=[],
            wire_segments={},
            components={},
            sensor_readings=[],
            timestamp=time.time()
        )
        self.efi_data = {}
        self.pcie_data = {}
        self.power_supply_data = {}
        self.cpu_data = {}
    
    def extract_sensor_data(self):
        """Extract all sensor data"""
        print("Extracting sensor data from sysfs...")
        self.topology_graph.sensor_readings = self.sensor_extractor.extract_all_sensors()
        print(f"  Extracted {len(self.topology_graph.sensor_readings)} sensor readings")
        
        # Print summary
        voltage_count = sum(1 for r in self.topology_graph.sensor_readings if r.sensor_type == "voltage")
        current_count = sum(1 for r in self.topology_graph.sensor_readings if r.sensor_type == "current")
        temp_count = sum(1 for r in self.topology_graph.sensor_readings if r.sensor_type == "temperature")
        energy_count = sum(1 for r in self.topology_graph.sensor_readings if r.sensor_type == "energy")
        
        print(f"  Voltage sensors: {voltage_count}")
        print(f"  Current sensors: {current_count}")
        print(f"  Temperature sensors: {temp_count}")
        print(f"  Energy sensors: {energy_count}")
    
    def extract_efi_data(self):
        """Extract all EFI information"""
        print("Extracting EFI information from sysfs...")
        self.efi_data = self.efi_extractor.extract_all_efi()
        
        # Print summary
        systab_count = len(self.efi_data.get("systab", {}))
        efivars_count = len(self.efi_data.get("efivars", {}))
        acpi_count = len(self.efi_data.get("acpi", {}))
        dmi_count = len(self.efi_data.get("dmi", {}))
        
        print(f"  EFI systab entries: {systab_count}")
        print(f"  EFI variables: {efivars_count}")
        print(f"  ACPI tables: {acpi_count}")
        print(f"  DMI sections: {dmi_count}")
        
        # Print systab details
        if self.efi_data.get("systab"):
            print("  EFI System Table:")
            for key, value in self.efi_data["systab"].items():
                print(f"    {key}={value}")
    
    def extract_pcie_data(self):
        """Extract all PCIe information"""
        print("Extracting PCIe information from sysfs...")
        self.pcie_data = self.pcie_extractor.extract_all_pcie()
        
        # Print summary
        pci_devices = self.pcie_data.get("devices", {})
        lspci_data = self.pcie_data.get("lspci", {})
        
        print(f"  PCI devices: {len(pci_devices)}")
        print(f"  lspci verbose: {'available' if 'verbose' in lspci_data else 'not available'}")
        print(f"  lspci numeric: {'available' if 'numeric' in lspci_data else 'not available'}")
        
        # Print device summary
        if pci_devices:
            print("  PCI Devices:")
            for device_id, device_info in pci_devices.items():
                vendor = device_info.get("vendor", "unknown")
                device = device_info.get("device", "unknown")
                driver = device_info.get("driver", "no driver")
                link = device_info.get("link", {})
                print(f"    {device_id}: {vendor} {device} (driver: {driver})")
                if link:
                    width = link.get("current_link_width", "unknown")
                    speed = link.get("current_link_speed", "unknown")
                    print(f"      Link: {width} @ {speed}")
    
    def extract_power_supply_data(self):
        """Extract all power supply information"""
        print("Extracting power supply information from sysfs...")
        self.power_supply_data = self.power_supply_extractor.extract_all_power_supply()
        
        # Print summary
        power_supplies = self.power_supply_data.get("power_supplies", {})
        power_flow = self.power_supply_data.get("power_flow", {})
        
        print(f"  Power supplies: {len(power_supplies)}")
        print(f"  Power flow domains: {len(power_flow)}")
        
        # Print power supply summary
        if power_supplies:
            print("  Power Supplies:")
            for supply_name, supply_info in power_supplies.items():
                supply_type = supply_info.get("type", "unknown")
                voltage = supply_info.get("voltage_now_mv", 0.0)
                current = supply_info.get("current_now_ma", 0.0)
                power = supply_info.get("power_now_mw", 0.0)
                status = supply_info.get("status", "unknown")
                print(f"    {supply_name}: {supply_type}, {voltage:.1f}mV, {current:.1f}mA, {power:.3f}mW, status={status}")
                
                # Print battery-specific info
                if supply_type == "Battery":
                    capacity = supply_info.get("capacity_percent", "N/A")
                    health = supply_info.get("health", "unknown")
                    print(f"      Capacity: {capacity}%, Health: {health}")
        
        # Print power flow summary
        if power_flow:
            print("  Power Flow:")
            for domain_name, domain_info in power_flow.items():
                energy_j = domain_info.get("energy_j", 0.0)
                power_limit_mw = domain_info.get("power_limit_mw", 0.0)
                print(f"    {domain_name}: {energy_j:.6f}J, limit: {power_limit_mw:.3f}mW")
    
    def extract_cpu_topology_data(self):
        """Extract all CPU topology information"""
        print("Extracting CPU topology information from sysfs...")
        self.cpu_data = self.cpu_topology_extractor.extract_all_cpu_topology()
        
        # Print summary
        cpu_topology = self.cpu_data.get("cpu_topology", {})
        cache_topology = self.cpu_data.get("cache_topology", {})
        cpu_voltage = self.cpu_data.get("cpu_voltage", {})
        wire_lengths = self.cpu_data.get("wire_lengths", {})
        lscpu_data = self.cpu_data.get("lscpu", {})
        
        print(f"  CPUs: {len(cpu_topology)}")
        print(f"  Cache levels: {len(cache_topology)}")
        print(f"  CPU voltage domains: {len(cpu_voltage)}")
        print(f"  Wire length estimates: {len(wire_lengths)}")
        print(f"  lscpu available: {'yes' if lscpu_data else 'no'}")
        
        # Print CPU topology summary
        if cpu_topology:
            print("  CPU Topology:")
            for cpu_id, cpu_info in cpu_topology.items():
                core_id = cpu_info.get("core_id", "unknown")
                package_id = cpu_info.get("physical_package_id", "unknown")
                max_freq = cpu_info.get("max_freq_khz", 0)
                cur_freq = cpu_info.get("cur_freq_khz", 0)
                online = cpu_info.get("online", "unknown")
                print(f"    {cpu_id}: core={core_id}, package={package_id}, freq={cur_freq}kHz/{max_freq}kHz, online={online}")
        
        # Print cache topology summary
        if cache_topology:
            print("  Cache Topology:")
            for cache_id, cache_info in cache_topology.items():
                level = cache_info.get("level", "unknown")
                cache_type = cache_info.get("type", "unknown")
                size = cache_info.get("size", "unknown")
                shared = cache_info.get("shared_cpu_list", "unknown")
                print(f"    {cache_id}: L{level} {cache_type}, size={size}, shared={shared}")
        
        # Print wire length summary
        if wire_lengths:
            print("  CPU Wire Lengths:")
            for wire_name, length_mm in wire_lengths.items():
                print(f"    {wire_name}: {length_mm}mm")
    
    def create_wire_segments_from_pcb(self):
        """Create wire segments from PCB specifications"""
        print("Creating wire segments from PCB specifications...")
        
        # Calculate wire lengths between components
        components = list(PCBSpecifications.COMPONENTS.keys())
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                length_mm = self.wire_calculator.calculate_wire_length_from_components(comp1, comp2)
                wire_name = f"WIRE_{comp1}_{comp2}"
                wire_segment = self.wire_calculator.create_wire_segment(wire_name, length_mm)
                self.topology_graph.wire_segments[wire_name] = wire_segment
                print(f"  {wire_name}: {length_mm:.2f}mm")
        
        # Create netlist wire segments
        for net_name, net_info in PCBSpecifications.NETLIST.items():
            # Default length for netlist segments (can be refined)
            wire_segment = self.wire_calculator.create_wire_segment(net_name, 15.0)
            self.topology_graph.wire_segments[net_name] = wire_segment
            print(f"  {net_name}: 15.00mm (netlist)")
    
    def create_components_from_sensors(self):
        """Create components from sensor readings"""
        print("Creating components from sensor readings...")
        
        # Group sensor readings by component
        component_sensors = {}
        for reading in self.topology_graph.sensor_readings:
            # Extract component name from sensor name
            component_name = reading.sensor_name.split("_")[0] if "_" in reading.sensor_name else reading.sensor_name
            if component_name not in component_sensors:
                component_sensors[component_name] = []
            component_sensors[component_name].append(reading)
        
        # Create components
        for comp_name, readings in component_sensors.items():
            voltage_mv = 0.0
            current_ma = 0.0
            temperature_c = 0.0
            
            for reading in readings:
                if reading.sensor_type == "voltage":
                    voltage_mv = reading.value
                elif reading.sensor_type == "current":
                    current_ma = reading.value
                elif reading.sensor_type == "temperature":
                    temperature_c = reading.value
            
            power_mw = (voltage_mv * current_ma) / 1000.0
            
            # Get component location from PCB specs
            pcb_comp = PCBSpecifications.COMPONENTS.get(comp_name)
            location = pcb_comp["location"] if pcb_comp else (0.0, 0.0)
            
            component = Component(
                name=comp_name,
                type="sensor",
                location=location,
                voltage_mv=voltage_mv,
                current_ma=current_ma,
                temperature_c=temperature_c,
                power_mw=power_mw
            )
            
            self.topology_graph.components[comp_name] = component
            print(f"  {comp_name}: {voltage_mv:.1f}mV, {current_ma:.1f}mA, {temperature_c:.1f}°C, {power_mw:.3f}mW")
    
    def infer_topology_from_voltage(self):
        """Infer topology from voltage measurements"""
        print("Inferring topology from voltage measurements...")
        
        components = list(self.topology_graph.components.keys())
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                wire_name = f"WIRE_{comp1}_{comp2}"
                
                if wire_name in self.topology_graph.wire_segments:
                    wire_segment = self.topology_graph.wire_segments[wire_name]
                    
                    comp1_obj = self.topology_graph.components[comp1]
                    comp2_obj = self.topology_graph.components[comp2]
                    
                    # Calculate voltage drop
                    voltage_drop_mv = self.voltage_inference.calculate_voltage_drop(
                        comp1_obj.current_ma, wire_segment.resistance_ohm
                    )
                    
                    # Infer connection
                    connected = self.voltage_inference.infer_connection_from_voltage(
                        comp1_obj.voltage_mv, comp1_obj.current_ma
                    )
                    
                    if connected:
                        edge = TopologyEdge(
                            source=comp1,
                            target=comp2,
                            wire_segment=wire_segment,
                            voltage_drop_mv=voltage_drop_mv,
                            current_ma=comp1_obj.current_ma,
                            timing_ps=wire_segment.propagation_delay_ps,
                            impedance_ohm=wire_segment.impedance_ohm
                        )
                        self.topology_graph.edges.append(edge)
                        print(f"  {comp1} -> {comp2}: connected (voltage drop: {voltage_drop_mv:.3f}mV)")
    
    def infer_topology_from_timing(self):
        """Infer topology from timing measurements"""
        print("Inferring topology from timing measurements...")
        
        # Use wire segment propagation delays for timing inference
        for wire_name, wire_segment in self.topology_graph.wire_segments.items():
            timing_ps = wire_segment.propagation_delay_ps
            
            # Infer if this is a synchronous connection
            clock_period_ps = 1000.0  # 1ns clock = 1000ps
            synchronous = self.timing_inference.infer_synchronous_connection(
                timing_ps, clock_period_ps
            )
            
            if synchronous:
                print(f"  {wire_name}: synchronous connection (timing: {timing_ps:.2f}ps)")
    
    def build_topology_graph(self):
        """Build complete topology graph"""
        print("Building topology graph...")
        
        # Create topology nodes
        for comp_name, component in self.topology_graph.components.items():
            node = TopologyNode(
                id=comp_name,
                component=component,
                connections=[],
                voltage_mv=component.voltage_mv,
                current_ma=component.current_ma,
                timing_ps=0.0
            )
            self.topology_graph.nodes[comp_name] = node
        
        # Update node connections from edges
        for edge in self.topology_graph.edges:
            if edge.source in self.topology_graph.nodes:
                self.topology_graph.nodes[edge.source].connections.append(edge.target)
            if edge.target in self.topology_graph.nodes:
                self.topology_graph.nodes[edge.target].connections.append(edge.source)
        
        print(f"  Created {len(self.topology_graph.nodes)} nodes")
        print(f"  Created {len(self.topology_graph.edges)} edges")
    
    def map_topology(self):
        """Complete topology mapping"""
        print("=" * 80)
        print("PURE SOFTWARE TOPOLOGY MAPPING")
        print("=" * 80)
        
        # Step 1: Extract sensor data
        self.extract_sensor_data()
        
        # Step 2: Extract EFI data
        self.extract_efi_data()
        
        # Step 3: Extract PCIe data
        self.extract_pcie_data()
        
        # Step 4: Extract power supply data
        self.extract_power_supply_data()
        
        # Step 5: Extract CPU topology data
        self.extract_cpu_topology_data()
        
        # Step 6: Create wire segments from PCB specs
        self.create_wire_segments_from_pcb()
        
        # Step 7: Create components from sensors
        self.create_components_from_sensors()
        
        # Step 8: Infer topology from voltage
        self.infer_topology_from_voltage()
        
        # Step 9: Infer topology from timing
        self.infer_topology_from_timing()
        
        # Step 10: Build topology graph
        self.build_topology_graph()
        
        print("=" * 80)
        print("TOPOLOGY MAPPING COMPLETE")
        print("=" * 80)
        
        return self.topology_graph
    
    def save_topology_map(self, output_path: str):
        """Save topology map to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dataclasses to dicts
        topology_data = {
            "timestamp": self.topology_graph.timestamp,
            "nodes": {k: asdict(v) for k, v in self.topology_graph.nodes.items()},
            "edges": [asdict(e) for e in self.topology_graph.edges],
            "wire_segments": {k: asdict(v) for k, v in self.topology_graph.wire_segments.items()},
            "components": {k: asdict(v) for k, v in self.topology_graph.components.items()},
            "sensor_readings": [asdict(r) for r in self.topology_graph.sensor_readings],
            "efi_data": self.efi_data,
            "pcie_data": self.pcie_data,
            "power_supply_data": self.power_supply_data,
            "cpu_data": self.cpu_data
        }
        
        with open(output_file, 'w') as f:
            json.dump(topology_data, f, indent=2)
        
        print(f"Topology map saved to: {output_file}")

# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Pure software topology mapper using sensors, PCB specs, voltage, and timing"
    )
    parser.add_argument(
        "--output",
        default="shared-data/data/germane/research/pure_software_topology_map.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Create mapper
    mapper = PureSoftwareTopologyMapper()
    
    # Map topology
    topology_graph = mapper.map_topology()
    
    # Save topology map
    mapper.save_topology_map(args.output)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TOPOLOGY MAPPING SUMMARY")
    print("=" * 80)
    print(f"Nodes: {len(topology_graph.nodes)}")
    print(f"Edges: {len(topology_graph.edges)}")
    print(f"Wire Segments: {len(topology_graph.wire_segments)}")
    print(f"Components: {len(topology_graph.components)}")
    print(f"Sensor Readings: {len(topology_graph.sensor_readings)}")
    print(f"Output: {args.output}")

if __name__ == "__main__":
    main()
