# WebRTC Bridge

Bypass Tailscale DERP relay latency for the Research Stack k3s cluster.

## Problem

Tailscale Funnel on node `361395-1` exposes Traefik at
`https://361395-1.tail4e7094.ts.net`, but Funnel traffic traverses DERP
relays, adding ~129 ms of latency per hop. For interactive workloads
(dashboards, shell, streaming) this is unacceptable.

## Solution

A lightweight WebRTC bridge that establishes a direct peer-to-peer data
channel between the browser client and the cluster node, bypassing DERP
entirely. After a one-time signaling exchange over WebSocket, all HTTP
traffic flows over the WebRTC data channel with sub-10 ms latency when
both peers have direct connectivity.

## Architecture

```
┌──────────────┐   WebSocket (signaling)   ┌───────────────────┐
│              │ ◄──────────────────────── │                   │
│   Browser    │   SDP offer/answer        │  Signaling Server │
│   Client     │   ICE candidates          │  (Go, port 8080)  │
│              │                           │  on 361395-1      │
│              │   WebRTC Data Channel     │                   │
│              │ ◄════════════════════════► │  HTTP proxy       │
│              │   (peer-to-peer)          │  → Traefik:30080  │
└──────────────┘                           └───────────────────┘
       │                                           │
       │  Direct P2P (UDP)                         │
       │  STUN for NAT traversal                   │
       │  No DERP relay!                           │
       ▼                                           ▼
  Client NAT                              Tailscale mesh
  (STUN resolves)                         (direct route)
```

### Components

| Component | Language | Port | Description |
|-----------|----------|------|-------------|
| `signaling-server.go` | Go | 8080 | WebSocket signaling + static file server |
| `client/index.html` | HTML/JS | — | Browser-side WebRTC client |
| `Containerfile` | — | — | Multi-stage Go build |
| `k8s/bridge.yaml` | YAML | — | k3s deployment manifests |

### Signaling Flow

1. Client opens WebSocket to `wss://361395-1.tail4e7094.ts.net/webrtc/ws`
2. Client creates `RTCPeerConnection` with public STUN servers
3. Client creates SDP offer, sends via WebSocket
4. Server receives offer, creates answer, sends back
5. ICE candidates exchanged over WebSocket
6. WebRTC data channel opens — signaling WebSocket may close
7. Client sends HTTP requests as JSON over the data channel
8. Server proxies requests to Traefik, returns responses

### Data Channel Protocol

Messages on the data channel are JSON-encoded HTTP request/response pairs:

**Request (client → server):**
```json
{
  "id": "req-uuid",
  "method": "GET",
  "path": "/api/v1/status",
  "headers": {"Accept": "application/json"},
  "body": ""
}
```

**Response (server → client):**
```json
{
  "id": "req-uuid",
  "status": 200,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"ok\": true}"
}
```

### NAT Traversal

- Uses public STUN servers (`stun:stun.l.google.com:19302`,
  `stun:stun1.l.google.com:19302`)
- The server runs on `361395-1` with `hostNetwork: true`, so its
  Tailscale IP `100.110.163.82` is directly reachable
- If STUN fails to resolve a direct path, the connection falls back to
  Tailscale's own NAT traversal (which is better than DERP for most cases)
- A TURN server can be added later if needed

## Deployment

### Build the container image

```bash
cd 5-Applications/webrtc-bridge
podman build -t localhost/webrtc-bridge:latest .
```

### Import into k3s

```bash
podman save localhost/webrtc-bridge:latest | ssh 361395-1 k3s ctr images import -
```

### Apply manifests

```bash
kubectl apply -f k8s/bridge.yaml
```

### Verify

```bash
kubectl -n edge get pods -l app=webrtc-bridge
curl -s https://361395-1.tail4e7094.ts.net/webrtc/health
```

## Access

Open `https://361395-1.tail4e7094.ts.net/webrtc/` in a browser. The client
will automatically connect via the signaling server, establish a WebRTC data
channel, and begin proxying HTTP requests.

## Future Work

- [ ] Add TURN server for symmetric NAT scenarios
- [ ] Multiplex multiple HTTP requests over a single data channel
- [ ] Add connection quality metrics (RTT, packet loss)
- [ ] Support WebSocket proxying through the data channel
- [ ] Add authentication (Tailscale identity headers)
