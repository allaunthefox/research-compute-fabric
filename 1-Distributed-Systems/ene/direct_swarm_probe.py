import subprocess

# Using hostnames from ~/.ssh/config for correct User/Identity defaults
nodes = ["architect", "judge", "768mb", "hutter", "netcup-router"]

results = {}

for node in nodes:
    print(f"Direct Probing {node}...")
    cmd = f"ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no {node} 'echo CPU: $(nproc); echo MEM: $(free -h | grep Mem | awk \"{{print \\$2}}\"); echo GPU: $(nvidia-smi -L 2>/dev/null || echo None)'"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            results[node] = res.stdout.strip().split('\n')
        else:
            results[node] = f"Error: {res.stderr.strip()}"
    except Exception as e:
        results[node] = f"Timeout/Error: {str(e)}"

print("\n" + "="*50)
print("EMPRICAL SWARM RESOURCE REPORT (DIRECT PROBE)")
print("="*50)
for node, info in results.items():
    print(f"{node}: {info}")
