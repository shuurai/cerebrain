"""API route handlers."""

import asyncio
import json
from typing import Any


def handle_chat(body: dict[str, Any], brain_name: str | None = None) -> dict[str, Any]:
    """POST /v1/chat — run brain matrix and return reply."""
    content = (body.get("content") or body.get("message") or "").strip()
    if not content:
        return {"reply": "", "session_id": body.get("session_id"), "error": "empty content"}
    try:
        from cerebrain.core.brain_agent import BrainAgent
        agent = BrainAgent.load(brain_name)
        reply = agent.process_message(content)
        return {"reply": reply, "session_id": body.get("session_id")}
    except Exception as e:
        return {"reply": "", "session_id": body.get("session_id"), "error": str(e)}


def handle_health() -> dict[str, str]:
    """GET /health."""
    return {"status": "ok"}


def handle_brain_info(brain_name: str | None) -> dict[str, Any]:
    """GET /v1/brain — non-sensitive brain info."""
    return {"brain": brain_name or "default", "status": "ok"}


async def handle_websocket(websocket: Any, brain_name: str | None = None) -> None:
    """WebSocket /v1/stream — stateful chat: one brain matrix per connection, JSON messages."""
    from cerebrain.core.brain_agent import BrainAgent

    try:
        agent = await asyncio.to_thread(BrainAgent.load, brain_name)
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e), "type": "init"}))
        await websocket.close()
        return
    await websocket.send_text(json.dumps({"type": "connected", "brain": agent.name}))
    while True:
        try:
            raw = await websocket.receive_text()
        except Exception:
            break
        try:
            body = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({"error": "invalid json", "reply": ""}))
            continue
        content = (body.get("content") or body.get("message") or "").strip()
        if not content:
            await websocket.send_text(json.dumps({"reply": "", "session_id": body.get("session_id"), "error": "empty content"}))
            continue
        try:
            reply = await asyncio.to_thread(agent.process_message, content)
            await websocket.send_text(json.dumps({"reply": reply, "session_id": body.get("session_id")}))
        except Exception as e:
            await websocket.send_text(json.dumps({"reply": "", "error": str(e), "session_id": body.get("session_id")}))
