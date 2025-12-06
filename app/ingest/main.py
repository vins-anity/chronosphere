import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.websockets import manager
from app.api.matches import router as matches_router

app = FastAPI(
    title="Chronosphere API",
    description="Dota 2 Real-time AI Probability Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API routers
app.include_router(matches_router)

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Chronosphere API started")
    
    # Start background tasks
    from app.worker.retrain import auto_retrainer
    asyncio.create_task(auto_retrainer.start_loop())

@app.on_event("shutdown")
async def shutdown():
    logger.info("Chronosphere API shutting down")

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
