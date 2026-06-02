# Adversarial Review: Self-Adapting Compute Fabric

I'm going to be brutally direct about what won't work, what's over-engineered,
and what's actually implementable right now. No sugar-coating.

---

## 1. The Aspirational Gap Is Your Real Problem

Your repo has three layers of reality:

| Layer | What | Accuracy |
|-------|------|----------|
| `k3s-flake/` | Desired NixOS architecture | **60% fiction** |
| Deployed cluster | What actually runs | **Known, works** |
| `self-adapting-compute-fabric.md` | Future vision | **90% fiction** |

You just wrote a 17KB design doc for a self-healing distributed compute fabric
when your **edge VPS doesn't even have SSH access** and the kubelet breaks on
restart. The foundation isn't solid enough for this house.

**Verdict**: Premature abstraction. Fix the six things that break today before
designing for a future that assumes they don't.

---

## 2. The Bootstrap Agent Can't Run "Once and Exit"

> "A single-shot agent that runs on every node at first boot. Runs once, exits."

This is naive:

- **Nodes reboot**. When racknerd restarts and the k3s-agent starts before
  Tailscale has an IP, it registers with the wrong address. Your "run once"
  agent is long gone.
- **k3s tokens expire or change**. The agent ran at first boot, but now the
  cluster token was rotated. The node can't rejoin.
- **Hardware changes**. A GPU gets replaced. The agent that ran at first boot
  has stale capability data. There's no daemon to re-detect.
- **CachyOS nftables reset on kernel update**. The nftables fix needs to re-apply
  after every kernel update. Your agent ran once and exited.

**Fix**: The bootstrap agent needs a **watchdog companion** — a small systemd
timer that runs `detect_and_report.py` every 5 minutes and re-applies fixes
if they've drifted. Or fold the detection into the k3s-agent's startup.

---

## 3. The Adaptive Scheduler Doesn't Work Like You Think

> "Scheduler picks the best node AT CALL TIME"
> `ray.get(assignment.execute.remote(data))`

This is not how Ray works. You can't do this:

```python
assignment = scheduler.select_worker(requirement)
return ray.get(assignment.execute.remote(data))
```

`assignment.execute` would need to be a reference to a function ON a specific
worker node. Ray doesn't let you dynamically dispatch a task to an arbitrary
node by name at call time — that's not how the distributed scheduler works.

**What Ray actually does**:
- `@ray.remote` tasks are scheduled by Ray's internal planner, not your code
- You can use `ray.remote(resources={...})` to constrain placement
- You can use placement groups for topology awareness
- You can't say "run this exact function on qfox-1" without node-level
  resource constraints that are set at task definition time, not call time

**What you should actually do**: Define one `@ray.remote` per tier with
the right `num_gpus`/`num_cpus` resources, and let Ray's built-in scheduler
handle placement. Your `AdaptiveScheduler` becomes a thin wrapper that:
1. Tries submitting to the highest tier
2. If it fails (no capacity), tries the next tier
3. Falls back to BATCH/WASM if all local tiers are saturated

This is `try/except` over `@ray.remote`, not dynamic dispatch.

---

## 4. The FrameDispatcher Is Not Distributed

Your current FrameDispatcher:

```python
class FrameDispatcher:
    def dispatch(self, tag, flags, seq, payload):
        backend = self.backends[tag]
        return backend.compute(tag, payload)
```

This is a synchronous Python function running in **a single process on qfox-1**.
It calls subprocesses (FFmpeg, PipeWire, etc.) on the local machine.

The "Ray integration" (`ray_vcn_bridge.py`) wraps this with `@ray.remote`
decorators, but it's never actually been run in production. The `python3 -m
py_compile` check only validates syntax, not logic.

**The 6-tier degradation table** assumes the FrameDispatcher already routes
through the Adaptive Scheduler. It doesn't. The FrameDispatcher routes through
a dict lookup in a Python process you started manually in a terminal.

**Fix before you design**: Make `dispatch()` actually go through the scheduler.
Today it goes through `self.backends[tag]`. Change it to go through
`self.scheduler.select_worker(tag)`. Then the degradation actually works.

---

## 5. The Edge Caddy Is Your Single Point of Failure

| Fact | Problem |
|------|---------|
| No SSH access to racknerd | Can't deploy config changes |
| kubelet breaks on restart | Can't run pods to fix it |
| Config is manually maintained | Port-registry.sh can't push to it |
| DNS TTL is 5 minutes | Even if you fix it, the whole domain goes dark for 5 min |

Your "port-registry.sh" design assumes you can push the generated config to
racknerd. How? The only working method we found was a privileged pod with
hostPath mount — and that only works if the kubelet isn't broken.

**The edge adapter should not depend on racknerd**. Design it so the edge
can be ANY machine with Caddy + Tailscale, including a new one if racknerd
dies. The bootstrap agent should install Caddy and configure it automatically.
The edge should be cattle, not a pet.

---

## 6. The Capability Registry Is a SPOF

You propose Trailbase (Postgres-compatible, in the `media` namespace) as the
backing store. If Trailbase goes down:

- No node can register
- The scheduler has no data to plan with
- New nodes appear invisible
- The health monitor can't track heartbeats

Trailbase itself runs on a single pod with a PVC. If that node goes down,
the registry goes down with it.

**Fix**: Use the k3s API itself as the registry. Node labels ARE the
capability registry. You don't need a separate database:

```bash
# Node labels already capture everything you need:
kubectl get nodes -L topology.researchstack.io/tier,topology.researchstack.io/gpu

