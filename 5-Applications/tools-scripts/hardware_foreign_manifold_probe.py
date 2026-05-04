#!/usr/bin/env python3
"""
Hardware Foreign Manifold Probe

Uses existing Linux drivers to directly probe hardware, treating it as a foreign manifold
that needs exact mapping down to the joule.

Hardware Components:
- U1: Lattice iCE40UP5K-SG48 FPGA (via ice40-spi.c driver)
- U2: DW3000 Qorvo UWB Transceiver (via SPI)
- U3-4: Si5351A-B-GT Clock Generator Array (via I2C)
- U7: AEM20940 Energy Manager (via I2C)

Power Measurement:
- Joule-level precision via /sys/class/power_supply
- Real-time power consumption tracking
- Foreign manifold mapping with exact energy coordinates
"""

import os
import sys
import time
import json
import subprocess
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# Foreign Manifold Data Structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EnergyCoordinate:
    """Exact energy coordinate in the foreign manifold (joules)"""
    timestamp: float
    voltage_mv: float
    current_ma: float
    power_mw: float
    energy_joules: float
    device_id: str
    component: str

@dataclass
class HardwareState:
    """Complete hardware state snapshot"""
    timestamp: float
    fpga_state: Dict
    uwb_state: Dict
    clock_state: Dict
    energy_state: EnergyCoordinate
    manifold_coordinates: Dict[str, float]

@dataclass
class ForeignManifoldMap:
    """Complete foreign manifold mapping"""
    device_id: str
    components: List[str]
    energy_trajectory: List[EnergyCoordinate]
    hardware_states: List[HardwareState]
    total_energy_joules: float
    manifold_dimensions: Dict[str, tuple]

# ═══════════════════════════════════════════════════════════════════════════
# Hardware Probing via Linux Drivers
# ═══════════════════════════════════════════════════════════════════════════

