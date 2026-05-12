# app/routers/realtime.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager

router = APIRouter(tags=["Realtime"])


@router.websocket("/ws/elections/{election_id}")
async def election_updates(websocket: WebSocket, election_id: int):
    """
    WebSocket endpoint for live election updates.
    Clients connect here to receive real-time pushes when
    candidates are analyzed or election status changes.
    """
    channel = f"election_{election_id}"
    await manager.connect(websocket, channel)
    try:
        # Keep connection alive — wait for client messages (or disconnection)
        while True:
            # We don't expect client messages, but we must await something
            # to detect when the client disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/ws/news")
async def news_updates(websocket: WebSocket):
    """
    WebSocket endpoint for live news feed.
    Clients connect here to receive real-time pushes when
    a news article is analyzed.
    """
    channel = "news"
    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)