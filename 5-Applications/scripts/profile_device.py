#!/usr/bin/env python3
"""
Hardware Profiling Script for FoxTop Device

Profiles GPU, CPU, memory, and other hardware capabilities for exploitation
in distributed computing tasks.
"""
import subprocess
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DeviceProfiler")

def run_command(cmd, description):
    """Run a command and return the result."""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.warning(f"Command failed: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out: {description}")
        return None
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return None

def profile_cpu():
    """Profile CPU capabilities."""
    logger.info("=" * 60)
    logger.info("CPU PROFILING")
    logger.info("=" * 60)
    
    cpu_info = {}
    
    # CPU model
    cpu_info['model'] = run_command("cat /proc/cpuinfo | grep 'model name' | head -n 1", "CPU Model")
    
    # CPU cores
    cpu_info['cores'] = run_command("nproc", "CPU Cores")
    
    # CPU architecture
    cpu_info['architecture'] = run_command("uname -m", "CPU Architecture")
    
    # CPU frequency
    cpu_info['frequency'] = run_command("cat /proc/cpuinfo | grep 'cpu MHz' | head -n 1", "CPU Frequency")
    
    # CPU flags (features)
    cpu_info['flags'] = run_command("cat /proc/cpuinfo | grep 'flags' | head -n 1", "CPU Flags")
    
    return cpu_info

def profile_gpu():
    """Profile GPU capabilities."""
    logger.info("=" * 60)
    logger.info("GPU PROFILING")
    logger.info("=" * 60)
    
    gpu_info = {}
    
    # Check for NVIDIA GPU
    gpu_info['nvidia_smi'] = run_command("nvidia-smi --query-gpu=name,memory.total,driver_version,cuda_version --format=csv,noheader", "NVIDIA GPU Info")
    
    # Check for AMD GPU
    gpu_info['amd_gpu'] = run_command("rocm-smi --showid", "AMD GPU Info")
    
    # Check for Intel GPU
    gpu_info['intel_gpu'] = run_command("intel_gpu_top", "Intel GPU Info")
    
    # Check for general GPU info
    gpu_info['lspci_gpu'] = run_command("lspci | grep -i vga", "PCI GPU Devices")
    
    # Check for CUDA availability
    gpu_info['cuda_devices'] = run_command("python3 -c 'import torch; print(torch.cuda.device_count())' 2>/dev/null", "CUDA Device Count")
    
    # Check for PyTorch GPU support
    gpu_info['pytorch_gpu'] = run_command("python3 -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null", "PyTorch GPU Support")
    
    return gpu_info

def profile_memory():
    """Profile memory capabilities."""
    logger.info("=" * 60)
    logger.info("MEMORY PROFILING")
    logger.info("=" * 60)
    
    memory_info = {}
    
    # Total memory
    memory_info['total'] = run_command("free -h | grep Mem | awk '{print $2}'", "Total Memory")
    
    # Available memory
    memory_info['available'] = run_command("free -h | grep Mem | awk '{print $7}'", "Available Memory")
    
    # Swap memory
    memory_info['swap'] = run_command("free -h | grep Swap | awk '{print $2}'", "Swap Memory")
    
    return memory_info

def profile_storage():
    """Profile storage capabilities."""
    logger.info("=" * 60)
    logger.info("STORAGE PROFILING")
    logger.info("=" * 60)
    
    storage_info = {}
    
    # Disk space
    storage_info['disk'] = run_command("df -h | grep -E '^/dev/' | head -n 5", "Disk Space")
    
    # Disk type (SSD/HDD)
    storage_info['disk_type'] = run_command("lsblk -o NAME,ROTA | grep -v 'ROTA'", "Disk Type")
    
    # I/O scheduler
    storage_info['io_scheduler'] = run_command("cat /sys/block/sda/queue/scheduler 2>/dev/null || cat /sys/block/nvme0n1/queue/scheduler 2>/dev/null", "I/O Scheduler")
    
    return storage_info

def profile_network():
    """Profile network capabilities."""
    logger.info("=" * 60)
    logger.info("NETWORK PROFILING")
    logger.info("=" * 60)
    
    network_info = {}
    
    # Network interfaces
    network_info['interfaces'] = run_command("ip -br addr show", "Network Interfaces")
    
    # Network speed
    network_info['ethtool'] = run_command("ethtool $(ip route | grep default | awk '{print $5}') 2>/dev/null | grep Speed", "Network Speed")
    
    # Tailscale status
    network_info['tailscale'] = run_command("tailscale status --json 2>/dev/null | head -n 20", "Tailscale Status")
    
    return network_info

def profile_system():
    """Profile general system information."""
    logger.info("=" * 60)
    logger.info("SYSTEM PROFILING")
    logger.info("=" * 60)
    
    system_info = {}
    
    # OS
    system_info['os'] = run_command("cat /etc/os-release | grep PRETTY_NAME", "Operating System")
    
    # Kernel
    system_info['kernel'] = run_command("uname -r", "Kernel Version")
    
    # Uptime
    system_info['uptime'] = run_command("uptime -p", "System Uptime")
    
    # Load average
    system_info['load'] = run_command("cat /proc/loadavg", "Load Average")
    
    return system_info

def profile_exploitable_features():
    """Profile features that can be exploited for distributed computing."""
    logger.info("=" * 60)
    logger.info("EXPLOITABLE FEATURES PROFILING")
    logger.info("=" * 60)
    
    exploitable = {}
    
    # Docker availability
    exploitable['docker'] = run_command("docker --version", "Docker")
    
    # Docker GPU support
    exploitable['nvidia_docker'] = run_command("docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi 2>/dev/null", "NVIDIA Docker")
    
    # Kubernetes
    exploitable['kubernetes'] = run_command("kubectl version --client 2>/dev/null", "Kubernetes")
    
    # MPI
    exploitable['mpi'] = run_command("mpirun --version 2>/dev/null", "MPI")
    
    # OpenCL
    exploitable['opencl'] = run_command("clinfo 2>/dev/null | head -n 10", "OpenCL")
    
    # Vulkan
    exploitable['vulkan'] = run_command("vulkaninfo 2>/dev/null | head -n 10", "Vulkan")
    
    # Python packages
    exploitable['torch'] = run_command("python3 -c 'import torch; print(torch.__version__)' 2>/dev/null", "PyTorch")
    exploitable['tensorflow'] = run_command("python3 -c 'import tensorflow as tf; print(tf.__version__)' 2>/dev/null", "TensorFlow")
    exploitable['jax'] = run_command("python3 -c 'import jax; print(jax.__version__)' 2>/dev/null", "JAX")
    
    return exploitable

def main():
    """Main profiling function."""
    logger.info("Starting FoxTop Device Hardware Profiling")
    
    profile = {
        'system': profile_system(),
        'cpu': profile_cpu(),
        'gpu': profile_gpu(),
        'memory': profile_memory(),
        'storage': profile_storage(),
        'network': profile_network(),
        'exploitable': profile_exploitable_features()
    }
    
    logger.info("=" * 60)
    logger.info("PROFILE SUMMARY")
    logger.info("=" * 60)
    
    print(json.dumps(profile, indent=2))
    
    # Save to file
    with open('/tmp/foxtop_profile.json', 'w') as f:
        json.dump(profile, f, indent=2)
    
    logger.info("Profile saved to /tmp/foxtop_profile.json")

if __name__ == "__main__":
    main()
