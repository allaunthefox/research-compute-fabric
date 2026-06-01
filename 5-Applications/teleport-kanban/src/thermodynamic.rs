use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use std::sync::atomic::{AtomicU32, AtomicBool, AtomicPtr, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use chrono::{Utc, DateTime};
use dashmap::DashMap;

use crate::teleport::TeleportCompressor;
use crate::interface::{HardwareConfig, StoryArc};
use crate::safety::SafetyMonitor;

/// Thermodynamic State Machine for BF16 Teleport Compression System
/// Converts the entire system into a thermodynamic state machine with fail-soft then safe modes
/// Based on Gemini's suggestions for 9600X optimization
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ThermodynamicState {
    /// Ground State: Minimal Entropy, Max Performance
    /// Soliton-Folded (Branchless), Full AVX-512, High Power
    Ground,
    /// Metastable State: High Heat/Noise
    /// Standard Branching, Mixed Scalar/SIMD, Mid Power
    Metastable,
    /// High-Entropy State: Thermal Throttling
    /// Serialized Logic, Scalar x86 Only, Low Power
    ThermalMax,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThermodynamicMetrics {
    pub timestamp: DateTime<Utc>,
    pub temperature_c: f64,
    pub power_watts: f64,
    pub current_entropy: f64,
    pub target_entropy: f64,
    pub state_transition_count: u64,
    pub last_transition: Option<DateTime<Utc>>,
    pub thermal_headroom: f64,
    pub performance_degradation: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PStateControl {
    pub pstate_level: u32,
    pub voltage_offset: i32,
    pub frequency_cap: u32,
    pub efficiency_mode: bool,
    pub precision_boost_enabled: bool,
}

#[derive(Debug, Clone)]
pub struct TripleBufferLUT {
    /// Ground State LUT: Max P-State + AVX-512 Soliton Folding
    pub ground_lut: Arc<DashMap<String, Vec<u8>>>,
    /// Fail-Soft LUT: Mid P-State + Standard Branching
    pub soft_lut: Arc<DashMap<String, Vec<u8>>>,
    /// Fail-Safe LUT: Low P-State + Scalar Serialized Logic
    pub safe_lut: Arc<DashMap<String, Vec<u8>>>,
    /// Active LUT pointer (Atomic for O(1) switching)
    pub active_lut: Arc<AtomicPtr<DashMap<String, Vec<u8>>>>,
}

#[derive(Debug, Clone)]
pub struct DeadMansSwitch {
    pub watchdog_enabled: bool,
    pub prochot_threshold: f64,
    pub emergency_timeout_ms: u64,
    pub last_heartbeat: Arc<AtomicU32>,
    pub emergency_triggered: Arc<AtomicBool>,
    pub ipi_target: Option<String>,
}

/// Thermodynamic Governor for 9600X Optimization
/// Manages the entire system as a non-equilibrium thermodynamic machine
pub struct ThermodynamicGovernor {
    /// Current thermodynamic state
    pub current_state: Arc<AtomicU32>,
    /// System metrics tracking
    pub metrics: Arc<DashMap<String, ThermodynamicMetrics>>,
    /// P-State control for hardware optimization
    pub pstate_control: Arc<AtomicPtr<PStateControl>>,
    /// Triple-buffer LUT for state transitions
    pub lut_strategy: TripleBufferLUT,
    /// Dead man's switch for emergency fallback
    pub dead_mans_switch: DeadMansSwitch,
    /// Safety monitor integration
    pub safety_monitor: SafetyMonitor,
    /// Teleport compressor for BF16 operations
    pub teleport: TeleportCompressor,
    /// Hardware configuration
    pub hardware_config: HardwareConfig,
    /// State transition history
    pub transition_history: Arc<DashMap<u64, ThermodynamicState>>,
    /// Performance counters
    pub performance_counters: Arc<DashMap<String, u64>>,
}

impl ThermodynamicGovernor {
    pub fn new(safety_monitor: SafetyMonitor, hardware_config: HardwareConfig) -> Self {
        let lut_strategy = TripleBufferLUT {
            ground_lut: Arc::new(DashMap::new()),
            soft_lut: Arc::new(DashMap::new()),
            safe_lut: Arc::new(DashMap::new()),
            active_lut: Arc::new(AtomicPtr::new(std::ptr::null_mut())),
        };

        // Initialize active LUT to ground state
        let active_ptr = Arc::as_ptr(&lut_strategy.ground_lut) as *mut DashMap<String, Vec<u8>>;
        lut_strategy.active_lut.store(active_ptr, Ordering::SeqCst);

        Self {
            current_state: Arc::new(AtomicU32::new(ThermodynamicState::Ground as u32)),
            metrics: Arc::new(DashMap::new()),
            pstate_control: Arc::new(AtomicPtr::new(Box::into_raw(Box::new(PStateControl {
                pstate_level: 255,
                voltage_offset: 0,
                frequency_cap: 5200,
                efficiency_mode: false,
                precision_boost_enabled: true,
            })))),
            lut_strategy,
            dead_mans_switch: DeadMansSwitch {
                watchdog_enabled: true,
                prochot_threshold: 95.0,
                emergency_timeout_ms: 1000,
                last_heartbeat: Arc::new(AtomicU32::new(0)),
                emergency_triggered: Arc::new(AtomicBool::new(false)),
                ipi_target: None,
            },
            safety_monitor,
            teleport: TeleportCompressor::new(),
            hardware_config,
            transition_history: Arc::new(DashMap::new()),
            performance_counters: Arc::new(DashMap::new()),
        }
    }

    /// Main thermodynamic control loop
    pub async fn run_thermodynamic_loop(&self) -> Result<()> {
        let mut last_state_check = Instant::now();
        let state_check_interval = Duration::from_millis(10); // 100Hz polling

        loop {
            if last_state_check.elapsed() >= state_check_interval {
                self.update_thermodynamic_state().await?;
                self.update_pstate_control().await?;
                self.update_triple_buffer_lut().await?;
                self.check_dead_mans_switch().await?;
                
                last_state_check = Instant::now();
            }

            // Small delay to prevent CPU spinning
            tokio::time::sleep(Duration::from_millis(1)).await;
        }
    }

    /// Update thermodynamic state based on system metrics
    async fn update_thermodynamic_state(&self) -> Result<()> {
        let current_temp = self.read_zen5_temperature().await?;
        let current_power = self.read_zen5_power().await?;
        let current_entropy = self.calculate_system_entropy(current_temp, current_power).await?;

        let target_state = self.determine_thermodynamic_state(current_temp, current_power, current_entropy).await?;
        
        if target_state != self.get_current_state() {
            self.transition_to_state(&target_state).await?;
        }

        // Update metrics
        let metrics = ThermodynamicMetrics {
            timestamp: Utc::now(),
            temperature_c: current_temp,
            power_watts: current_power,
            current_entropy,
            target_entropy: self.get_target_entropy(&target_state),
            state_transition_count: self.get_transition_count() + 1,
            last_transition: Some(Utc::now()),
            thermal_headroom: 95.0 - current_temp,
            performance_degradation: self.calculate_performance_degradation(&target_state),
        };

        self.metrics.insert("current".to_string(), metrics);
        Ok(())
    }

    /// Determine thermodynamic state based on physical constraints
    async fn determine_thermodynamic_state(
        &self, 
        temp: f64, 
        power: f64, 
        entropy: f64
    ) -> Result<ThermodynamicState> {
        // Ground State: High performance, controlled heat
        if temp < 75.0 && power < 120.0 && entropy < 0.3 {
            Ok(ThermodynamicState::Ground)
        }
        // Metastable State: Moderate heat, reduced performance
        else if temp < 85.0 && power < 150.0 && entropy < 0.7 {
            Ok(ThermodynamicState::Metastable)
        }
        // ThermalMax State: Critical heat, emergency mode
        else {
            Ok(ThermodynamicState::ThermalMax)
        }
    }

    /// Transition to new thermodynamic state
    async fn transition_to_state(&self, new_state: &ThermodynamicState) -> Result<()> {
        let old_state = self.get_current_state();
        
        // Record transition
        self.transition_history.insert(
            Utc::now().timestamp() as u64,
            new_state.clone()
        );

        // Update P-State control based on new state
        self.configure_pstate_for_state(&new_state).await?;

        // Switch LUT strategy
        self.switch_lut_strategy(&new_state).await?;

        // Update safety monitor
        self.update_safety_monitor_for_state(&new_state).await?;

        // Log transition
        log::info!("Thermodynamic state transition: {:?} -> {:?}", old_state, new_state);

        self.current_state.store(new_state as *const _ as u32, Ordering::SeqCst);
        Ok(())
    }

    /// Configure P-State control for specific thermodynamic state
    async fn configure_pstate_for_state(&self, state: &ThermodynamicState) -> Result<()> {
        let pstate_config = match state {
            ThermodynamicState::Ground => PStateControl {
                pstate_level: 255,           // Max performance
                voltage_offset: 0,           // Standard voltage
                frequency_cap: 5200,         // Max boost
                efficiency_mode: false,
                precision_boost_enabled: true,
            },
            ThermodynamicState::Metastable => PStateControl {
                pstate_level: 192,           // Mid performance
                voltage_offset: -25,         // Slight undervolt
                frequency_cap: 4800,         // Reduced boost
                efficiency_mode: true,
                precision_boost_enabled: false,
            },
            ThermodynamicState::ThermalMax => PStateControl {
                pstate_level: 128,           // Low performance
                voltage_offset: -50,         // Aggressive undervolt
                frequency_cap: 4200,         // Thermal cap
                efficiency_mode: true,
                precision_boost_enabled: false,
            },
        };

        let new_ptr = Box::into_raw(Box::new(pstate_config));
        // Swap atomically and free the old allocation to prevent memory leak.
        let old_ptr = self.pstate_control.swap(new_ptr, Ordering::SeqCst);
        if !old_ptr.is_null() {
            unsafe { drop(Box::from_raw(old_ptr)); }
        }

        // Apply hardware P-State changes
        self.apply_hardware_pstate_changes(unsafe { &*new_ptr }).await?;
        Ok(())
    }

    /// Switch LUT strategy based on thermodynamic state
    async fn switch_lut_strategy(&self, state: &ThermodynamicState) -> Result<()> {
        let target_lut = match state {
            ThermodynamicState::Ground => Arc::as_ptr(&self.lut_strategy.ground_lut),
            ThermodynamicState::Metastable => Arc::as_ptr(&self.lut_strategy.soft_lut),
            ThermodynamicState::ThermalMax => Arc::as_ptr(&self.lut_strategy.safe_lut),
        };

        // O(1) LUT switch
        self.lut_strategy.active_lut.store(
            target_lut as *mut DashMap<String, Vec<u8>>,
            Ordering::SeqCst
        );

        log::debug!("Switched LUT strategy to: {:?}", state);
        Ok(())
    }

    /// Update safety monitor based on thermodynamic state
    async fn update_safety_monitor_for_state(&self, state: &ThermodynamicState) -> Result<()> {
        match state {
            ThermodynamicState::Ground => {
                // Enable full optimization with safety monitoring
                self.safety_monitor.reset_to_normal_operation().await?;
            },
            ThermodynamicState::Metastable => {
                // Enable fail-soft mode
                self.safety_monitor.handle_user_action(crate::safety::UserAction {
                    action_id: "fail_soft_transition".to_string(),
                    user_id: "thermodynamic_governor".to_string(),
                    action_type: crate::safety::UserActionType::OverrideOptimization,
                    timestamp: Utc::now(),
                    priority: 5,
                    description: "Fail-soft transition due to thermal constraints".to_string(),
                    requires_immediate: false,
                    approved: true,
                    executed: true,
                }).await?;
            },
            ThermodynamicState::ThermalMax => {
                // Emergency fallback
                self.safety_monitor.trigger_emergency_fallback(
                    "Thermal emergency: system in ThermalMax state".to_string()
                ).await?;
            },
        }
        Ok(())
    }

    /// Update P-State control based on current state
    async fn update_pstate_control(&self) -> Result<()> {
        // This would interface with actual MSR registers on real hardware
        // For now, we simulate the behavior
        let current_state = self.get_current_state();
        let pstate_ptr = self.pstate_control.load(Ordering::SeqCst);
        
        if !pstate_ptr.is_null() {
            let pstate_ref = unsafe { &*pstate_ptr };
            log::debug!("Current P-State: {:?}, Level: {}", current_state, pstate_ref.pstate_level);
        }
        Ok(())
    }

    /// Update triple-buffer LUT based on current workload
    async fn update_triple_buffer_lut(&self) -> Result<()> {
        let active_lut_ptr = self.lut_strategy.active_lut.load(Ordering::SeqCst);
        
        if !active_lut_ptr.is_null() {
            let active_lut = unsafe { &*active_lut_ptr };
            
            // Update LUT with current compression patterns
            let compression_result = self.teleport.compress_semantic("thermodynamic_workload").await?;
            active_lut.insert("current_workload".to_string(), compression_result.into_bytes());
        }
        Ok(())
    }

    /// Check dead man's switch for emergency fallback
    async fn check_dead_mans_switch(&self) -> Result<()> {
        if !self.dead_mans_switch.watchdog_enabled {
            return Ok(());
        }

        let current_time = Utc::now().timestamp_millis() as u64;
        let last_heartbeat = self.dead_mans_switch.last_heartbeat.load(Ordering::Relaxed);
        
        // Update heartbeat
        self.dead_mans_switch.last_heartbeat.store(current_time as u32, Ordering::Relaxed);

        // Check for emergency conditions
        let current_temp = self.read_zen5_temperature().await?;
        
        if current_temp > self.dead_mans_switch.prochot_threshold {
            self.trigger_emergency_fallback().await?;
        }

        // Check for timeout
        if current_time - (last_heartbeat as u64) > self.dead_mans_switch.emergency_timeout_ms {
            self.trigger_emergency_fallback().await?;
        }

        Ok(())
    }

    /// Trigger emergency fallback
    async fn trigger_emergency_fallback(&self) -> Result<()> {
        self.dead_mans_switch.emergency_triggered.store(true, Ordering::SeqCst);
        
        // Force transition to ThermalMax state
        self.transition_to_state(&ThermodynamicState::ThermalMax).await?;
        
        // Notify safety monitor
        self.safety_monitor.trigger_emergency_fallback(
            "Dead man's switch emergency trigger".to_string()
        ).await?;

        log::error!("Emergency fallback triggered by dead man's switch");
        Ok(())
    }

    /// Apply hardware P-State changes (MSR interface)
    async fn apply_hardware_pstate_changes(&self, pstate: &PStateControl) -> Result<()> {
        // This would interface with actual MSR registers:
        // - MSR_AMD_PSTATE_CTL (0xC0010062)
        // - MSR_AMD_CPPC_CAP1 (0xC00102B0)
        // - MSR_AMD_CPPC_REQ (0xC00102B1)
        
        log::debug!("Would apply P-State changes: level={}, cap={}MHz", 
                   pstate.pstate_level, pstate.frequency_cap);
        Ok(())
    }

    /// Read Zen 5 temperature (simulated)
    async fn read_zen5_temperature(&self) -> Result<f64> {
        // In real implementation, this would read from:
        // - MSR 0xC00102E3 (TjMax)
        // - MSR 0xC00102E4 (Current Temperature)
        
        // Simulated temperature based on load
        let base_temp = 45.0;
        let load_factor = self.get_current_load_factor().await?;
        Ok(base_temp + (load_factor * 30.0))
    }

    /// Read Zen 5 power consumption (simulated)
    async fn read_zen5_power(&self) -> Result<f64> {
        // In real implementation, this would read from:
        // - MSR 0xC0010299 (Power Consumption)
        // - MSR 0xC001029A (Energy Counter)
        
        // Simulated power based on state
        let base_power = 65.0;
        let state_factor = match self.get_current_state() {
            ThermodynamicState::Ground => 1.5,
            ThermodynamicState::Metastable => 1.2,
            ThermodynamicState::ThermalMax => 0.8,
        };
        Ok(base_power * state_factor)
    }

    /// Calculate system entropy based on temperature and power
    async fn calculate_system_entropy(&self, temp: f64, power: f64) -> Result<f64> {
        // Entropy calculation based on thermodynamic principles
        let temp_factor = (temp - 45.0) / 50.0; // Normalize to 0-1
        let power_factor = (power - 65.0) / 100.0; // Normalize to 0-1
        
        // Combined entropy (0.0 = perfect order, 1.0 = maximum entropy)
        Ok((temp_factor + power_factor) / 2.0)
    }

    /// Get current thermodynamic state
    fn get_current_state(&self) -> ThermodynamicState {
        match self.current_state.load(Ordering::SeqCst) {
            0 => ThermodynamicState::Ground,
            1 => ThermodynamicState::Metastable,
            2 => ThermodynamicState::ThermalMax,
            _ => ThermodynamicState::Ground,
        }
    }

    /// Get target entropy for state
    fn get_target_entropy(&self, state: &ThermodynamicState) -> f64 {
        match state {
            ThermodynamicState::Ground => 0.2,
            ThermodynamicState::Metastable => 0.5,
            ThermodynamicState::ThermalMax => 0.8,
        }
    }

    /// Get transition count
    fn get_transition_count(&self) -> u64 {
        self.transition_history.len() as u64
    }

    /// Calculate performance degradation for state
    fn calculate_performance_degradation(&self, state: &ThermodynamicState) -> f64 {
        match state {
            ThermodynamicState::Ground => 0.0,      // No degradation
            ThermodynamicState::Metastable => 0.25, // 25% degradation
            ThermodynamicState::ThermalMax => 0.60, // 60% degradation
        }
    }

    /// Get current load factor (simulated)
    async fn get_current_load_factor(&self) -> Result<f64> {
        // Simulate load based on compression activity
        let compression_count = self.performance_counters.get("compressions").map(|c| *c.value()).unwrap_or(0);
        Ok((compression_count % 100) as f64 / 100.0)
    }

    /// Get active LUT reference
    pub fn get_active_lut(&self) -> Arc<DashMap<String, Vec<u8>>> {
        let active_ptr = self.lut_strategy.active_lut.load(Ordering::SeqCst);
        if active_ptr.is_null() {
            self.lut_strategy.ground_lut.clone()
        } else {
            // SAFETY: active_ptr was obtained via Arc::as_ptr() and does not transfer
            // ownership. We must NOT call Arc::from_raw (which steals the refcount).
            // Instead, reconstruct a temporary Arc in ManuallyDrop and clone it.
            let borrowed = unsafe { std::mem::ManuallyDrop::new(Arc::from_raw(active_ptr)) };
            (*borrowed).clone()
        }
    }

    /// Record performance counter
    pub fn record_performance(&self, counter: &str, value: u64) {
        let mut entry = self.performance_counters.entry(counter.to_string()).or_insert(0);
        *entry += value;
    }
}

impl Drop for ThermodynamicGovernor {
    fn drop(&mut self) {
        // Free the PStateControl allocation created via Box::into_raw.
        let pstate_ptr = self.pstate_control.load(Ordering::SeqCst);
        if !pstate_ptr.is_null() {
            unsafe { drop(Box::from_raw(pstate_ptr)); }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::safety::SafetyMonitor;

    #[tokio::test]
    async fn test_thermodynamic_state_transitions() {
        let safety_monitor = SafetyMonitor::new();
        let config = HardwareConfig {
            cpu_cores: 6,
            cpu_base_freq: 3.5,
            cpu_boost_freq: 5.2,
            ram_capacity_gb: 32,
            ram_frequency_mhz: 3200.0,
            gpu_vram_gb: 8,
            gpu_core_clock: 2000.0,
            nvme_capacity_tb: 1.0,
            pcie_lanes: 16,
            story_arc: StoryArc::Optimization,
        };

        let governor = ThermodynamicGovernor::new(safety_monitor, config);
        
        // Test state transitions
        assert_eq!(governor.get_current_state(), ThermodynamicState::Ground);
        
        // Simulate thermal stress
        let metrics = ThermodynamicMetrics {
            timestamp: Utc::now(),
            temperature_c: 85.0,
            power_watts: 150.0,
            current_entropy: 0.8,
            target_entropy: 0.8,
            state_transition_count: 1,
            last_transition: Some(Utc::now()),
            thermal_headroom: 10.0,
            performance_degradation: 0.6,
        };

        governor.metrics.insert("test".to_string(), metrics);
        
        // Should transition to ThermalMax
        let new_state = governor.determine_thermodynamic_state(85.0, 150.0, 0.8).await.unwrap();
        assert_eq!(new_state, ThermodynamicState::ThermalMax);
    }

    #[test]
    fn test_pstate_configuration() {
        let ground_config = PStateControl {
            pstate_level: 255,
            voltage_offset: 0,
            frequency_cap: 5200,
            efficiency_mode: false,
            precision_boost_enabled: true,
        };

        let thermal_max_config = PStateControl {
            pstate_level: 128,
            voltage_offset: -50,
            frequency_cap: 4200,
            efficiency_mode: true,
            precision_boost_enabled: false,
        };

        assert!(ground_config.pstate_level > thermal_max_config.pstate_level);
        assert!(ground_config.frequency_cap > thermal_max_config.frequency_cap);
        assert!(ground_config.voltage_offset > thermal_max_config.voltage_offset);
    }
}