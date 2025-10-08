from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

# -----------------------------
# Config
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENC_CHUNKS_DIR = os.path.join(BASE_DIR, "enc_chunks")   # encrypted segments + manifest + AES key
FRONTEND_DIR = os.path.join(BASE_DIR, "player")          # HTML + JS + CSS

app = FastAPI(title="Encrypted Video Player MVP")

# -----------------------------
# Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Fine for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Static mounts
# -----------------------------
app.mount("/web", StaticFiles(directory=FRONTEND_DIR), name="web")
app.mount("/enc_chunks", StaticFiles(directory=ENC_CHUNKS_DIR), name="enc_chunks")

# -----------------------------
# Routes
# -----------------------------

@app.get("/")
def serve_index():
    """Serve the main player page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)

@app.get("/key")
def get_key():
    key_path = os.path.join(ENC_CHUNKS_DIR, "aes_key.bin")
    return FileResponse(key_path, media_type="application/octet-stream")


@app.get("/ping")
def ping():
    """Health check."""
    return {"status": "ok"}

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
