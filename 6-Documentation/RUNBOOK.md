# Ops Runbook — Research Stack

**Last updated:** 2026-05-29

Quick-reference operational procedures for k3s, FPGA, Tailscale, GPU, and DNS.

---

## k3s Cluster

### Start / Stop

```bash
# Set kubeconfig
export KUBECONFIG=/tmp/researchstack-kubeconfig.yaml

# Check cluster status
kubectl get nodes
kubectl get pods -A
```

**Control plane (nixos):**
```bash
# Restart k3s server
sudo systemctl restart k3s

# Check k3s server health
sudo systemctl status k3s
sudo journalctl -u k3s -f --lines=50
```

### Check Health

```bash
# All nodes ready
kubectl get nodes -o wide

# All pods running (any namespace)
kubectl get pods -A --field-selector='status.phase!=Running,status.phase!=Succeeded'

# Specific namespace
kubectl get pods -n services
kubectl get pods -n media
kubectl get pods -n monitoring
kubectl get pods -n ai-models
```

### Restart Pods

```bash
# Restart a deployment (rolling restart)
kubectl rollout restart deployment/<name> -n <namespace>

# Examples
kubectl rollout restart deployment/homer -n services
kubectl rollout restart deployment/ollama -n ai-models
kubectl rollout restart deployment/cluster-dashboard -n monitoring

# Force delete stuck pod
kubectl delete pod <pod-name> -n <namespace> --grace-period=0 --force
```

### View Logs

```bash
# Pod logs
kubectl logs <pod-name> -n <namespace> --tail=100 -f

# Previous container (if crashed)
kubectl logs <pod-name> -n <namespace> --previous

# All pods matching label
kubectl logs -l app=<label> -n <namespace> --tail=50
```

### Common Pods

| Namespace | Service | Deployment Name |
|-----------|---------|-----------------|
| `services` | Homer | `homer` |
| `services` | Hermes | `hermes` |
| `services` | Actual Budget | `actual-budget` |
| `services` | Uptime Kuma | `uptime-kuma` |
| `services` | Vaultwarden | `vaultwarden` |
| `services` | Authentik | `authentik` |
| `services` | Credential Server | `credential-server` |
| `services` | Registry API | `registry-api` |
| `services` | Jobs API | `jobs-api` |
| `services` | Blobs API | `blobs-api` |
| `ai-models` | Ollama | `ollama` |
| `monitoring` | Cluster Dashboard | `cluster-dashboard` |
| `media` | Jellyfin | `jellyfin` |
| `research` | AlphaProof | `alphaproof` |

---

## FPGA — Tang Nano 9K

### Flash Bitstream

```bash
# Build
cd 4-Infrastructure/hardware && bash build_research_stack.sh

# Flash via USB-JTAG
openFPGALoader -b tangnano9k research_stack_top.fs

# Verify flash
openFPGALoader -b tangnano9k --verify research_stack_top.fs
```

### Verify LEDs

After power-on, `led[0:5]` (pins 10-16) should show SUBLEQ state.
- **All off:** CPU halted or not clocked
- **Blinking:** CPU running (heartbeat)
- **LED 0 solid on:** CPU halted (trap)

### Debug UART

```bash
# Connect to UART TX (pin 17) via USB-serial adapter
# Baud rate: 115384 (27MHz / 234)
picocom -b 115384 /dev/ttyUSB0

# Or with screen
screen /dev/ttyUSB0 115384
```

### Run Simulation

```bash
cd /tmp/fpga_sim_full && ./obj_dir/sim_top
```

### Pin Reference

| Pin | Signal | Direction | Notes |
|-----|--------|-----------|-------|
| 52 | clk | input | 27 MHz oscillator |
| 4 | rst_n | input | Active-low reset (pull-up) |
| 3 | user_btn | input | Active-low (pull-up) |
| 10-16 | led[0:5] | output | LVCMOS18 |
| 17 | uart_tx | output | 115384 baud |
| 18 | uart_rx | input | Pull-up |

### FPGA Not Responding

1. Check USB connection to Tang Nano 9K
2. Verify `openFPGALoader` sees the device: `openFPGALoader --detect`
3. Re-flash bitstream: `openFPGALoader -b tangnano9k research_stack_top.fs`
4. Check clock: pin 52 should have 27 MHz (oscilloscope)
5. Assert reset: pull pin 4 low momentarily, then release
6. Check power: board should draw ~100mA from USB

---

## Tailscale

### Check Status

```bash
# Show tailnet status
tailscale status

# Show current node IP
tailscale ip

# Check connectivity to other nodes
tailscale ping qfox-1
tailscale ping 361395-1
tailscale ping racknerd-510bd9c
```

### Restart Funnel

The Funnel runs on `361395-1` and routes to Traefik NodePort 30080:

```bash
# On 361395-1 (edge node):
tailscale funnel 8080 off
tailscale funnel 8080

# Verify funnel URL
tailscale funnel status
```

### Debug Relay

```bash
# Check if relay is in use
tailscale status | grep relay

# Force direct connections (disable relay)
tailscale set --direct-peers-only=true

# Reset to default
tailscale set --direct-peers-only=false
```

### Re-authenticate