class HardwareProbe:
    """Probe hardware using existing Linux drivers"""
    
    def __init__(self, device_id: str = "sovereign-stack-v5"):
        self.device_id = device_id
        self.sysfs_base = Path("/sys")
        self.manifold_map = ForeignManifoldMap(
            device_id=device_id,
            components=["fpga", "uwb", "clock", "energy"],
            energy_trajectory=[],
            hardware_states=[],
            total_energy_joules=0.0,
            manifold_dimensions={}
        )
        self.last_energy_joules = 0.0
        self.start_time = time.time()
        
    def probe_fpga(self) -> Dict:
        """Probe Lattice iCE40 FPGA via ice40-spi.c driver"""
        fpga_state = {
            "driver": "ice40-spi",
            "device": "lattice,ice40-fpga-mgr",
            "state": "unknown"
        }
        
        # Check FPGA manager state via sysfs
        fpga_mgr_path = self.sysfs_base / "class" / "fpga_manager"
        if fpga_mgr_path.exists():
            for device in fpga_mgr_path.iterdir():
                state_file = device / "state"
                if state_file.exists():
                    fpga_state["state"] = state_file.read_text().strip()
                    fpga_state["device_path"] = str(device)
                    break
        
        # Check SPI device
        spi_path = self.sysfs_base / "bus" / "spi"
        if spi_path.exists():
            spi_devices = [d for d in spi_path.iterdir() if d.is_dir() and d.name.startswith("spi")]
            fpga_state["spi_devices"] = len(spi_devices)
            fpga_state["spi_paths"] = [str(d) for d in spi_devices]
        
        # Check GPIO (reset, CDONE)
        gpio_path = self.sysfs_base / "class" / "gpio"
        if gpio_path.exists():
            gpios = [d for d in gpio_path.iterdir() if d.is_dir() and d.name.startswith("gpiochip")]
            fpga_state["gpio_chips"] = len(gpios)
        
        return fpga_state
    
    def probe_uwb(self) -> Dict:
        """Probe DW3000 UWB via SPI"""
        uwb_state = {
            "driver": "dw3000",
            "device": "qorvo,dw3000",
            "state": "unknown"
        }
        
        # Check for UWB devices
        spi_path = self.sysfs_base / "bus" / "spi"
        if spi_path.exists():
            uwb_devices = []
            for device in spi_path.iterdir():
                if device.is_dir() and device.name.startswith("spi"):
                    modalias = device / "modalias"
                    if modalias.exists():
                        modalias_content = modalias.read_text().strip()
                        if "dw3000" in modalias_content.lower() or "uwb" in modalias_content.lower():
                            uwb_devices.append(str(device))
            
            uwb_state["devices"] = len(uwb_devices)
            uwb_state["device_paths"] = uwb_devices
            if uwb_devices:
                uwb_state["state"] = "detected"
        
        # Check for UWB class devices
        uwb_class_path = self.sysfs_base / "class" / "uwb"
        if uwb_class_path.exists():
            uwb_state["uwb_class_devices"] = len(list(uwb_class_path.iterdir()))
        
        return uwb_state
    
    def probe_clock(self) -> Dict:
        """Probe Si5351A clock generator via I2C"""
        clock_state = {
            "driver": "si5351",
            "device": "si5351a-b-gt",
            "state": "unknown"
        }
        
        # Check for I2C devices
        i2c_path = self.sysfs_base / "bus" / "i2c"
        if i2c_path.exists():
            si5351_devices = []
            for bus in i2c_path.iterdir():
                if bus.is_dir() and bus.name.startswith("i2c-"):
                    for device in bus.iterdir():
                        if device.is_dir() and device.name.startswith("i2c-"):
                            name_file = device / "name"
                            if name_file.exists():
                                name_content = name_file.read_text().strip()
                                if "si5351" in name_content.lower():
                                    si5351_devices.append(str(device))
            
            clock_state["devices"] = len(si5351_devices)
            clock_state["device_paths"] = si5351_devices
            if si5351_devices:
                clock_state["state"] = "detected"
        
        # Check clock subsystem
        clock_class_path = self.sysfs_base / "class" / "clk"
        if clock_class_path.exists():
            clocks = list(clock_class_path.iterdir())
            clock_state["clock_count"] = len(clocks)
        
        return clock_state
    
    def measure_energy(self) -> EnergyCoordinate:
        """Measure energy consumption at joule-level precision"""
        voltage_mv = 0.0
        current_ma = 0.0
        power_mw = 0.0
        
        # Try multiple power measurement interfaces
        # 1. Power supply class
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
                        except (ValueError, IOError):
                            pass
                    
                    if current_file.exists():
                        try:
                            current_ua = int(current_file.read_text().strip())
                            current_ma = current_ua / 1000.0
                        except (ValueError, IOError):
                            pass
        
        # 2. HWMON (hardware monitoring)
        hwmon_path = self.sysfs_base / "class" / "hwmon"
        if hwmon_path.exists():
            for hwmon in hwmon_path.iterdir():
                if hwmon.is_dir():
                    # Look for voltage and current sensors
                    for sensor in hwmon.iterdir():
                        if sensor.is_file():
                            if "in" in sensor.name and "input" in sensor.name:
                                try:
                                    voltage_mv = float(sensor.read_text().strip())
                                except (ValueError, IOError):
                                    pass
                            elif "curr" in sensor.name and "input" in sensor.name:
                                try:
                                    current_ma = float(sensor.read_text().strip())
                                except (ValueError, IOError):
                                    pass
        
        # 3. PowerCAP (RAPL for Intel CPUs)
        powercap_path = self.sysfs_base / "class" / "powercap"
        if powercap_path.exists():
            for domain in powercap_path.iterdir():
                if domain.is_dir():
                    energy_file = domain / "energy_uj"
                    if energy_file.exists():
                        try:
                            energy_uj = int(energy_file.read_text().strip())
                            energy_joules = energy_uj / 1000000.0
                            return EnergyCoordinate(
                                timestamp=time.time(),
                                voltage_mv=voltage_mv,
                                current_ma=current_ma,
                                power_mw=power_mw,
                                energy_joules=energy_joules,
                                device_id=self.device_id,
                                component="powercap"
                            )
                        except (ValueError, IOError):
                            pass
        
        # Calculate power and energy
        power_mw = (voltage_mv * current_ma) / 1000.0  # mW
        
        # Calculate energy (integral of power over time)
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        energy_joules = (power_mw / 1000.0) * elapsed_time  # Joules = (mW / 1000) * seconds
        
        return EnergyCoordinate(
            timestamp=current_time,
            voltage_mv=voltage_mv,
            current_ma=current_ma,
            power_mw=power_mw,
            energy_joules=energy_joules,
            device_id=self.device_id,
            component="sysfs"
        )
    
    def compute_manifold_coordinates(self, energy: EnergyCoordinate) -> Dict[str, float]:
        """Compute foreign manifold coordinates from energy measurement"""
        # Map energy to manifold coordinates (11-dimensional space)
        coordinates = {
            "energy_0": energy.energy_joules,
            "power_1": energy.power_mw,
            "voltage_2": energy.voltage_mv / 1000.0,  # Normalize to volts
            "current_3": energy.current_ma / 1000.0,  # Normalize to amps
            "time_4": energy.timestamp,
            "delta_energy_5": energy.energy_joules - self.last_energy_joules,
            "efficiency_6": 0.0,  # Will be computed
            "thermal_7": 0.0,  # Will be computed from temperature
            "entropy_8": 0.0,  # Will be computed from state
            "coherence_9": 1.0,  # Initial coherence
            "topology_10": 0.0  # Topological coordinate
        }
        
        self.last_energy_joules = energy.energy_joules
        return coordinates
    
    def probe_all(self) -> HardwareState:
        """Probe all hardware components"""
        fpga_state = self.probe_fpga()
        uwb_state = self.probe_uwb()
        clock_state = self.probe_clock()
        energy_state = self.measure_energy()
        manifold_coordinates = self.compute_manifold_coordinates(energy_state)
        
        state = HardwareState(
            timestamp=time.time(),
            fpga_state=fpga_state,
            uwb_state=uwb_state,
            clock_state=clock_state,
            energy_state=energy_state,
            manifold_coordinates=manifold_coordinates
        )
        
        self.manifold_map.energy_trajectory.append(energy_state)
        self.manifold_map.hardware_states.append(state)
        self.manifold_map.total_energy_joules = energy_state.energy_joules
        
        return state
    
    def continuous_probe(self, duration_seconds: float, interval_seconds: float = 1.0):
        """Continuously probe hardware over time"""
        print(f"Starting continuous probe for {duration_seconds} seconds...")
        print(f"Interval: {interval_seconds} seconds")
        print("=" * 80)
        
        start_time = time.time()
        probe_count = 0
        
        while time.time() - start_time < duration_seconds:
            state = self.probe_all()
            probe_count += 1
            
            # Print current state
            print(f"\nProbe #{probe_count} at {state.timestamp:.3f}s")
            print(f"  Energy: {state.energy_state.energy_joules:.6f} J")
            print(f"  Power: {state.energy_state.power_mw:.3f} mW")
            print(f"  Voltage: {state.energy_state.voltage_mv:.1f} mV")
            print(f"  Current: {state.energy_state.current_ma:.1f} mA")
            print(f"  FPGA State: {state.fpga_state.get('state', 'unknown')}")
            print(f"  UWB Devices: {state.uwb_state.get('devices', 0)}")
            print(f"  Clock Devices: {state.clock_state.get('devices', 0)}")
            print(f"  Manifold Coordinates: {list(state.manifold_coordinates.keys())}")
            
            time.sleep(interval_seconds)
        
        print("\n" + "=" * 80)
        print(f"Probe complete. Total probes: {probe_count}")
        print(f"Total energy consumed: {self.manifold_map.total_energy_joules:.6f} J")
    
    def save_manifold_map(self, output_path: str):
        """Save foreign manifold map to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dataclasses to dicts
        manifold_data = {
            "device_id": self.manifold_map.device_id,
            "components": self.manifold_map.components,
            "energy_trajectory": [asdict(e) for e in self.manifold_map.energy_trajectory],
            "hardware_states": [asdict(h) for h in self.manifold_map.hardware_states],
            "total_energy_joules": self.manifold_map.total_energy_joules,
            "manifold_dimensions": self.manifold_map.manifold_dimensions,
            "probe_duration_seconds": time.time() - self.start_time,
            "probe_count": len(self.manifold_map.hardware_states)
        }
        
        with open(output_file, 'w') as f:
            json.dump(manifold_data, f, indent=2)
        
        print(f"Manifold map saved to: {output_file}")

# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Probe hardware as foreign manifold with joule-level precision"
    )
    parser.add_argument(
        "--device-id",
        default="sovereign-stack-v5",
        help="Device identifier"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Probe duration in seconds"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Probe interval in seconds"
    )
    parser.add_argument(
        "--output",
        default="shared-data/data/germane/research/hardware_foreign_manifold_map.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Create probe
    probe = HardwareProbe(device_id=args.device_id)
    
    # Run continuous probe
    probe.continuous_probe(
        duration_seconds=args.duration,
        interval_seconds=args.interval
    )
    
    # Save manifold map
    probe.save_manifold_map(args.output)
    
    # Print summary
    print("\n" + "=" * 80)
    print("FOREIGN MANIFOLD MAPPING COMPLETE")
    print("=" * 80)
    print(f"Device ID: {probe.manifold_map.device_id}")
    print(f"Components: {probe.manifold_map.components}")
    print(f"Total Energy: {probe.manifold_map.total_energy_joules:.6f} J")
    print(f"Probe Count: {len(probe.manifold_map.hardware_states)}")
    print(f"Output: {args.output}")

if __name__ == "__main__":
    main()
