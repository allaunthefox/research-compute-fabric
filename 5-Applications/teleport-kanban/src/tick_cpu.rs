use anyhow::{Result, anyhow};
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use std::collections::VecDeque;
use tokio::time::sleep;

/// Internal Tick-Based CPU System
/// Implements a simple CPU architecture based on ADD, SUBTRACT, and WAIT operations
/// Provides precise timing control and deterministic execution for the BF16 teleport system
#[derive(Debug, Clone)]
pub struct TickCPU {
    /// Current tick counter
    pub tick_count: Arc<AtomicU64>,
    /// CPU clock speed in Hz (ticks per second)
    pub clock_speed: u64,
    /// Current instruction pointer
    pub instruction_pointer: Arc<AtomicU64>,
    /// CPU registers (16 general-purpose registers)
    pub registers: Arc<Vec<AtomicU64>>,
    /// Memory space (64KB)
    pub memory: Arc<Vec<AtomicU64>>,
    /// Instruction queue for batch processing
    pub instruction_queue: Arc<std::sync::Mutex<VecDeque<Instruction>>>,
    /// Running state
    pub running: Arc<AtomicBool>,
    /// Halt state
    pub halted: Arc<AtomicBool>,
    /// Tick interval in nanoseconds
    pub tick_interval: Duration,
    /// Statistics tracking
    pub stats: Arc<std::sync::Mutex<CPUStats>>,
}

#[derive(Debug, Clone)]
pub enum Instruction {
    /// ADD register, value - Add value to register
    Add(u8, u64),
    /// SUB register, value - Subtract value from register
    Sub(u8, u64),
    /// WAIT ticks - Wait for specified number of ticks
    Wait(u64),
    /// LOAD register, address - Load memory into register
    Load(u8, u16),
    /// STORE register, address - Store register to memory
    Store(u8, u16),
    /// JUMP address - Jump to instruction address
    Jump(u64),
    /// JUMP_IF_ZERO register, address - Jump if register is zero
    JumpIfZero(u8, u64),
    /// HALT - Stop CPU execution
    Halt,
    /// NOP - No operation
    Nop,
}

#[derive(Debug, Clone)]
pub struct CPUStats {
    pub total_ticks: u64,
    pub instructions_executed: u64,
    pub add_operations: u64,
    pub subtract_operations: u64,
    pub wait_operations: u64,
    pub memory_operations: u64,
    pub jump_operations: u64,
    pub last_execution_time: Option<Duration>,
    pub average_execution_time: Duration,
}

impl Default for CPUStats {
    fn default() -> Self {
        Self {
            total_ticks: 0,
            instructions_executed: 0,
            add_operations: 0,
            subtract_operations: 0,
            wait_operations: 0,
            memory_operations: 0,
            jump_operations: 0,
            last_execution_time: None,
            average_execution_time: Duration::ZERO,
        }
    }
}

impl TickCPU {
    /// Create a new TickCPU with specified clock speed
    pub fn new(clock_speed_hz: u64) -> Self {
        Self {
            tick_count: Arc::new(AtomicU64::new(0)),
            clock_speed: clock_speed_hz,
            instruction_pointer: Arc::new(AtomicU64::new(0)),
            registers: Arc::new((0..16).map(|_| AtomicU64::new(0)).collect()),
            memory: Arc::new((0..65536).map(|_| AtomicU64::new(0)).collect()),
            instruction_queue: Arc::new(std::sync::Mutex::new(VecDeque::new())),
            running: Arc::new(AtomicBool::new(false)),
            halted: Arc::new(AtomicBool::new(false)),
            tick_interval: Duration::from_nanos(1_000_000_000 / clock_speed_hz),
            stats: Arc::new(std::sync::Mutex::new(CPUStats::default())),
        }
    }

