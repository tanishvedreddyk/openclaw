"""
OpenClaw Core API
- GET  /              → chat web UI
- GET  /api/health    → health check
- GET  /api/models    → list available models
- POST /api/chat      → REST chat (non-streaming)
- WS   /ws/{session}  → streaming WebSocket chat
"""
import json, uuid, asyncio, httpx
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import cfg
from core.llm import chat_stream, chat_once

app = FastAPI(title="OpenClaw", version="1.0.0")

# ─── Session store ─────────────────────────────────────────────────────────────
sessions: Dict[str, List[dict]] = defaultdict(list)

def get_or_create(session_id: str) -> List[dict]:
    return sessions[session_id]

def trim_history(session_id: str):
    h = sessions[session_id]
    if len(h) > cfg.MAX_HISTORY * 2:
        sessions[session_id] = h[-(cfg.MAX_HISTORY * 2):]

# ─── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "model": cfg.LLM_MODEL, "provider": cfg.LLM_PROVIDER}


@app.get("/api/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{cfg.LLM_BASE_URL.rstrip('/v1').rstrip('/')}/api/tags")
            if r.status_code == 200:
                data = r.json()
                names = [m["name"] for m in data.get("models", [])]
                return {"models": names}
    except Exception:
        pass
    return {"models": [cfg.LLM_MODEL]}


class ChatRequest(BaseModel):
    message:    str
    session_id: str = ""
    model:      str = ""
    platform:   str = "api"
    user_id:    str = ""

@app.post("/api/chat")
async def rest_chat(req: ChatRequest):
    sid = req.session_id or str(uuid.uuid4())
    history = get_or_create(sid)
    history.append({"role": "user", "content": req.message})
    trim_history(sid)

    reply = await chat_once(history, model=req.model or None)

    history.append({"role": "assistant", "content": reply})
    return {"reply": reply, "session_id": sid}


@app.delete("/api/chat/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": session_id}


# ─── WebSocket (streaming) ─────────────────────────────────────────────────────

@app.websocket("/ws/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    history = get_or_create(session_id)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"message": raw}

            message = data.get("message", "").strip()
            model   = data.get("model", "")
            if not message:
                continue

            history.append({"role": "user", "content": message})
            trim_history(session_id)

            full_reply = []
            async for token in chat_stream(history, model=model or None):
                await websocket.send_text(json.dumps({"type": "token", "content": token}))
                full_reply.append(token)

            reply = "".join(full_reply)
            history.append({"role": "assistant", "content": reply})
            await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "content": str(e)}))
        except Exception:
            pass


# ─── Serve web UI ─────────────────────────────────────────────────────────────

WEB_DIR = Path(__file__).parent.parent / "web"

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index = WEB_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>OpenClaw API running. Web UI not found.</h1>")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.main:app", host=cfg.HOST, port=cfg.PORT,
                reload=False, workers=1)
