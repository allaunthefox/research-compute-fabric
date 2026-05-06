import express from "express";
import Database from "better-sqlite3";
import { join } from "path";
import fs from "fs";

const router = express.Router();

// Helper to get database connection
const getDb = () => {
  const dbPath = process.env.SUBSTRATE_INDEX_DB || join(process.cwd(), "data", "substrate_index.db");

  // Ensure directory exists
  const dbDir = join(dbPath, "..");
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  const db = new Database(dbPath);

  // Initialize table if it doesn't exist
  db.prepare(`
    CREATE TABLE IF NOT EXISTS ollama_models (
      model_id TEXT PRIMARY KEY,
      model_name TEXT NOT NULL,
      endpoint TEXT NOT NULL,
      provider TEXT DEFAULT 'Ollama Cloud',
      tag TEXT,
      description TEXT,
      created_at TEXT NOT NULL,
      is_active BOOLEAN DEFAULT TRUE
    )
  `).run();

  return db;
};

// GET /workspace/models/create
router.get("/models/create", (req, res) => {
  res.send(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Model | Research Stack</title>
    <link rel="stylesheet" href="/css/index.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Create Model</h1>
            <p class="subtitle">Provision a new Ollama Cloud model instance.</p>

            <form id="modelForm">
                <div class="form-group">
                    <label for="modelName">Model Name</label>
                    <input type="text" id="modelName" name="modelName" placeholder="e.g. llama3:8b-instruct" required>
                </div>

                <div class="form-group">
                    <label for="endpoint">Cloud Endpoint</label>
                    <input type="url" id="endpoint" name="endpoint" placeholder="https://api.ollama.cloud" required>
                </div>

                <div class="form-group">
                    <label for="tag">Metatype Tag</label>
                    <input type="text" id="tag" name="tag" placeholder="e.g. #formal-logic">
                </div>

                <div class="form-group">
                    <label for="description">Purpose / Rationale</label>
                    <textarea id="description" name="description" rows="3" placeholder="Describe the intended research domain..."></textarea>
                </div>

                <div id="status" class="status-msg"></div>

                <div class="btn-group">
                    <button type="button" id="testBtn" style="background: rgba(255,255,255,0.1); margin-bottom: 1rem; box-shadow: none; border: 1px solid rgba(255,255,255,0.1);">
                        Test Connection
                    </button>
                    <button type="submit" id="submitBtn">
                        <span class="btn-text">Initialize Substrate</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        const form = document.getElementById('modelForm');
        const status = document.getElementById('status');
        const submitBtn = document.getElementById('submitBtn');
        const testBtn = document.getElementById('testBtn');

        testBtn.addEventListener('click', async () => {
            const endpoint = document.getElementById('endpoint').value;
            if (!endpoint) {
                status.className = 'status-msg error';
                status.textContent = 'Please enter an endpoint first.';
                return;
            }

            testBtn.disabled = true;
            testBtn.innerHTML = 'Testing...';

            try {
                const response = await fetch('/workspace/models/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ endpoint })
                });
                const result = await response.json();
                if (result.ok) {
                    status.className = 'status-msg success';
                    status.textContent = 'Connection successful: ' + result.message;
                } else {
                    status.className = 'status-msg error';
                    status.textContent = 'Connection failed: ' + result.error;
                }
            } catch (err) {
                status.className = 'status-msg error';
                status.textContent = 'Network error testing endpoint.';
            } finally {
                testBtn.disabled = false;
                testBtn.innerHTML = 'Test Connection';
            }
        });

        form.addEventListener('submit', async (e) => {

            e.preventDefault();

            status.className = 'status-msg';
            status.textContent = '';
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Initializing...';

            const formData = {
                modelName: document.getElementById('modelName').value,
                endpoint: document.getElementById('endpoint').value,
                tag: document.getElementById('tag').value,
                description: document.getElementById('description').value
            };

            try {
                const response = await fetch('/workspace/models/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (result.ok) {
                    status.className = 'status-msg success';
                    status.textContent = 'Model successfully provisioned in ENE Substrate.';
                    form.reset();
                } else {
                    status.className = 'status-msg error';
                    status.textContent = 'Error: ' + (result.error || 'Failed to create model');
                }
            } catch (err) {
                status.className = 'status-msg error';
                status.textContent = 'Network error. Please verify the Research Stack server is running.';
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Initialize Substrate';
            }
        });
    </script>
</body>
</html>
  `);
});

// POST /workspace/models/test
router.post("/models/test", async (req, res) => {
  try {
    const { endpoint } = req.body;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${endpoint}/api/tags`, { signal: controller.signal });
    clearTimeout(timeout);

    if (response.ok) {
      res.json({ ok: true, message: "Ollama service reached." });
    } else {
      res.json({ ok: false, error: `HTTP ${response.status}` });
    }
  } catch (error) {
    res.json({ ok: false, error: error.message });
  }
});

// POST /workspace/models/create
router.post("/models/create", async (req, res) => {

  try {
    const { modelName, endpoint, tag, description } = req.body;

    if (!modelName || !endpoint) {
      return res.status(400).json({ ok: false, error: "Model name and endpoint are required." });
    }

    const db = getDb();
    const modelId = `ollama_${Math.random().toString(36).substring(2, 10)}`;
    const createdAt = new Date().toISOString();

    const insert = db.prepare(`
      INSERT INTO ollama_models (model_id, model_name, endpoint, tag, description, created_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    insert.run(modelId, modelName, endpoint, tag || null, description || null, createdAt);

    db.close();

    console.log(`[WORKSPACE] Model created: ${modelName} @ ${endpoint}`);

    res.json({ ok: true, modelId });
  } catch (error) {
    console.error("[WORKSPACE] Error creating model:", error.message);
    res.status(500).json({ ok: false, error: error.message });
  }
});

export default router;