    /// Start the CPU execution loop
    pub async fn start(&self) -> Result<()> {
        self.running.store(true, Ordering::SeqCst);
        self.halted.store(false, Ordering::SeqCst);
        
        log::info!("TickCPU started with clock speed {} Hz", self.clock_speed);

        let mut last_tick = Instant::now();
        
        while self.running.load(Ordering::SeqCst) && !self.halted.load(Ordering::SeqCst) {
            let now = Instant::now();
            let elapsed = now - last_tick;

            if elapsed >= self.tick_interval {
                self.execute_tick().await?;
                last_tick = now;
            }

            // Small delay to prevent CPU spinning
            sleep(Duration::from_nanos(100)).await;
        }

        Ok(())
    }

    /// Stop the CPU execution
    pub fn stop(&self) {
        self.running.store(false, Ordering::SeqCst);
        log::info!("TickCPU stopped");
    }

    /// Halt the CPU execution
    pub fn halt(&self) {
        self.halted.store(true, Ordering::SeqCst);
        self.running.store(false, Ordering::SeqCst);
        log::info!("TickCPU halted");
    }

    /// Execute a single tick
    async fn execute_tick(&self) -> Result<()> {
        let tick = self.tick_count.fetch_add(1, Ordering::SeqCst);
        
        // Execute instruction if available
        if let Some(instruction) = self.fetch_instruction() {
            let start_time = Instant::now();
            self.execute_instruction(instruction).await?;
            let execution_time = start_time.elapsed();

            // Update statistics
            let mut stats = self.stats.lock().unwrap();
            stats.total_ticks = tick;
            stats.instructions_executed += 1;
            stats.last_execution_time = Some(execution_time);
            
            if stats.instructions_executed > 1 {
                let total_ns = stats.average_execution_time.as_nanos() * (stats.instructions_executed as u128 - 1) + execution_time.as_nanos();
                stats.average_execution_time = Duration::from_nanos((total_ns / stats.instructions_executed as u128) as u64);
            } else {
                stats.average_execution_time = execution_time;
            }
        }

        Ok(())
    }

    /// Fetch next instruction from queue
    fn fetch_instruction(&self) -> Option<Instruction> {
        let mut queue = self.instruction_queue.lock().unwrap();
        queue.pop_front()
    }

    /// Execute a single instruction
    async fn execute_instruction(&self, instruction: Instruction) -> Result<()> {
        match instruction {
            Instruction::Add(register, value) => {
                self.execute_add(register, value).await?;
            },
            Instruction::Sub(register, value) => {
                self.execute_sub(register, value).await?;
            },
            Instruction::Wait(ticks) => {
                self.execute_wait(ticks).await?;
            },
            Instruction::Load(register, address) => {
                self.execute_load(register, address).await?;
            },
            Instruction::Store(register, address) => {
                self.execute_store(register, address).await?;
            },
            Instruction::Jump(address) => {
                self.execute_jump(address).await?;
            },
            Instruction::JumpIfZero(register, address) => {
                self.execute_jump_if_zero(register, address).await?;
            },
            Instruction::Halt => {
                self.halt();
            },
            Instruction::Nop => {
                // No operation
            },
        }
        Ok(())
    }

    /// Execute ADD instruction: register = register + value
    async fn execute_add(&self, register: u8, value: u64) -> Result<()> {
        if register >= 16 {
            return Err(anyhow!("Invalid register: {}", register));
        }

        let reg_ptr = &self.registers[register as usize];
        let current = reg_ptr.load(Ordering::SeqCst);
        let result = current.wrapping_add(value);
        reg_ptr.store(result, Ordering::SeqCst);

        let mut stats = self.stats.lock().unwrap();
        stats.add_operations += 1;

        log::debug!("ADD R{}: {} + {} = {}", register, current, value, result);
        Ok(())
    }

    /// Execute SUB instruction: register = register - value
    async fn execute_sub(&self, register: u8, value: u64) -> Result<()> {
        if register >= 16 {
            return Err(anyhow!("Invalid register: {}", register));
        }

        let reg_ptr = &self.registers[register as usize];
        let current = reg_ptr.load(Ordering::SeqCst);
        let result = current.wrapping_sub(value);
        reg_ptr.store(result, Ordering::SeqCst);

        let mut stats = self.stats.lock().unwrap();
        stats.subtract_operations += 1;

        log::debug!("SUB R{}: {} - {} = {}", register, current, value, result);
        Ok(())
    }