```bash
# On any node:
tailscale up --authkey=<TS_AUTH_KEY>

# Or interactive login
tailscale up
```

### Node IPs

| Node | Tailscale IP | Role |
|------|-------------|------|
| nixos | 100.102.173.61 | Control plane |
| qfox-1 | 100.88.57.96 | GPU worker |
| 361395-1 | 100.110.163.82 | Edge/Funnel |
| racknerd | 100.80.39.40 | Edge worker |
| steamdeck | 100.85.244.73 | Worker |

---

## GPU — QFox (RTX 4070)

### Check nvidia-smi

```bash
# GPU status
nvidia-smi

# Watch GPU utilization
nvidia-smi -l 1

# Check driver version
nvidia-smi --query-gpu=driver_version --format=csv,noheader
# Expected: 610.43
```

### Restart Ollama

```bash
# If running as k3s pod
kubectl rollout restart deployment/ollama -n ai-models
kubectl logs -l app=ollama -n ai-models --tail=20 -f

# If running as systemd service on qfox-1
sudo systemctl restart ollama
sudo journalctl -u ollama -f --tail=20
```

### Pull / Manage Models

```bash
# List loaded models
curl http://100.88.57.96:11434/api/tags

# Pull a model
curl http://100.88.57.96:11434/api/pull -d '{"name": "deepseek-coder-v2:16b"}'

# Test inference
curl http://100.88.57.96:11434/api/generate \
  -d '{"model": "deepseek-coder-v2:16b", "prompt": "Hello", "stream": false}'
```

### Ollama via NodePort

```bash
# Access from cluster
curl http://<any-node-ip>:31434/api/tags
```

---

## DNS & TLS

### Check LE Certificates

```bash
# Check cert expiry
echo | openssl s_client -connect researchstack.info:443 -servername researchstack.info 2>/dev/null | openssl x509 -noout -dates

# Wildcard cert
echo | openssl s_client -connect registry.researchstack.info:443 -servername registry.researchstack.info 2>/dev/null | openssl x509 -noout -dates
```

**Current cert valid until:** 2026-08-18

### Renew Certificates

Caddy auto-renews via Porkbun DNS-01. If manual renewal is needed:

```bash
# Restart Caddy to trigger renewal check
kubectl rollout restart deployment/caddy -n services

# Check Caddy logs for renewal
kubectl logs -l app=caddy -n services --tail=50 | grep -i renew
```

### Check Porkbun DNS

```bash
# Verify A record
dig researchstack.info +short
dig auth.researchstack.info +short
dig registry.researchstack.info +short

# Check API key (set PORKBUN_API_KEY env var)
curl -X POST https://api.porkbun.com/api/json/v3/ping \
  -H "Content-Type: application/json" \
  -d '{"apikey": "'$PORKBUN_API_KEY'"}'
```

---

## Common Failures

### Node Down

```bash
# Identify down node
kubectl get nodes

# Check node conditions
kubectl describe node <node-name>

# On the node itself:
sudo systemctl status k3s-agent    # worker nodes
sudo systemctl status k3s          # control plane

# Rejoin cluster if needed (worker):
sudo k3s agent --server https://100.102.173.61:6443 --token <TOKEN>
```

### Pod CrashLoopBackOff

```bash
# Check events
kubectl describe pod <pod-name> -n <namespace>

# Check logs (including previous crash)
kubectl logs <pod-name> -n <namespace> --previous --tail=100

# Common fixes:
# - ConfigMap/Secret missing: kubectl get configmap -n <ns>; kubectl get secret -n <ns>
# - Image pull error: check image tag and registry access
# - Resource limits: kubectl top pod -n <namespace>
# - OOMKill: increase memory limit in deployment spec
```

### FPGA Not Responding

1. Unplug and replug USB cable
2. Check `ls /dev/ttyUSB*` — device should appear
3. Re-flash: `openFPGALoader -b tangnano9k research_stack_top.fs`
4. If JTAG fails: try holding reset (pin 4 low) while plugging in
5. Check power LED on Tang Nano 9K board
6. Try different USB port / cable

### Tailscale Tunnel Down

```bash
# Check daemon
sudo systemctl status tailscaled

# Restart
sudo systemctl restart tailscaled
tailscale up

# Check if key expired
tailscale status | grep -i expir
```

### DNS Resolution Failing

```bash
# Check Caddy pod
kubectl logs -l app=caddy -n services --tail=50

# Test DNS from inside cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup researchstack.info

# Check Porkbun API key
kubectl get secret porkbun-credentials -n services -o jsonpath='{.data.api-key}' | base64 -d
```

---

## Escalation Matrix

| Issue | First Response | Escalation |
|-------|---------------|------------|
| Pod down | `kubectl rollout restart` | Check node, check resource limits |
| Node down | SSH to node, check `systemctl` | Reboot, check hardware |
| FPGA unresponsive | Re-flash bitstream | Check USB, try different board |
| Tailscale tunnel | `tailscale up` | Check auth key, restart daemon |
| DNS/cert | Restart Caddy | Check Porkbun API, check ingress |
| GPU errors | Check `nvidia-smi` | Restart driver, check PCIe seating |
| OOM on Ollama | Restart pod | Reduce context length, switch model |
