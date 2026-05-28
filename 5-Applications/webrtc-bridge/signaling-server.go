package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

// Signaling message types exchanged over WebSocket.
type SignalMessage struct {
	Type     string                     `json:"type"` // "offer", "answer", "candidate"
	SDP      *webrtc.SessionDescription `json:"sdp,omitempty"`
	Candidate *webrtc.ICECandidateInit  `json:"candidate,omitempty"`
}

// HTTP request forwarded over the WebRTC data channel.
type HTTPRequest struct {
	ID      string            `json:"id"`
	Method  string            `json:"method"`
	Path    string            `json:"path"`
	Headers map[string]string `json:"headers"`
	Body    string            `json:"body"`
}

// HTTP response returned over the WebRTC data channel.
type HTTPResponse struct {
	ID      string            `json:"id"`
	Status  int               `json:"status"`
	Headers map[string]string `json:"headers"`
	Body    string            `json:"body"`
}

var (
	upgrader = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}
	// Target for proxied HTTP requests — Traefik ingress.
	proxyTarget = envOr("PROXY_TARGET", "http://100.102.173.61:30080")
)

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func main() {
	port := envOr("PORT", "8080")

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok","service":"webrtc-bridge"}`))
	})

	http.HandleFunc("/ws", handleWebSocket)

	// Serve the static client files.
	http.Handle("/", http.FileServer(http.Dir("/app/client")))

	log.Printf("WebRTC bridge signaling server starting on :%s (proxy target: %s)", port, proxyTarget)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}
	defer conn.Close()

	log.Printf("Client connected: %s", r.RemoteAddr)

	// Create a new RTCPeerConnection for this client.
	config := webrtc.Configuration{
		ICEServers: []webrtc.ICEServer{
			{URLs: []string{"stun:stun.l.google.com:19302"}},
			{URLs: []string{"stun:stun1.l.google.com:19302"}},
			{URLs: []string{"stun:stun2.l.google.com:19302"}},
		},
	}

	peerConnection, err := webrtc.NewPeerConnection(config)
	if err != nil {
		log.Printf("Failed to create PeerConnection: %v", err)
		return
	}
	defer peerConnection.Close()

	var dcOnce sync.Once
	// Handle incoming data channels from the client.
	peerConnection.OnDataChannel(func(dc *webrtc.DataChannel) {
		dcOnce.Do(func() {
			setupDataChannel(dc)
		})
	})

	// Send ICE candidates to the client.
	peerConnection.OnICECandidate(func(c *webrtc.ICECandidate) {
		if c == nil {
			return
		}
		candidate := c.ToJSON()
		msg := SignalMessage{
			Type:      "candidate",
			Candidate: &candidate,
		}
		conn.WriteJSON(msg)
	})

	// Log connection state changes.
	peerConnection.OnConnectionStateChange(func(state webrtc.PeerConnectionState) {
		log.Printf("PeerConnection state: %s", state.String())
	})

	// Read signaling messages from the WebSocket.
	for {
		_, raw, err := conn.ReadMessage()
		if err != nil {
			if websocket.IsCloseError(err, websocket.CloseNormalClosure, websocket.CloseGoingAway) {
				log.Printf("Client disconnected: %s", r.RemoteAddr)
			} else {
				log.Printf("WebSocket read error: %v", err)
			}
			return
		}

		var msg SignalMessage
		if err := json.Unmarshal(raw, &msg); err != nil {
			log.Printf("Invalid signaling message: %v", err)
			continue
		}

		switch msg.Type {
		case "offer":
			if msg.SDP == nil {
				log.Printf("Offer missing SDP")
				continue
			}
			if err := peerConnection.SetRemoteDescription(*msg.SDP); err != nil {
				log.Printf("SetRemoteDescription failed: %v", err)
				continue
			}

			answer, err := peerConnection.CreateAnswer(nil)
			if err != nil {
				log.Printf("CreateAnswer failed: %v", err)
				continue
			}
			if err := peerConnection.SetLocalDescription(answer); err != nil {
				log.Printf("SetLocalDescription failed: %v", err)
				continue
			}

			conn.WriteJSON(SignalMessage{
				Type: "answer",
				SDP:  &answer,
			})
			log.Printf("Sent SDP answer to %s", r.RemoteAddr)

		case "candidate":
			if msg.Candidate == nil {
				continue
			}
			if err := peerConnection.AddICECandidate(*msg.Candidate); err != nil {
				log.Printf("AddICECandidate failed: %v", err)
			}
		}
	}
}

func setupDataChannel(dc *webrtc.DataChannel) {
	dc.OnOpen(func() {
		log.Printf("Data channel opened: %s (id=%d)", dc.Label(), *dc.ID())
	})

	dc.OnClose(func() {
		log.Printf("Data channel closed: %s", dc.Label())
	})

	dc.OnMessage(func(msg webrtc.DataChannelMessage) {
		var req HTTPRequest
		if err := json.Unmarshal(msg.Data, &req); err != nil {
			log.Printf("Invalid data channel message: %v", err)
			return
		}

		go func() {
			resp := proxyRequest(&req)
			data, _ := json.Marshal(resp)
			dc.SendText(string(data))
		}()
	})
}

func proxyRequest(req *HTTPRequest) *HTTPResponse {
	start := time.Now()

	path := req.Path
	if path == "" {
		path = "/"
	}
	url := proxyTarget + path

	var body io.Reader
	if req.Body != "" {
		body = &readCloser{[]byte(req.Body)}
	}

	httpReq, err := http.NewRequest(req.Method, url, body)
	if err != nil {
		return &HTTPResponse{
			ID:     req.ID,
			Status: 502,
			Headers: map[string]string{"Content-Type": "application/json"},
			Body:   fmt.Sprintf(`{"error":"bad request: %s"}`, err.Error()),
		}
	}

	for k, v := range req.Headers {
		httpReq.Header.Set(k, v)
	}

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return &HTTPResponse{
			ID:     req.ID,
			Status: 502,
			Headers: map[string]string{"Content-Type": "application/json"},
			Body:   fmt.Sprintf(`{"error":"proxy error: %s"}`, err.Error()),
		}
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return &HTTPResponse{
			ID:     req.ID,
			Status: 502,
			Headers: map[string]string{"Content-Type": "application/json"},
			Body:   fmt.Sprintf(`{"error":"read body: %s"}`, err.Error()),
		}
	}

	headers := make(map[string]string)
	for k := range resp.Header {
		headers[k] = resp.Header.Get(k)
	}

	elapsed := time.Since(start)
	log.Printf("Proxy %s %s → %d (%s)", req.Method, req.Path, resp.Status, elapsed)

	return &HTTPResponse{
		ID:      req.ID,
		Status:  resp.StatusCode,
		Headers: headers,
		Body:    string(respBody),
	}
}

// readCloser wraps a byte slice as an io.ReadCloser.
type readCloser struct {
	data []byte
}

func (r *readCloser) Read(p []byte) (int, error) {
	if len(r.data) == 0 {
		return 0, io.EOF
	}
	n := copy(p, r.data)
	r.data = r.data[n:]
	return n, nil
}

func (r *readCloser) Close() error { return nil }