    /// Execute WAIT instruction: wait for specified ticks
    async fn execute_wait(&self, ticks: u64) -> Result<()> {
        let start_tick = self.tick_count.load(Ordering::SeqCst);
        let target_tick = start_tick + ticks;

        while self.tick_count.load(Ordering::SeqCst) < target_tick {
            sleep(Duration::from_nanos(100)).await;
        }

        let mut stats = self.stats.lock().unwrap();
        stats.wait_operations += 1;

        log::debug!("WAIT: waited for {} ticks", ticks);
        Ok(())
    }

    /// Execute LOAD instruction: register = memory[address]
    async fn execute_load(&self, register: u8, address: u16) -> Result<()> {
        if register >= 16 {
            return Err(anyhow!("Invalid register: {}", register));
        }
        if address > 65535 {
            return Err(anyhow!("Invalid memory address: {}", address));
        }

        let value = self.memory[address as usize].load(Ordering::SeqCst);
        self.registers[register as usize].store(value, Ordering::SeqCst);

        let mut stats = self.stats.lock().unwrap();
        stats.memory_operations += 1;

        log::debug!("LOAD R{} <- M[{}]: {}", register, address, value);
        Ok(())
    }

    /// Execute STORE instruction: memory[address] = register
    async fn execute_store(&self, register: u8, address: u16) -> Result<()> {
        if register >= 16 {
            return Err(anyhow!("Invalid register: {}", register));
        }
        if address > 65535 {
            return Err(anyhow!("Invalid memory address: {}", address));
        }

        let value = self.registers[register as usize].load(Ordering::SeqCst);
        self.memory[address as usize].store(value, Ordering::SeqCst);

        let mut stats = self.stats.lock().unwrap();
        stats.memory_operations += 1;

        log::debug!("STORE M[{}] <- R{}: {}", address, register, value);
        Ok(())
    }

    /// Execute JUMP instruction: instruction_pointer = address
    async fn execute_jump(&self, address: u64) -> Result<()> {
        self.instruction_pointer.store(address, Ordering::SeqCst);
        
        let mut stats = self.stats.lock().unwrap();
        stats.jump_operations += 1;

        log::debug!("JUMP: instruction pointer set to {}", address);
        Ok(())
    }

    /// Execute JUMP_IF_ZERO instruction: if register == 0 then jump
    async fn execute_jump_if_zero(&self, register: u8, address: u64) -> Result<()> {
        if register >= 16 {
            return Err(anyhow!("Invalid register: {}", register));
        }

        let value = self.registers[register as usize].load(Ordering::SeqCst);
        
        if value == 0 {
            self.instruction_pointer.store(address, Ordering::SeqCst);
            
            let mut stats = self.stats.lock().unwrap();
            stats.jump_operations += 1;

            log::debug!("JUMP_IF_ZERO R{} == 0: jumped to {}", register, address);
        } else {
            log::debug!("JUMP_IF_ZERO R{} != 0: no jump", register);
        }
        
        Ok(())
    }

    /// Add instruction to the queue
    pub fn queue_instruction(&self, instruction: Instruction) {
        let mut queue = self.instruction_queue.lock().unwrap();
        queue.push_back(instruction);
    }

    /// Add multiple instructions to the queue
    pub fn queue_instructions(&self, instructions: Vec<Instruction>) {
        let mut queue = self.instruction_queue.lock().unwrap();
        for instruction in instructions {
            queue.push_back(instruction);
        }
    }

    /// Clear the instruction queue
    pub fn clear_queue(&self) {
        let mut queue = self.instruction_queue.lock().unwrap();
        queue.clear();
    }

    /// Get current register value
    pub fn get_register(&self, register: u8) -> Result<u64> {
        if register >= 16 {
            return Err(anyhow!("Invalid register: {}", register));
        }
        Ok(self.registers[register as usize].load(Ordering::SeqCst))
    }

