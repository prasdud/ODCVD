"""
chunker.py
----------
Module to split a video into smaller chunks for just-in-time decryption playback.
"""

import os
import subprocess
import json

# -----------------------------
# Config / Constants
# -----------------------------
CHUNK_LENGTH = 10  # seconds per chunk
OUTPUT_DIR = "chunks"

# -----------------------------
# Helper Functions
# -----------------------------

def ensure_output_dir(directory: str = OUTPUT_DIR):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")

def get_video_duration(video_path: str) -> float:
    """
    Returns the duration of the video in seconds using ffprobe.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration_str = result.stdout.decode().strip()
        duration = float(duration_str)
        return duration
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return 0.0

def generate_chunk_filename(index: int, output_dir: str = OUTPUT_DIR, extension: str = "mp4") -> str:
    """
    Returns a standardized filename for each chunk, e.g., chunk001.mp4
    """
    filename = f"chunk{index:03d}.{extension}"
    return os.path.join(output_dir, filename)


def split_video_into_chunks(video_path: str, chunk_length: int = CHUNK_LENGTH, output_dir: str = OUTPUT_DIR):
    """
    Split the input video into chunks of chunk_length seconds.
    Saves chunks to output_dir.
    """
    ensure_output_dir(output_dir)
    duration = get_video_duration(video_path)
    if duration == 0:
        print("Cannot split video: duration is 0.")
        return

    num_chunks = int(duration // chunk_length) + (1 if duration % chunk_length > 0 else 0)
    print(f"Video duration: {duration:.2f}s, creating {num_chunks} chunks...")

    manifest = {"chunks": []}

    for i in range(num_chunks):
        start_time = i * chunk_length
        # For last chunk, adjust duration if needed
        current_duration = min(chunk_length, duration - start_time)
        chunk_filename = generate_chunk_filename(i, output_dir)

        # FFmpeg command to extract chunk
        command = [
            "ffmpeg",
            "-y",  # overwrite if exists
            "-i", video_path,
            "-ss", str(start_time),
            "-t", str(current_duration),
            "-c", "copy",
            chunk_filename
        ]

        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Created chunk: {chunk_filename} (start: {start_time}s, duration: {current_duration}s)")
            manifest["chunks"].append({"filename": chunk_filename, "start": start_time, "duration": current_duration})
        except Exception as e:
            print(f"Error creating chunk {i}: {e}")

    # Save manifest JSON
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)
    print(f"Chunking complete. Manifest saved to {manifest_path}")


if __name__ == "__main__":
    video_file = "demo/video.mp4"
    split_video_into_chunks(video_file)
