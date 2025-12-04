import asyncio
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core import globals
from app.core.websockets import manager
from app.core.db import connect_db, disconnect_db
from app.worker.worker import process_gsi_stream
from loguru import logger
import json

app = FastAPI(title="Chronosphere Ingest (Lite)")

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Initialize global queue
    globals.queue = asyncio.Queue()
    
    # Connect to DB
    await connect_db()
    
    # Start worker task
    app.state.worker_task = asyncio.create_task(process_gsi_stream())
    logger.info("Startup complete: Queue initialized, DB connected, Worker started")

@app.on_event("shutdown")
async def shutdown():
    # Cancel worker task
    if hasattr(app.state, "worker_task"):
        app.state.worker_task.cancel()
        try:
            await app.state.worker_task
        except asyncio.CancelledError:
            pass
            
    # Disconnect DB
    await disconnect_db()
    logger.info("Shutdown complete")

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, maybe listen for pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.post("/api/v1/gsi")
async def ingest_gsi(request: Request):
    client_host = request.client.host
    if client_host not in settings.ALLOWED_IPS:
        logger.warning(f"Unauthorized access attempt from {client_host}")
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Push to in-memory queue
    if globals.queue:
        logger.info(f"Ingest: Queue ID: {id(globals.queue)}")
        globals.queue.put_nowait(data)
        logger.info(f"Ingest: Pushed to queue. Size: {globals.queue.qsize()}")
    else:
        logger.error("Queue not initialized!")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    return {"status": "ok"}
