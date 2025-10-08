class VideoPlayer {
    constructor(videoElementId, manifestUrl, chunksPath, keyUrl, mimeCodec = 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"') {
        this.videoElement = document.getElementById(videoElementId);
        this.manifestUrl = manifestUrl;
        this.chunksPath = chunksPath;
        this.keyUrl = keyUrl;
        this.mimeCodec = mimeCodec;

        this.mediaSource = new MediaSource();
        this.sourceBuffer = null;
        this.chunkQueue = [];
        this.aesKey = null;

        this.init();
    }

    hexToBytes(hex) {
        const bytes = new Uint8Array(hex.length / 2);
        for (let i = 0; i < hex.length; i += 2) {
            bytes[i/2] = parseInt(hex.substr(i, 2), 16);
        }
        return bytes;
    }

    async fetchAESKey() {
        const resp = await fetch(this.keyUrl);
        const keyBuffer = await resp.arrayBuffer();
        return await crypto.subtle.importKey(
            "raw",
            keyBuffer,
            "AES-GCM",
            false,
            ["decrypt"]
        );
    }

    async init() {
        console.log("Initializing video player...");
        this.videoElement.src = URL.createObjectURL(this.mediaSource);
        this.mediaSource.addEventListener('sourceopen', this.onSourceOpen.bind(this));
    }

    async onSourceOpen() {
        console.log("MediaSource opened.");

        if (!MediaSource.isTypeSupported(this.mimeCodec)) {
            console.error(`Unsupported MIME type: ${this.mimeCodec}`);
            return;
        }

        this.sourceBuffer = this.mediaSource.addSourceBuffer(this.mimeCodec);
        this.sourceBuffer.addEventListener('updateend', this.processNextChunk.bind(this));

        try {
            // 1️⃣ Load AES key
            this.aesKey = await this.fetchAESKey();
            console.log("AES key loaded.");

            // 2️⃣ Load manifest
            const manifestResp = await fetch(this.manifestUrl);
            const manifest = await manifestResp.json();

            // 3️⃣ Queue segments (init first)
            this.chunkQueue = [];
            if (manifest.init) this.chunkQueue.push(manifest.init);
            if (manifest.chunks) this.chunkQueue.push(...manifest.chunks);

            console.log(`Total segments: ${this.chunkQueue.length}`);

            // 4️⃣ Start
            this.processNextChunk();
        } catch(err) {
            console.error("Init error:", err);
        }
    }

    async processNextChunk() {
        if (!this.chunkQueue.length) {
            if (this.mediaSource.readyState === 'open' && !this.sourceBuffer.updating) {
                console.log("All segments processed. Ending stream.");
                this.mediaSource.endOfStream();
            }
            return;
        }

        if (this.sourceBuffer.updating) return;

        const chunk = this.chunkQueue.shift();
        console.log(`Processing segment: ${chunk.filename}`);

        try {
            const resp = await fetch(`${this.chunksPath}/${chunk.filename}`);
            const ciphertext = await resp.arrayBuffer();

            // IV + tag
            const iv = this.hexToBytes(chunk.iv);
            const tag = this.hexToBytes(chunk.tag);

            const combined = new Uint8Array(ciphertext.byteLength); // ciphertext already has tag appended
            combined.set(new Uint8Array(ciphertext));

            const decrypted = await crypto.subtle.decrypt(
                { name: "AES-GCM", iv },
                this.aesKey,
                combined.buffer
            );

            this.sourceBuffer.appendBuffer(decrypted);
        } catch(err) {
            console.error(`Error processing ${chunk.filename}:`, err);
        }
    }
}

// Initialize
window.videoPlayer = new VideoPlayer(
    "video",
    "/enc_chunks/manifest.json",
    "/enc_chunks",
    "/enc_chunks/aes_key.bin"
);