    /// Set register value
    pub fn set_register(&self, register: u8, value: u64) -> Result<()> {
        if register >= 16 {
            return Err(anyhow!("Invalid register: {}", register));
        }
        self.registers[register as usize].store(value, Ordering::SeqCst);
        Ok(())
    }

    /// Get memory value
    pub fn get_memory(&self, address: u16) -> Result<u64> {
        if address > 65535 {
            return Err(anyhow!("Invalid memory address: {}", address));
        }
        Ok(self.memory[address as usize].load(Ordering::SeqCst))
    }

    /// Set memory value
    pub fn set_memory(&self, address: u16, value: u64) -> Result<()> {
        if address > 65535 {
            return Err(anyhow!("Invalid memory address: {}", address));
        }
        self.memory[address as usize].store(value, Ordering::SeqCst);
        Ok(())
    }

    /// Get current CPU statistics
    pub fn get_stats(&self) -> CPUStats {
        self.stats.lock().unwrap().clone()
    }

    /// Reset CPU statistics
    pub fn reset_stats(&self) {
        let mut stats = self.stats.lock().unwrap();
        *stats = CPUStats::default();
    }

    /// Get current tick count
    pub fn get_tick_count(&self) -> u64 {
        self.tick_count.load(Ordering::SeqCst)
    }

    /// Get current instruction pointer
    pub fn get_instruction_pointer(&self) -> u64 {
        self.instruction_pointer.load(Ordering::SeqCst)
    }

    /// Check if CPU is running
    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    /// Check if CPU is halted
    pub fn is_halted(&self) -> bool {
        self.halted.load(Ordering::SeqCst)
    }
}

/// High-level CPU operations for system integration
impl TickCPU {
    /// Execute a timing sequence for thermodynamic state transitions
    pub async fn execute_thermodynamic_sequence(&self) -> Result<()> {
        log::info!("Executing thermodynamic state transition sequence");
        
        // Sequence: Wait -> Add -> Wait -> Sub -> Wait
        self.queue_instructions(vec![
            Instruction::Wait(100),      // Wait 100 ticks
            Instruction::Add(0, 1),      // Increment state counter
            Instruction::Wait(50),       // Wait 50 ticks  
            Instruction::Sub(0, 1),      // Decrement state counter
            Instruction::Wait(25),       // Wait 25 ticks
            Instruction::Add(1, 10),     // Add to performance counter
        ]);

        // Wait for sequence completion
        while !self.instruction_queue.lock().unwrap().is_empty() {
            sleep(Duration::from_millis(10)).await;
        }

        log::info!("Thermodynamic sequence completed");
        Ok(())
    }

    /// Execute a timing sequence for compression operations
    pub async fn execute_compression_sequence(&self) -> Result<()> {
        log::info!("Executing compression timing sequence");
        
        // Load compression parameters into registers
        self.set_register(2, 1000)?;  // Compression timeout
        self.set_register(3, 50)?;   // Wait interval
        
        self.queue_instructions(vec![
            Instruction::Load(4, 100),     // Load compression level
            Instruction::Wait(10),         // Wait for system stabilization
            Instruction::Add(5, 1),        // Increment compression counter
            Instruction::Store(5, 200),    // Store compression result
            Instruction::JumpIfZero(4, 10), // Jump if compression level is zero
            Instruction::Wait(5),          // Wait before next operation
        ]);

        // Wait for completion
        while !self.instruction_queue.lock().unwrap().is_empty() {
            sleep(Duration::from_millis(5)).await;
        }

        log::info!("Compression sequence completed");
        Ok(())
    }