# Custom resources can be read from the k8s API:
kubectl get node qfox-1 -o json | jq '.metadata.labels'
```

The k8s API is HA (etcd-backed), already replicated, and you can't kill it
without killing the whole cluster. Write capability data into node annotations
and labels. This eliminates the registry as a separate service.

---

## 7. Ray Head on steamdeck = No HA

Your Ray head is pinned to `steamdeck` via `nodeSelector`. When steamdeck
goes offline:

1. Ray head dies
2. All workers disconnect
3. All in-flight tasks are lost
4. The Adaptive Scheduler (also on the head) is gone
5. The Health Monitor (proposed as a Deployment) might survive, but it has
   nothing to monitor

**The self-adapting fabric cannot adapt to losing its own brain.**

**Fix at minimum**: Don't pin the Ray head to a single node. Use a Deployment
with anti-affinity, or at least have a backup head on another node. Or accept
that Ray availability equals single-node availability and document it honestly.

---

## 8. NodePort Allocation Is Wild-West

There are 20+ NodePort services with manually assigned ports. Nothing
prevents collisions. When a new service gets deployed with `nodePort: auto`,
k3s picks a random port in 30000-32768 that happens to be free AT THAT MOMENT.
If another service was added between your deploy and now, it collides (we saw
this with 30080, 30081, 30082 during Traefik install).

Your `port-registry.sh` can document the current allocations, but it can't
prevent future collisions. The Traefik install failure proved this.

**Fix**: Either:
1. Manage NodePorts centrally in a single YAML file with explicit ports
2. Or stop using NodePorts entirely — use ClusterIP + Traefik Ingress as the
   sole entry point (this requires fixing nixos:80)
3. Or write a `port-allocator` admission webhook that checks for conflicts

---

## 9. BATCH and WASM Tiers Are Handwaved

> "When all local tiers saturated: deploy BATCH workers (GitHub Actions)"

This sounds good but:

- **GitHub Actions has no inbound networking**. You can't dispatch work TO
  a GitHub Actions runner. The runner has to pull work from somewhere. Where?
- **Cloudflare Workers can't do GPU compute**. The WASM tier can do trinary
  ops on 512-byte payloads. That's it. No FFmpeg, no CUDA, no audio DSP.
- **How does work get TO these tiers?** The FrameDispatcher is a synchronous
  Python call. You can't call `dispatch()` and have it magically appear in a
  GitHub Actions workflow 30 seconds later.
- **Latency**. BATCH tier has 5-hour timeout. If your compute fabric is
  designed for "rapid adaptation," waiting 5 hours for a result isn't rapid.

**If you need async compute**: Deploy a job queue (Redis + Celery, or just
Ray's built-in object store) that workers pull from. GitHub Actions can
poll a REST endpoint. Cloudflare Workers can receive webhooks. But none of
this is in the design.

---

## 10. The Design Has No MVP

The spec describes 6 components, 4 phases, 8 sessions. That's a 2-3 week
project assuming nothing goes wrong. Here's what you can build in **one
session** that actually improves things:

### The Real MVP

```
One session, three files:
  1. shim/node_watchdog.py     — runs every 5 min via systemd timer
     - Re-detects hardware
     - Updates k3s node labels with current capabilities
     - Re-applies nftables fix if missing
     - Reports to health endpoint

  2. shim/nodepool_watcher.py  — runs as k3s Deployment
     - Watches node labels for changes
     - Auto-scales Ray worker groups (up/down) based on available nodes
     - Updates port-registry ConfigMap with current NodePorts

  3. scripts/port-registry.sh  — runnable script
     - Dumps all NodePort allocations as a Caddy-compatible config
     - Detects conflicts
```

That's it. Three files. No Trailbase dependency, no new databases, no
distributed scheduler, no cloud tier integration. It uses what you already
have: node labels, k3s API, RayCluster CRD, and a shell script.

The self-adapting fabric evolves from these three primitives. Everything
else (tier fallback, cloud tiers, adaptive scheduler) comes AFTER these
work reliably for a week.

---

## Summary of Adversarial Findings

| # | Claim | Reality | Severity |
|---|-------|---------|----------|
| 1 | Bootstrap runs once | Nodes reboot, need re-detection | 🔴 HIGH |
| 2 | Scheduler picks node at call time | Ray doesn't work that way | 🔴 HIGH |
| 3 | FrameDispatcher is distributed | It's a single Python process | 🔴 HIGH |
| 4 | Edge config can be auto-updated | No SSH, kubelet breaks | 🔴 HIGH |
| 5 | Capability Registry in Trailbase | SPOF, k8s labels already have this | 🟡 MED |
| 6 | Ray head is HA | Pinned to steamdeck, single-failure kills everything | 🟡 MED |
| 7 | NodePorts are managed | No central allocation, collision-prone | 🟡 MED |
| 8 | BATCH/WASM tiers are ready | GH Actions has no inbound; Workers too limited | 🟡 MED |
| 9 | Self-adapting fabric (design) | 90% aspirational, no MVP, too much architecture | 🟡 MED |
| 10 | Can implement in one session | No — 8 sessions minimum for the full design | 🟢 LOW |
