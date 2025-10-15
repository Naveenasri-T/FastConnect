# backend/app/main.py
import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .groq_client import stream_chat_completion
load_dotenv()

app = FastAPI(title="FastConnect API", version="1.0.0")
# allow local frontend (Streamlit) connections (adjust origins accordingly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "FastConnect API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for connection testing"""
    return {"status": "healthy", "websocket_url": "/ws"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Protocol:
      Client -> Server: {"type": "prompt", "prompt": "Hello"}
      Server -> Client: JSON messages of types:
         {"type":"delta","text":"..."}  (token chunk)
         {"type":"done"}                (stream finished)
         {"type":"error","message":"..."}
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type":"error","message":"invalid json"}))
                continue

            if data.get("type") != "prompt" or "prompt" not in data:
                await websocket.send_text(json.dumps({"type":"error","message":"expected type 'prompt' with 'prompt' field"}))
                continue

            prompt = data["prompt"]
            # stream from Groq and forward deltas to client
            try:
                async for chunk in stream_chat_completion(prompt):
                    # send partial token chunk to client
                    await websocket.send_text(json.dumps({"type":"delta", "text": chunk}))
                # when done
                await websocket.send_text(json.dumps({"type":"done"}))
            except Exception as e:
                await websocket.send_text(json.dumps({"type":"error", "message": str(e)}))

    except WebSocketDisconnect:
        # client disconnected; nothing special to do
        return
