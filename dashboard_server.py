import os
import sys
import json
import asyncio
from typing import List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Ensure utf-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from automation.tracker_manager import ApplicationTracker
from automation.cover_letter_generator import CoverLetterGenerator
from automation.browser_engine import BrowserEngine

app = FastAPI(title="Job Copilot Dashboard")

# Mount static files
WEB_DIR = os.path.abspath("web")
os.makedirs(WEB_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_json(self, data: dict):
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)

manager = ConnectionManager()

async def ws_log_broadcaster(payload: dict):
    await manager.broadcast_json({"type": "log", **payload})

# Initialize Engines
tracker = ApplicationTracker()
cover_gen = CoverLetterGenerator()
browser_engine = BrowserEngine(log_broadcaster=ws_log_broadcaster)

# Models
class LaunchBrowserRequest(BaseModel):
    url: str = "https://www.linkedin.com/jobs/"

class CoverLetterRequest(BaseModel):
    company: str = ""
    role: str = ""
    category: str = "Tech"

class ApplicationLogRequest(BaseModel):
    company: str
    role: str
    category: str = "Tech"
    platform: str = "LinkedIn"
    job_url: str = ""

# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Dashboard index.html not found.</h1>", status_code=404)

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial status
    try:
        stats = tracker.get_stats()
        status = await browser_engine.get_status()
        await websocket.send_json({"type": "stats", **stats})
        await websocket.send_json({"type": "status", **status})

        while True:
            # Keepalive listener
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.get("/api/stats")
async def get_stats():
    return tracker.get_stats()

@app.get("/api/applications")
async def get_applications():
    return tracker.get_all_applications()

@app.post("/api/applications")
async def log_application(req: ApplicationLogRequest):
    app_id = tracker.log_application(
        company=req.company,
        role=req.role,
        category=req.category,
        platform=req.platform,
        job_url=req.job_url
    )
    # Broadcast updated stats
    new_stats = tracker.get_stats()
    await manager.broadcast_json({"type": "stats", **new_stats})
    await browser_engine.log(f"Logged application #{app_id}: {req.company} ({req.role})", "success")
    return {"success": True, "id": app_id, "stats": new_stats}

@app.get("/api/profile")
async def get_profile():
    return browser_engine.load_profile()

@app.post("/api/profile")
async def update_profile(req: Request):
    data = await req.json()
    browser_engine.save_profile(data)
    await browser_engine.log("Candidate profile & screening answers updated.", "success")
    return {"success": True}

@app.post("/api/cover-letter/preview")
async def preview_cover_letter(req: CoverLetterRequest):
    res = cover_gen.generate(req.company, req.role, category=req.category)
    return res

@app.get("/api/browser/status")
async def get_browser_status():
    return await browser_engine.get_status()

@app.post("/api/browser/launch")
async def launch_browser_endpoint(req: LaunchBrowserRequest):
    asyncio.create_task(browser_engine.launch_browser(req.url))
    return {"success": True, "message": "Launching browser..."}

@app.post("/api/browser/autofill")
async def autofill_endpoint():
    result = await browser_engine.autofill_current_page()
    return result

@app.post("/api/browser/inject-cover-letter")
async def inject_cover_letter_endpoint(req: CoverLetterRequest):
    result = await browser_engine.inject_cover_letter(req.company, req.role, category=req.category)
    return result

@app.post("/api/browser/safe-batch-step")
async def safe_batch_endpoint():
    result = await browser_engine.safe_batch_apply_step()
    return result

@app.post("/api/browser/close")
async def close_browser_endpoint():
    await browser_engine.close_browser()
    status = await browser_engine.get_status()
    await manager.broadcast_json({"type": "status", **status})
    return {"success": True}

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("   🚀 STARTING JOB COPILOT DASHBOARD SERVER")
    print("   👉 Open your browser at: http://localhost:8000")
    print("=" * 65 + "\n")
    uvicorn.run("dashboard_server.py:app", host="127.0.0.1", port=8000, reload=False)
