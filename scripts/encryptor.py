"""
encryptor.py
----------
Module to encrypt all chunks in /chunks one by one and place them in /enc_chunks using AES.
"""

import os
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# -----------------------------
# Config / Constants
# -----------------------------
OUTPUT_DIR = "enc_chunks"
INPUT_DIR = "chunks"
MANIFEST_JSON = "manifest.json"

# -----------------------------
# Helper Functions
# -----------------------------

def ensure_output_dir(directory: str = OUTPUT_DIR):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")

def generate_chunk_filename(index: int, output_dir: str = OUTPUT_DIR, extension: str = "enc") -> str:
    """
    Returns a standardized filename for each encrypted chunk, e.g., chunk001.enc
    """
    filename = f"chunk{index:03d}.{extension}"
    return os.path.join(output_dir, filename)

def chunk_manifest_validation(manifest: str = MANIFEST_JSON):
    """
    Validate that all chunks listed in manifest exist in INPUT_DIR.
    Returns True if all exist, False otherwise.
    """
    manifest_path = os.path.join(INPUT_DIR, manifest)
    
    if not os.path.exists(manifest_path):
        print(f"Manifest file does not exist, EXITING")
        return False

    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    all_exist = True
    for i, entry in enumerate(manifest_data.get("chunks", [])):
        chunk_file = os.path.join(INPUT_DIR, os.path.basename(entry["filename"]))
        if not os.path.exists(chunk_file):
            print(f"Missing chunk: {chunk_file}")
            all_exist = False
        else:
            print(f"Found chunk: {chunk_file}")

    return all_exist


def chunk_encryptor(key: bytes):
    """
    Encrypt each chunk from INPUT_DIR and save to OUTPUT_DIR using AES-GCM.
    Updates manifest with IVs and tags.
    """

    # Load manifest
    manifest_path = os.path.join(INPUT_DIR, MANIFEST_JSON)

    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    for i, entry in enumerate(manifest_data.get("chunks", [])):
        input_file = os.path.join(INPUT_DIR, os.path.basename(entry["filename"]))
        output_file = generate_chunk_filename(i)

        # Read chunk data
        with open(input_file, "rb") as f:
            plaintext = f.read()

        # Create AES-GCM cipher
        iv = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

        # Save encrypted chunk
        with open(output_file, "wb") as f:
            f.write(ciphertext)

        # Update manifest
        entry["filename"] = output_file
        entry["iv"] = iv.hex()
        entry["tag"] = tag.hex()

        print(f"Encrypted chunk {i} → {output_file}")

    # Save updated manifest
    with open(os.path.join(OUTPUT_DIR, MANIFEST_JSON), "w") as f:
        json.dump(manifest_data, f, indent=4)

    print("All chunks encrypted. Manifest updated.")


if __name__ == "__main__":
    ensure_output_dir(OUTPUT_DIR)
    valid = chunk_manifest_validation(MANIFEST_JSON)
    if not valid:
        exit(1)

    key = get_random_bytes(32)

    KEY_FILE = os.path.join(OUTPUT_DIR, "aes_key.bin")
    with open(KEY_FILE, "wb") as f:
        f.write(key)

    print(f"AES key saved to {KEY_FILE}")
    
    chunk_encryptor(key)