    /// Execute a safety monitoring sequence
    pub async fn execute_safety_sequence(&self) -> Result<()> {
        log::info!("Executing safety monitoring sequence");
        
        self.queue_instructions(vec![
            Instruction::Load(6, 300),     // Load temperature reading
            Instruction::Sub(6, 85),       // Subtract safe threshold
            Instruction::JumpIfZero(6, 20), // Jump if temperature is safe
            Instruction::Add(7, 1),        // Increment safety alert
            Instruction::Store(7, 400),    // Store safety status
            Instruction::Halt,             // Halt system if unsafe
        ]);

        // Monitor until completion or halt
        while self.is_running() && !self.is_halted() {
            if self.instruction_queue.lock().unwrap().is_empty() {
                break;
            }
            sleep(Duration::from_millis(1)).await;
        }

        log::info!("Safety sequence completed");
        Ok(())
    }

    /// Create a timing loop for continuous monitoring
    pub async fn create_monitoring_loop(&self, duration_ms: u64) -> Result<()> {
        let start_time = Instant::now();
        let duration = Duration::from_millis(duration_ms);
        
        log::info!("Starting monitoring loop for {}ms", duration_ms);
        
        while start_time.elapsed() < duration {
            // Execute monitoring cycle
            self.queue_instruction(Instruction::Add(8, 1));  // Increment cycle counter
            self.queue_instruction(Instruction::Wait(10));   // Wait between cycles
            
            // Process current instructions
            while !self.instruction_queue.lock().unwrap().is_empty() {
                sleep(Duration::from_millis(1)).await;
            }
            
            sleep(Duration::from_millis(100)).await;  // Main loop delay
        }
        
        log::info!("Monitoring loop completed");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_tick_cpu_basic_operations() {
        let cpu = TickCPU::new(1000); // 1kHz clock
        
        // Test register operations
        cpu.set_register(0, 100).unwrap();
        assert_eq!(cpu.get_register(0).unwrap(), 100);
        
        cpu.queue_instruction(Instruction::Add(0, 50));
        cpu.queue_instruction(Instruction::Sub(0, 25));
        
        // Execute instructions
        cpu.start().await.unwrap();
        
        // Give time for execution
        sleep(Duration::from_millis(10)).await;
        cpu.stop();
        
        assert_eq!(cpu.get_register(0).unwrap(), 125);
    }

    #[tokio::test]
    async fn test_tick_cpu_memory_operations() {
        let cpu = TickCPU::new(1000);
        
        // Test memory operations
        cpu.set_memory(100, 42).unwrap();
        assert_eq!(cpu.get_memory(100).unwrap(), 42);
        
        cpu.queue_instruction(Instruction::Load(1, 100));
        cpu.queue_instruction(Instruction::Store(1, 200));
        
        cpu.start().await.unwrap();
        sleep(Duration::from_millis(10)).await;
        cpu.stop();
        
        assert_eq!(cpu.get_memory(200).unwrap(), 42);
    }

    #[tokio::test]
    async fn test_tick_cpu_timing() {
        let cpu = TickCPU::new(100); // 100Hz clock (10ms per tick)
        
        let start_time = Instant::now();
        
        cpu.queue_instruction(Instruction::Wait(10)); // Wait 10 ticks = 100ms
        
        cpu.start().await.unwrap();
        
        // Wait for completion
        while !cpu.instruction_queue.lock().unwrap().is_empty() {
            sleep(Duration::from_millis(1)).await;
        }
        
        cpu.stop();
        
        let elapsed = start_time.elapsed();
        assert!(elapsed >= Duration::from_millis(95)); // Allow some tolerance
        assert!(elapsed <= Duration::from_millis(150));
    }

    #[test]
    fn test_cpu_stats() {
        let cpu = TickCPU::new(1000);
        
        // Execute some operations
        cpu.queue_instruction(Instruction::Add(0, 1));
        cpu.queue_instruction(Instruction::Sub(0, 1));
        cpu.queue_instruction(Instruction::Nop);
        
        // Get initial stats
        let stats = cpu.get_stats();
        assert_eq!(stats.instructions_executed, 0);
        
        // Reset stats
        cpu.reset_stats();
        let stats = cpu.get_stats();
        assert_eq!(stats.total_ticks, 0);
        assert_eq!(stats.instructions_executed, 0);
    }
}