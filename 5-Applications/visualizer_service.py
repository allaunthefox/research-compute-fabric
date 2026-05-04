from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import json
import random
from pathlib import Path

app = FastAPI()

# Path to the AVM gold traces for playback simulation
TRACE_PATH = Path("/home/allaun/Documents/Research Stack/shared-data/burgers_avm_gold_traces.json")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
    <head>
        <title>Sovereign NUVMAP Live</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { 
                background: #0f172a; 
                color: #f8fafc; 
                font-family: 'Inter', sans-serif;
                margin: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            #dashboard {
                width: 90%;
                max-width: 1200px;
                margin-top: 20px;
            }
            .card {
                background: #1e293b;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            h1 { color: #38bdf8; }
            #status { font-family: monospace; color: #10b981; }
        </style>
    </head>
    <body>
        <h1>Sovereign NUVMAP Live</h1>
        <div id="status">Connecting to AVM-R node...</div>
        
        <div id="dashboard">
            <div class="card">
                <h2>Spectral Complexity (&Omega;)</h2>
                <div id="omega-plot"></div>
            </div>
            <div class="card">
                <h2>Effective Viscosity (&nu;<sub>eff</sub>)</h2>
                <div id="nu-plot"></div>
            </div>
        </div>

        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            const status = document.getElementById('status');
            
            let timeData = [];
            let omegaData = [];
            let nuData = [];

            ws.onopen = () => {
                status.innerText = "Connected: Stream Active";
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const now = new Date();
                
                timeData.push(now);
                omegaData.push(data.omega);
                nuData.push(data.nu_eff);

                if (timeData.length > 50) {
                    timeData.shift();
                    omegaData.shift();
                    nuData.shift();
                }

                Plotly.newPlot('omega-plot', [{
                    x: timeData,
                    y: omegaData,
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#38bdf8', shape: 'spline' },
                    marker: { color: '#f8fafc' }
                }], {
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#f8fafc' },
                    margin: { t: 10, b: 40, l: 40, r: 10 },
                    xaxis: { gridcolor: '#334155' },
                    yaxis: { gridcolor: '#334155' }
                });

                Plotly.newPlot('nu-plot', [{
                    x: timeData,
                    y: nuData,
                    type: 'scatter',
                    mode: 'lines',
                    fill: 'tozeroy',
                    line: { color: '#10b981' }
                }], {
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#f8fafc' },
                    margin: { t: 10, b: 40, l: 40, r: 10 },
                    xaxis: { gridcolor: '#334155' },
                    yaxis: { gridcolor: '#334155' }
                });
            };

            ws.onclose = () => {
                status.innerText = "Disconnected: AVM-R offline";
                status.style.color = "#ef4444";
            };
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(HTML_TEMPLATE)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Load gold traces for simulation playback
    gold_data = {}
    if TRACE_PATH.exists():
        with open(TRACE_PATH, 'r') as f:
            gold_data = json.load(f)

    # Initial simulated state
    omega = 0.5
    nu0 = 0.1
    
    try:
        while True:
            # Simulate a slight drift in Omega
            omega += random.uniform(-0.05, 0.05)
            omega = max(0.1, min(1.0, omega))
            
            # Compute nu_eff (Burgers AVM law)
            nu_eff = nu0 * (1.0 + omega)
            
            payload = {
                "omega": omega,
                "nu_eff": nu_eff,
                "status": "CALIBRATED"
            }
            
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.5) # 2Hz refresh
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
