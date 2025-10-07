"""
server.py
---------
FastAPI server for ODCVD MVP.
Serves encrypted video chunks, manifest.json, and the web-based decryptor player.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

# -----------------------------
# Config / Constants
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENC_CHUNKS_DIR = os.path.join(BASE_DIR, "enc_chunks")
FRONTEND_DIR = os.path.join(BASE_DIR, "player")
MANIFEST_PATH = os.path.join(ENC_CHUNKS_DIR, "manifest.json")


app = FastAPI(title="ODCVD MVP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # REMOVE LATER
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static directories
app.mount("/web", StaticFiles(directory=FRONTEND_DIR), name="player")
app.mount("/enc_chunks", StaticFiles(directory=ENC_CHUNKS_DIR), name="enc_chunks")


# -----------------------------
# Routes
# -----------------------------

@app.get("/")
def serve_index():
    """Serve main HTML player page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)


@app.get("/manifest.json")
def get_manifest():
    """Serve manifest JSON."""
    if os.path.exists(MANIFEST_PATH):
        return FileResponse(MANIFEST_PATH)
    return JSONResponse({"error": "manifest.json not found"}, status_code=404)


@app.get("/ping")
def ping():
    """Simple health check."""
    return {"status": "ok"}


# Optional: Placeholder for future key exchange endpoint
@app.get("/key")
def get_key():
    """(Optional) AES key endpoint — placeholder for future secure key delivery."""
    return {"key": "PLACEHOLDER_KEY"}


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
