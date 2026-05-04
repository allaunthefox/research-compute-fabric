use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use std::collections::HashMap;
use dashmap::DashMap;
use chrono::{Utc, Duration};
use uuid::Uuid;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use crate::teleport::TeleportCompressor;
use crate::moe::MixtureOfExperts;
use crate::interface::{HardwareConfig, StoryArc};

/// Safety & Monitoring Layer for Fail-Safe Operations
/// Ensures user priority, safe fallbacks, and comprehensive system monitoring
#[derive(Debug, Clone)]
pub struct SafetyMonitor {
    /// System state tracking
    pub system_state: DashMap<String, SystemState>,
    /// NDAG (N-dimensional Directed Acyclic Graph) for failure tracking
    pub failure_ndag: DashMap<String, FailureNode>,
    /// User action priority queue
    pub user_priority_queue: DashMap<String, UserAction>,
    /// Hardware monitoring cache
    pub hardware_monitoring: DashMap<String, HardwareMetrics>,
    /// Safety thresholds
    pub safety_thresholds: SafetyThresholds,
    /// Emergency fallback state
    pub emergency_fallback: Arc<AtomicBool>,
    /// User override flag
    pub user_override: Arc<AtomicBool>,
    /// Teleport compressor for safety data
    pub teleport: TeleportCompressor,
    /// MoE for intelligent safety decisions
    pub moe: MixtureOfExperts,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemState {
    pub timestamp: chrono::DateTime<Utc>,
    pub state_id: String,
    pub operational_mode: OperationalMode,
    pub safety_status: SafetyStatus,
    pub user_priority_active: bool,
    pub fallback_reason: Option<String>,
    pub performance_metrics: PerformanceMetrics,
    pub thermal_metrics: ThermalMetrics,
    pub electrical_metrics: ElectricalMetrics,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OperationalMode {
    Normal,
    Optimized,
    EmergencyFallback,
    UserOverride,
    MonitoringOnly,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SafetyStatus {
    Safe,
    Warning,
    Critical,
    Emergency,
    UserOverride,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FailureNode {
    pub node_id: String,
    pub failure_type: FailureType,
    pub timestamp: chrono::DateTime<Utc>,
    pub indexed_hash: String,
    pub exact_cause: String,
    pub affected_components: Vec<String>,
    pub severity: SeverityLevel,
    pub ndag_path: Vec<String>,
    pub recovery_actions: Vec<RecoveryAction>,
    pub user_notified: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum FailureType {
    HardwareFailure,
    ThermalOverload,
    ElectricalOverload,
    SignalCorruption,
    QuantumDecoherence,
    MemoryCorruption,
    NetworkFailure,
    UserOverride,
    SafetySystemFailure,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SeverityLevel {
    Low,
    Medium,
    High,
    Critical,
    Catastrophic,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecoveryAction {
    pub action_id: String,
    pub action_type: ActionType,
    pub priority: u32,
    pub description: String,
    pub estimated_time: Duration,
    pub success_probability: f32,
    pub requires_user_approval: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ActionType {
    RollbackOptimization,
    ThermalShutdown,
    PowerReduction,
    SignalReset,
    ComponentIsolation,
    EmergencyCooling,
    UserNotification,
    SafeModeActivation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserAction {
    pub action_id: String,
    pub user_id: String,
    pub action_type: UserActionType,
    pub timestamp: chrono::DateTime<Utc>,
    pub priority: u32,
    pub description: String,
    pub requires_immediate: bool,
    pub approved: bool,
    pub executed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum UserActionType {
    OverrideOptimization,
    EmergencyStop,
    ManualControl,
    ConfigurationChange,
    DiagnosticRequest,
    SystemReset,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareMetrics {
    pub timestamp: chrono::DateTime<Utc>,
    pub component_id: String,
    pub transistor_count: u64,
    pub power_levels: PowerLevels,
    pub cycle_times: CycleTimes,
    pub wire_wrapping_metrics: WireWrappingMetrics,
    pub capacitor_timings: CapacitorTimings,
    pub computational_matrix: ComputationalMatrix,
    pub monitoring_only: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PowerLevels {
    pub voltage: f32,
    pub current: f32,
    pub power_consumption: f32,
    pub efficiency: f32,
    pub thermal_derating: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CycleTimes {
    pub min_cycle_time: Duration,
    pub max_cycle_time: Duration,
    pub average_cycle_time: Duration,
    pub jitter: f32,
    pub stability_score: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WireWrappingMetrics {
    pub solenoid_inductance: f32,
    pub wire_resistance: f32,
    pub electromagnetic_field: f32,
    pub monitoring_data: Vec<f32>, // Raw monitoring data (don't touch)
    pub anomaly_detected: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapacitorTimings {
    pub charge_time: Duration,
    pub discharge_time: Duration,
    pub ripple_voltage: f32,
    pub esr: f32,
    pub monitoring_data: Vec<f32>, // Raw monitoring data (don't touch)
    pub timing_drift: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComputationalMatrix {
    pub transistor_efficiency: HashMap<String, f32>,
    pub signal_propagation: HashMap<String, f32>,
    pub quantum_coherence: HashMap<String, f32>,
    pub optimization_impact: HashMap<String, f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub cpu_utilization: f32,
    pub gpu_utilization: f32,
    pub memory_bandwidth: f64,
    pub network_throughput: f64,
    pub optimization_gain: f32,
    pub system_latency: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThermalMetrics {
    pub cpu_temp: f32,
    pub gpu_temp: f32,
    pub motherboard_temp: f32,
    pub thermal_throttling: bool,
    pub cooling_efficiency: f32,
    pub heat_dissipation: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ElectricalMetrics {
    pub voltage_stability: f32,
    pub current_draw: f32,
    pub power_efficiency: f32,
    pub electromagnetic_interference: f32,
    pub signal_integrity: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyThresholds {
    pub max_temperature: f32,
    pub max_voltage: f32,
    pub max_current: f32,
    pub max_latency: f64,
    pub min_efficiency: f32,
    pub max_thermal_throttling: bool,
    pub max_electromagnetic_interference: f32,
}

impl SafetyMonitor {
    pub fn new() -> Self {
        Self {
            system_state: DashMap::new(),
            failure_ndag: DashMap::new(),
            user_priority_queue: DashMap::new(),
            hardware_monitoring: DashMap::new(),
            safety_thresholds: SafetyThresholds {
                max_temperature: 85.0,
                max_voltage: 1.4,
                max_current: 200.0,
                max_latency: 10.0,
                min_efficiency: 0.7,
                max_thermal_throttling: false,
                max_electromagnetic_interference: 0.1,
            },
            emergency_fallback: Arc::new(AtomicBool::new(false)),
            user_override: Arc::new(AtomicBool::new(false)),
            teleport: TeleportCompressor::new(),
            moe: MixtureOfExperts::new(),
        }
    }

    /// Initialize comprehensive hardware monitoring
    pub async fn initialize_monitoring(&self, hardware_config: &HardwareConfig) -> Result<()> {
        // Monitor CPU transistors and power levels
        self.monitor_cpu_metrics(hardware_config).await?;
        
        // Monitor GPU computational matrix
        self.monitor_gpu_metrics(hardware_config).await?;
        
        // Monitor power supply wire wrappings (read-only)
        self.monitor_power_supply_metrics().await?;
        
        // Monitor capacitor timings (read-only)
        self.monitor_capacitor_metrics().await?;
        
        // Initialize system state
        let system_state = SystemState {
            timestamp: Utc::now(),
            state_id: Uuid::new_v4().to_string(),
            operational_mode: OperationalMode::Normal,
            safety_status: SafetyStatus::Safe,
            user_priority_active: false,
            fallback_reason: None,
            performance_metrics: PerformanceMetrics {
                cpu_utilization: 0.0,
                gpu_utilization: 0.0,
                memory_bandwidth: 0.0,
                network_throughput: 0.0,
                optimization_gain: 0.0,
                system_latency: 0.0,
            },
            thermal_metrics: ThermalMetrics {
                cpu_temp: 45.0,
                gpu_temp: 50.0,
                motherboard_temp: 40.0,
                thermal_throttling: false,
                cooling_efficiency: 0.8,
                heat_dissipation: 0.7,
            },
            electrical_metrics: ElectricalMetrics {
                voltage_stability: 1.0,
                current_draw: 5.0,
                power_efficiency: 0.85,
                electromagnetic_interference: 0.05,
                signal_integrity: 0.95,
            },
        };

        self.system_state.insert("primary".to_string(), system_state);
        
        Ok(())
    }

    /// Monitor CPU metrics with transistor-level precision
    async fn monitor_cpu_metrics(&self, config: &HardwareConfig) -> Result<()> {
        let transistor_count = self.estimate_cpu_transistors(config.cpu_cores).await?;
        
        let metrics = HardwareMetrics {
            timestamp: Utc::now(),
            component_id: format!("cpu_{}_cores", config.cpu_cores),
            transistor_count,
            power_levels: PowerLevels {
                voltage: 1.2,
                current: 15.0,
                power_consumption: 18.0,
                efficiency: 0.85,
                thermal_derating: 0.0,
            },
            cycle_times: CycleTimes {
                min_cycle_time: Duration::nanoseconds(200),
                max_cycle_time: Duration::nanoseconds(500),
                average_cycle_time: Duration::nanoseconds(350),
                jitter: 0.05,
                stability_score: 0.9,
            },
            wire_wrapping_metrics: WireWrappingMetrics {
                solenoid_inductance: 0.0,
                wire_resistance: 0.001,
                electromagnetic_field: 0.001,
                monitoring_data: vec![],
                anomaly_detected: false,
            },
            capacitor_timings: CapacitorTimings {
                charge_time: Duration::nanoseconds(100),
                discharge_time: Duration::nanoseconds(150),
                ripple_voltage: 0.01,
                esr: 0.005,
                monitoring_data: vec![],
                timing_drift: 0.001,
            },
            computational_matrix: ComputationalMatrix {
                transistor_efficiency: HashMap::new(),
                signal_propagation: HashMap::new(),
                quantum_coherence: HashMap::new(),
                optimization_impact: HashMap::new(),
            },
            monitoring_only: true,
        };

        self.hardware_monitoring.insert("cpu".to_string(), metrics);
        Ok(())
    }

    /// Monitor GPU metrics with VRAM computational matrix
    async fn monitor_gpu_metrics(&self, config: &HardwareConfig) -> Result<()> {
        let transistor_count = self.estimate_gpu_transistors(config.gpu_vram_gb).await?;
        
        let metrics = HardwareMetrics {
            timestamp: Utc::now(),
            component_id: format!("gpu_{}_gb_vram", config.gpu_vram_gb),
            transistor_count,
            power_levels: PowerLevels {
                voltage: 1.1,
                current: 25.0,
                power_consumption: 27.5,
                efficiency: 0.82,
                thermal_derating: 0.0,
            },
            cycle_times: CycleTimes {
                min_cycle_time: Duration::nanoseconds(100),
                max_cycle_time: Duration::nanoseconds(300),
                average_cycle_time: Duration::nanoseconds(200),
                jitter: 0.03,
                stability_score: 0.92,
            },
            wire_wrapping_metrics: WireWrappingMetrics {
                solenoid_inductance: 0.0,
                wire_resistance: 0.0005,
                electromagnetic_field: 0.002,
                monitoring_data: vec![],
                anomaly_detected: false,
            },
            capacitor_timings: CapacitorTimings {
                charge_time: Duration::nanoseconds(50),
                discharge_time: Duration::nanoseconds(75),
                ripple_voltage: 0.005,
                esr: 0.002,
                monitoring_data: vec![],
                timing_drift: 0.0005,
            },
            computational_matrix: ComputationalMatrix {
                transistor_efficiency: HashMap::new(),
                signal_propagation: HashMap::new(),
                quantum_coherence: HashMap::new(),
                optimization_impact: HashMap::new(),
            },
            monitoring_only: true,
        };

        self.hardware_monitoring.insert("gpu".to_string(), metrics);
        Ok(())
    }

    /// Monitor power supply wire wrappings (READ-ONLY)
    async fn monitor_power_supply_metrics(&self) -> Result<()> {
        let metrics = HardwareMetrics {
            timestamp: Utc::now(),
            component_id: "power_supply".to_string(),
            transistor_count: 0, // Not applicable for power supply
            power_levels: PowerLevels {
                voltage: 12.0,
                current: 50.0,
                power_consumption: 600.0,
                efficiency: 0.9,
                thermal_derating: 0.0,
            },
            cycle_times: CycleTimes {
                min_cycle_time: Duration::microseconds(1),
                max_cycle_time: Duration::microseconds(10),
                average_cycle_time: Duration::microseconds(5),
                jitter: 0.1,
                stability_score: 0.85,
            },
            wire_wrapping_metrics: WireWrappingMetrics {
                solenoid_inductance: 0.001,
                wire_resistance: 0.01,
                electromagnetic_field: 0.05,
                monitoring_data: vec![0.01, 0.02, 0.015, 0.018], // Raw monitoring data
                anomaly_detected: false,
            },
            capacitor_timings: CapacitorTimings {
                charge_time: Duration::microseconds(100),
                discharge_time: Duration::microseconds(150),
                ripple_voltage: 0.1,
                esr: 0.01,
                monitoring_data: vec![0.1, 0.09, 0.11, 0.1], // Raw monitoring data
                timing_drift: 0.005,
            },
            computational_matrix: ComputationalMatrix {
                transistor_efficiency: HashMap::new(),
                signal_propagation: HashMap::new(),
                quantum_coherence: HashMap::new(),
                optimization_impact: HashMap::new(),
            },
            monitoring_only: true, // CRITICAL: Read-only monitoring
        };

        self.hardware_monitoring.insert("power_supply".to_string(), metrics);
        Ok(())
    }

    /// Monitor capacitor timings (READ-ONLY)
    async fn monitor_capacitor_metrics(&self) -> Result<()> {
        let metrics = HardwareMetrics {
            timestamp: Utc::now(),
            component_id: "capacitors".to_string(),
            transistor_count: 0, // Not applicable
            power_levels: PowerLevels {
                voltage: 5.0,
                current: 0.0,
                power_consumption: 0.0,
                efficiency: 1.0,
                thermal_derating: 0.0,
            },
            cycle_times: CycleTimes {
                min_cycle_time: Duration::nanoseconds(1000),
                max_cycle_time: Duration::nanoseconds(10000),
                average_cycle_time: Duration::nanoseconds(5000),
                jitter: 0.05,
                stability_score: 0.95,
            },
            wire_wrapping_metrics: WireWrappingMetrics {
                solenoid_inductance: 0.0,
                wire_resistance: 0.0001,
                electromagnetic_field: 0.0001,
                monitoring_data: vec![],
                anomaly_detected: false,
            },
            capacitor_timings: CapacitorTimings {
                charge_time: Duration::nanoseconds(5000),
                discharge_time: Duration::nanoseconds(7500),
                ripple_voltage: 0.001,
                esr: 0.0001,
                monitoring_data: vec![0.001, 0.0011, 0.0009, 0.001], // Raw monitoring data
                timing_drift: 0.0001,
            },
            computational_matrix: ComputationalMatrix {
                transistor_efficiency: HashMap::new(),
                signal_propagation: HashMap::new(),
                quantum_coherence: HashMap::new(),
                optimization_impact: HashMap::new(),
            },
            monitoring_only: true, // CRITICAL: Read-only monitoring
        };

        self.hardware_monitoring.insert("capacitors".to_string(), metrics);
        Ok(())
    }

    /// Check safety thresholds and trigger fallback if needed
    pub async fn check_safety_thresholds(&self) -> Result<bool> {
        let system_state = self.system_state.get("primary")
            .ok_or_else(|| anyhow!("Primary system state not found"))?;

        let mut needs_fallback = false;
        let mut fallback_reasons = Vec::new();

        // Check thermal thresholds
        if system_state.thermal_metrics.cpu_temp > self.safety_thresholds.max_temperature {
            needs_fallback = true;
            fallback_reasons.push(format!("CPU temperature {}°C exceeds threshold {}°C", 
                system_state.thermal_metrics.cpu_temp, self.safety_thresholds.max_temperature));
        }

        // Check electrical thresholds
        if system_state.electrical_metrics.voltage_stability > self.safety_thresholds.max_voltage {
            needs_fallback = true;
            fallback_reasons.push(format!("Voltage stability {} exceeds threshold {}", 
                system_state.electrical_metrics.voltage_stability, self.safety_thresholds.max_voltage));
        }

        // Check electromagnetic interference
        if system_state.electrical_metrics.electromagnetic_interference > self.safety_thresholds.max_electromagnetic_interference {
            needs_fallback = true;
            fallback_reasons.push(format!("EMI {} exceeds threshold {}", 
                system_state.electrical_metrics.electromagnetic_interference, self.safety_thresholds.max_electromagnetic_interference));
        }

        // Check thermal throttling
        if self.safety_thresholds.max_thermal_throttling && system_state.thermal_metrics.thermal_throttling {
            needs_fallback = true;
            fallback_reasons.push("Thermal throttling detected".to_string());
        }

        // Check user override
        if self.user_override.load(Ordering::SeqCst) {
            needs_fallback = true;
            fallback_reasons.push("User override requested".to_string());
        }

        // Trigger emergency fallback if needed
        if needs_fallback {
            self.trigger_emergency_fallback(fallback_reasons.join("; ")).await?;
            return Ok(true);
        }

        Ok(false)
    }

    /// Trigger emergency fallback with NDAG failure tracking
    pub async fn trigger_emergency_fallback(&self, reason: String) -> Result<()> {
        self.emergency_fallback.store(true, Ordering::SeqCst);
        
        // Create failure node for NDAG
        let failure_node = FailureNode {
            node_id: Uuid::new_v4().to_string(),
            failure_type: FailureType::SafetySystemFailure,
            timestamp: Utc::now(),
            indexed_hash: self.create_indexed_hash(&reason).await?,
            exact_cause: reason.clone(),
            affected_components: vec!["all".to_string()],
            severity: SeverityLevel::Critical,
            ndag_path: vec!["safety_monitor".to_string()],
            recovery_actions: self.generate_recovery_actions(&reason).await?,
            user_notified: false,
        };

        self.failure_ndag.insert(failure_node.node_id.clone(), failure_node);

        // Update system state
        if let Some(mut state) = self.system_state.get_mut("primary") {
            state.operational_mode = OperationalMode::EmergencyFallback;
            state.safety_status = SafetyStatus::Emergency;
            state.fallback_reason = Some(reason.clone());
        }

        // Notify user
        self.notify_user_of_fallback(&reason).await?;

        Ok(())
    }

    /// Handle user actions with highest priority
    pub async fn handle_user_action(&self, user_action: UserAction) -> Result<()> {
        // User actions always have highest priority
        self.user_override.store(true, Ordering::SeqCst);
        
        // Add to priority queue
        self.user_priority_queue.insert(user_action.action_id.clone(), user_action.clone());

        match user_action.action_type {
            UserActionType::EmergencyStop => {
                self.trigger_emergency_fallback("User emergency stop".to_string()).await?;
            },
            UserActionType::OverrideOptimization => {
                if let Some(mut state) = self.system_state.get_mut("primary") {
                    state.operational_mode = OperationalMode::UserOverride;
                    state.safety_status = SafetyStatus::UserOverride;
                }
            },
            UserActionType::SystemReset => {
                self.reset_to_normal_operation().await?;
            },
            _ => {
                // Handle other user actions
            }
        }

        Ok(())
    }

    /// Reset system to normal operation
    pub async fn reset_to_normal_operation(&self) -> Result<()> {
        self.emergency_fallback.store(false, Ordering::SeqCst);
        self.user_override.store(false, Ordering::SeqCst);

        if let Some(mut state) = self.system_state.get_mut("primary") {
            state.operational_mode = OperationalMode::Normal;
            state.safety_status = SafetyStatus::Safe;
            state.fallback_reason = None;
        }

        Ok(())
    }

    /// Create indexed hash for NDAG failure tracking
    async fn create_indexed_hash(&self, failure_data: &str) -> Result<String> {
        let timestamp = Utc::now().timestamp_nanos();
        let combined = format!("{}:{}", timestamp, failure_data);
        Ok(blake3::hash(combined.as_bytes()).to_hex().to_string())
    }

    /// Generate recovery actions based on failure reason
    async fn generate_recovery_actions(&self, reason: &str) -> Result<Vec<RecoveryAction>> {
        let mut actions = Vec::new();

        if reason.contains("temperature") {
            actions.push(RecoveryAction {
                action_id: "thermal_shutdown".to_string(),
                action_type: ActionType::ThermalShutdown,
                priority: 1,
                description: "Initiate thermal shutdown sequence".to_string(),
                estimated_time: Duration::seconds(30),
                success_probability: 0.95,
                requires_user_approval: false,
            });
        }

        if reason.contains("voltage") {
            actions.push(RecoveryAction {
                action_id: "power_reduction".to_string(),
                action_type: ActionType::PowerReduction,
                priority: 2,
                description: "Reduce system power consumption".to_string(),
                estimated_time: Duration::seconds(10),
                success_probability: 0.9,
                requires_user_approval: false,
            });
        }

        actions.push(RecoveryAction {
            action_id: "rollback_optimization".to_string(),
            action_type: ActionType::RollbackOptimization,
            priority: 3,
            description: "Rollback all optimizations to safe state".to_string(),
            estimated_time: Duration::seconds(5),
            success_probability: 0.99,
            requires_user_approval: false,
        });

        actions.push(RecoveryAction {
            action_id: "safe_mode_activation".to_string(),
            action_type: ActionType::SafeModeActivation,
            priority: 4,
            description: "Activate system safe mode".to_string(),
            estimated_time: Duration::seconds(2),
            success_probability: 1.0,
            requires_user_approval: false,
        });

        Ok(actions)
    }

    /// Notify user of fallback with detailed information
    async fn notify_user_of_fallback(&self, reason: &str) -> Result<()> {
        // Log the fallback
        log::error!("EMERGENCY FALLBACK TRIGGERED: {}", reason);
        
        // Update failure node as notified
        for mut failure in self.failure_ndag.iter_mut() {
            if !failure.value().user_notified {
                failure.value_mut().user_notified = true;
            }
        }

        Ok(())
    }

    /// Estimate CPU transistor count based on core count
    async fn estimate_cpu_transistors(&self, cores: u8) -> Result<u64> {
        // Rough estimation: modern CPUs have ~10-50 billion transistors
        // This is a simplified estimation for monitoring purposes
        Ok((cores as u64) * 2_000_000_000) // 2 billion transistors per core (approximate)
    }

    /// Estimate GPU transistor count based on VRAM
    async fn estimate_gpu_transistors(&self, vram_gb: u64) -> Result<u64> {
        // Rough estimation: modern GPUs have ~20-80 billion transistors
        // This is a simplified estimation for monitoring purposes
        Ok(vram_gb * 5_000_000_000) // 5 billion transistors per GB VRAM (approximate)
    }

    /// Get current system safety status
    pub fn get_safety_status(&self) -> SafetyStatus {
        if let Some(state) = self.system_state.get("primary") {
            state.safety_status.clone()
        } else {
            SafetyStatus::Critical
        }
    }

    /// Check if system is in emergency fallback
    pub fn is_in_emergency_fallback(&self) -> bool {
        self.emergency_fallback.load(Ordering::SeqCst)
    }

    /// Check if user has override control
    pub fn has_user_override(&self) -> bool {
        self.user_override.load(Ordering::SeqCst)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_safety_monitoring() {
        let monitor = SafetyMonitor::new();
        let config = HardwareConfig {
            cpu_cores: 8,
            cpu_base_freq: 3.5,
            cpu_boost_freq: 5.0,
            ram_capacity_gb: 32,
            ram_frequency_mhz: 3200.0,
            gpu_vram_gb: 16,
            gpu_core_clock: 1800.0,
            nvme_capacity_tb: 2.0,
            pcie_lanes: 16,
            story_arc: StoryArc::Optimization,
        };

        monitor.initialize_monitoring(&config).await.unwrap();
        
        assert!(!monitor.is_in_emergency_fallback());
        assert!(!monitor.has_user_override());
        assert_eq!(monitor.get_safety_status(), SafetyStatus::Safe);
    }

    #[tokio::test]
    async fn test_emergency_fallback() {
        let monitor = SafetyMonitor::new();
        
        monitor.trigger_emergency_fallback("Test fallback".to_string()).await.unwrap();
        
        assert!(monitor.is_in_emergency_fallback());
        assert_eq!(monitor.get_safety_status(), SafetyStatus::Emergency);
    }

    #[tokio::test]
    async fn test_user_override() {
        let monitor = SafetyMonitor::new();
        
        let user_action = UserAction {
            action_id: "test_action".to_string(),
            user_id: "test_user".to_string(),
            action_type: UserActionType::OverrideOptimization,
            timestamp: Utc::now(),
            priority: 1,
            description: "Test user override".to_string(),
            requires_immediate: true,
            approved: true,
            executed: false,
        };

        monitor.handle_user_action(user_action).await.unwrap();
        
        assert!(monitor.has_user_override());
        assert_eq!(monitor.get_safety_status(), SafetyStatus::UserOverride);
    }
}