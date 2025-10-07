// decryptor.js
// -----------------------------
// Barebones decryptor for ODCVD MVP
// -----------------------------

// Hardcoded AES key for testing (replace with secure key later)
const AES_KEY_BASE64 = "QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE=";

async function importKey(base64Key) {
    const rawKey = Uint8Array.from(atob(AES_KEY_BASE64), c => c.charCodeAt(0));
    console.log("JS Key bytes:", rawKey);
    // Should print: Uint8Array(32) [65, 65, 65, ..., 65]

    return await crypto.subtle.importKey(
        "raw",
        rawKey,
        { name: "AES-GCM" },
        false,
        ["decrypt"]
    );
}

// Fetch and parse manifest.json
async function fetchManifest() {
    const response = await fetch("/manifest.json");
    const manifest = await response.json();
    return manifest.chunks;  // Array of chunk objects
}

// Fetch a single encrypted chunk
async function fetchChunk(url) {
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    return arrayBuffer;
}

// Decrypt a chunk using AES-GCM
async function decryptChunk(encryptedBuffer, key, ivHex, tagHex) {
    const iv = hexStringToUint8Array(ivHex);
    const tag = hexStringToUint8Array(tagHex);

    console.log("IV:", ivHex, iv, "length:", iv.length);
    console.log("Tag:", tagHex, tag, "length:", tag.length);
    console.log("Ciphertext length:", encryptedBuffer.byteLength);

    // Append the tag to the end of ciphertext (Web Crypto expects it that way)
    const dataWithTag = new Uint8Array(encryptedBuffer.byteLength + tag.length);
    dataWithTag.set(new Uint8Array(encryptedBuffer), 0);
    dataWithTag.set(tag, encryptedBuffer.byteLength);

    const decrypted = await crypto.subtle.decrypt(
        { name: "AES-GCM", iv: iv },
        key,
        dataWithTag
    );

    return decrypted; // ArrayBuffer
}

// Utility: Convert hex string to Uint8Array
function hexStringToUint8Array(hex) {
    if (hex.length % 2 !== 0) throw "Invalid hex string";
    const arr = new Uint8Array(hex.length / 2);
    for (let i = 0; i < hex.length; i += 2) {
        arr[i / 2] = parseInt(hex.substr(i, 2), 16);
    }
    return arr;
}

// Main function
async function decryptAllChunks() {
    const key = await importKey(AES_KEY_BASE64);
    const chunks = await fetchManifest();

    const decryptedChunks = [];

    for (let i = 0; i < chunks.length; i++) {
        const chunk = chunks[i];
        console.log(`Fetching chunk: ${chunk.filename}`);
        const encryptedBuffer = await fetchChunk("/" + chunk.filename);
        console.log(`Decrypting chunk ${i}`);
        const decryptedBuffer = await decryptChunk(
            encryptedBuffer,
            key,
            chunk.iv,
            chunk.tag
        );

        decryptedChunks.push(decryptedBuffer);
        console.log(`Chunk ${i} decrypted`);
    }

    console.log("All chunks decrypted");
    return decryptedChunks;
}

// Start decryption (for testing)
decryptAllChunks().then(chunks => {
    console.log("Decrypted chunks array:", chunks);
});
