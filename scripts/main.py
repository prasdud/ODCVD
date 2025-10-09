import os
import subprocess
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# -----------------------------
# Config
# -----------------------------
INPUT_VIDEO = "demo/backup-video.mp4"
CHUNK_DIR = "chunks"        # temp folder for fMP4 segments
OUTPUT_DIR = "enc_chunks"   # encrypted output
AES_KEY_FILE = "aes_key.bin"
MANIFEST_FILE = "manifest.json"
AES_KEY = b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'  # 32 bytes

# -----------------------------
# Helpers
# -----------------------------
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def run_command(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stdout.decode())
        print(result.stderr.decode())
        raise RuntimeError("Command failed")
    return result.stdout.decode()

def fragment_video(input_file, output_dir):
    """Use MP4Box to fragment input MP4 into fMP4 segments"""
    ensure_dir(output_dir)
    mpd_file = os.path.join(output_dir, "stream.mpd")
    cmd = [
        "MP4Box",
        "-dash", "1000",      # 1-second segments
        "-frag-rap",
        "-rap",
        "-segment-name", "segment_",
        input_file,
        "-out", mpd_file
    ]
    print("[+] Fragmenting video with MP4Box...")
    run_command(cmd)
    print("[+] Fragmentation complete.")

    # Collect init + media segments
    segments = sorted([
        f for f in os.listdir(output_dir)
        if f.endswith(".m4s") or f.endswith("init.mp4")
    ])
    # Ensure init segment first
    segments.sort(key=lambda x: 0 if "init.mp4" in x else 1)
    print(f"[+] Segments found: {segments}")
    return segments

def generate_enc_filename(index=None, is_init=False):
    if is_init:
        return "chunk_init.enc"
    return f"chunk{index:03d}.enc"

def encrypt_segments(segments, input_dir, output_dir, key):
    """Encrypt each fMP4 segment using AES-GCM and build manifest"""
    ensure_dir(output_dir)
    manifest = {"init": {}, "chunks": []}

    chunk_index = 0
    for seg in segments:
        input_path = os.path.join(input_dir, seg)
        is_init = "init.mp4" in seg
        output_filename = generate_enc_filename(index=chunk_index, is_init=is_init)
        output_path = os.path.join(output_dir, output_filename)

        with open(input_path, "rb") as f:
            plaintext = f.read()

        iv = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

        # Write ciphertext + tag
        with open(output_path, "wb") as f:
            f.write(ciphertext + tag)

        print(f"[+] Encrypted {seg} → {output_filename}")

        entry = {"filename": output_filename, "iv": iv.hex(), "tag": tag.hex()}

        if is_init:
            manifest["init"] = entry
        else:
            manifest["chunks"].append(entry)
            chunk_index += 1

    # Save manifest
    manifest_path = os.path.join(output_dir, MANIFEST_FILE)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)
    print(f"[+] Manifest saved: {manifest_path}")

    # Save AES key
    key_path = os.path.join(output_dir, AES_KEY_FILE)
    with open(key_path, "wb") as f:
        f.write(key)
    print(f"[+] AES key saved: {key_path}")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    ensure_dir(CHUNK_DIR)
    ensure_dir(OUTPUT_DIR)

    # Step 1: Fragment video
    segments = fragment_video(INPUT_VIDEO, CHUNK_DIR)

    # Step 2: Encrypt segments
    encrypt_segments(segments, CHUNK_DIR, OUTPUT_DIR, AES_KEY)
