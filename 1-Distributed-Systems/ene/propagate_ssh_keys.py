import subprocess

nodes = ["architect", "judge", "768mb", "hutter", "netcup-router"]

with open("/home/allaun/.ssh/id_ed25519.pub", "r") as f:
    pub_key = f.read().strip()

print(f"Propagating public key: {pub_key[:20]}...")

for node in nodes:
    print(f"Targeting {node}...")
    # Use the hostname from .ssh/config which has the correct User and IdentityFile already
    cmd = f"ssh -o StrictHostKeyChecking=no {node} 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo {pub_key} >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            print(f"  ✅ Successfully pushed to {node}")
        else:
            print(f"  ❌ Failed for {node}: {res.stderr.strip()}")
    except Exception as e:
        print(f"  ⚠️  Timeout/Error for {node}: {str(e)}")
