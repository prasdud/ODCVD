
# ODCVD: On-Demand Chunked Video Decryptor

ODCVD is a proof-of-concept system for secure, on-demand playback of encrypted video. Instead of decrypting an entire video file at once, ODCVD decrypts and streams video in small chunks, enabling just-in-time decryption and playback in the browser. This approach improves security and efficiency for encrypted video delivery.

## Status

- **Completed & Working**: The MVP is functional and demonstrates on-demand chunked decryption and playback.
- **Not Actively Developing**: No new features are planned, but issues and PRs are welcome.

## Features

- Encrypts video segments using AES-GCM
- Serves encrypted chunks and manifest via FastAPI backend
- Decrypts and plays video in-browser using JavaScript and WebCrypto API
- No need to decrypt the entire video at once

## Requirements

- Python 3.8+
- [FastAPI](https://fastapi.tiangolo.com/)
- [pycryptodome](https://pycryptodome.readthedocs.io/en/latest/)
- [Uvicorn](https://www.uvicorn.org/) (for running the server)
- [ffmpeg](https://ffmpeg.org/) and [MP4Box](https://gpac.wp.imt.fr/mp4box/) (for chunking and fragmenting video)

Install Python dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pycryptodome
```

## Usage

1. **Prepare your video:**
	- Place your input video in the `demo/` directory (e.g., `demo/video.mp4`).

2. **Chunk and encrypt the video:**
	- Use the provided scripts to split and encrypt the video:
	  - `python scripts/chunker.py` (splits video into chunks using ffmpeg)
	  - `python scripts/main.py` (fragments, encrypts, and generates manifest)

3. **Start the server:**
	- Run the FastAPI server:
	  ```bash
	  uvicorn server:app --reload
	  ```

4. **Play the video:**
	- Open your browser and go to [http://localhost:8000/](http://localhost:8000/) to use the encrypted video player.

## Project Structure

- `scripts/` — Video chunking and encryption scripts
- `chunks/` — Raw video segments (not encrypted)
- `enc_chunks/` — Encrypted video chunks, manifest, and AES key
- `player/` — HTML/JS frontend for playback and decryption
- `server.py` — FastAPI backend serving encrypted content and frontend

## License

MIT License © 2025 Abdul | prasdud