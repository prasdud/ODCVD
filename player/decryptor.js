// decryptor.js
// Client-side decryption and playback for encrypted video chunks

class EncryptedVideoPlayer {
    constructor() {
        this.videoElement = document.getElementById('video');
        this.manifest = null;
        this.currentChunkIndex = 0;
        this.isPlaying = false;
        this.key = null;
        
        // Initialize the player
        this.init();
    }

    async init() {
        try {
            console.log('Initializing encrypted video player...');
            
            // Load AES key (in production, this would come from a secure endpoint)
            await this.loadKey();
            
            // Load manifest
            await this.loadManifest();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Preload first chunk
            await this.loadChunk(0);
            
            console.log('Player initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize player:', error);
        }
    }

    async loadKey() {
        // In this demo, we'll use a hardcoded key that matches the server
        // In production, this should be fetched from a secure endpoint
        const keyBytes = new Uint8Array(32).fill(65); // 65 = 'A' in ASCII
        this.key = await crypto.subtle.importKey(
            'raw',
            keyBytes,
            { name: 'AES-GCM' },
            false,
            ['decrypt']
        );
        console.log('AES key loaded');
    }

    async loadManifest() {
        const response = await fetch('/manifest.json');
        if (!response.ok) {
            throw new Error(`Failed to load manifest: ${response.status}`);
        }
        
        this.manifest = await response.json();
        console.log(`Loaded manifest with ${this.manifest.chunks.length} chunks`);
    }

    setupEventListeners() {
        // When video ends, load next chunk
        this.videoElement.addEventListener('ended', () => {
            this.loadNextChunk();
        });

        // When video time updates, check if we need to preload next chunk
        this.videoElement.addEventListener('timeupdate', () => {
            this.handleTimeUpdate();
        });

        // Handle errors
        this.videoElement.addEventListener('error', (e) => {
            console.error('Video error:', e);
        });
    }

    async loadChunk(chunkIndex) {
        if (!this.manifest || chunkIndex >= this.manifest.chunks.length) {
            console.log('All chunks played or manifest not loaded');
            this.videoElement.pause();
            return;
        }

        const chunk = this.manifest.chunks[chunkIndex];
        console.log(`Loading chunk ${chunkIndex}: ${chunk.filename}`);

        try {
            // Fetch encrypted chunk
            const encryptedResponse = await fetch(`/enc_chunks/${chunk.filename}`);
            if (!encryptedResponse.ok) {
                throw new Error(`Failed to fetch chunk ${chunkIndex}`);
            }

            const encryptedData = await encryptedResponse.arrayBuffer();
            
            // Decrypt the chunk
            const decryptedData = await this.decryptChunk(encryptedData, chunk);
            
            // Create blob URL for the decrypted video chunk
            const blob = new Blob([decryptedData], { type: 'video/mp4' });
            const videoUrl = URL.createObjectURL(blob);
            
            // Update video source
            this.videoElement.src = videoUrl;
            this.currentChunkIndex = chunkIndex;
            
            console.log(`Chunk ${chunkIndex} loaded and decrypted successfully`);
            
            // Auto-play if it's the first chunk
            if (chunkIndex === 0) {
                this.videoElement.play().catch(e => {
                    console.log('Autoplay prevented, user interaction required');
                });
            }
            
        } catch (error) {
            console.error(`Error loading chunk ${chunkIndex}:`, error);
        }
    }

    async decryptChunk(encryptedData, chunkInfo) {
        try {
            // Convert IV and tag from hex strings to ArrayBuffer
            const iv = this.hexToArrayBuffer(chunkInfo.iv);
            const tag = this.hexToArrayBuffer(chunkInfo.tag);
            
            // Combine encrypted data with authentication tag
            const encryptedBuffer = new Uint8Array(encryptedData);
            const tagBuffer = new Uint8Array(tag);
            const combinedData = new Uint8Array(encryptedBuffer.length + tagBuffer.length);
            combinedData.set(encryptedBuffer);
            combinedData.set(tagBuffer, encryptedBuffer.length);
            
            // Decrypt using AES-GCM
            const decryptedData = await crypto.subtle.decrypt(
                {
                    name: 'AES-GCM',
                    iv: iv,
                    additionalData: new ArrayBuffer(0), // No additional data
                    tagLength: 128 // 16 bytes
                },
                this.key,
                combinedData
            );
            
            return decryptedData;
            
        } catch (error) {
            console.error('Decryption failed:', error);
            throw new Error('Failed to decrypt video chunk');
        }
    }

    hexToArrayBuffer(hexString) {
        const bytes = new Uint8Array(hexString.length / 2);
        for (let i = 0; i < hexString.length; i += 2) {
            bytes[i / 2] = parseInt(hexString.substr(i, 2), 16);
        }
        return bytes;
    }

    async loadNextChunk() {
        const nextIndex = this.currentChunkIndex + 1;
        if (nextIndex < this.manifest.chunks.length) {
            // Clean up previous blob URL to avoid memory leaks
            if (this.videoElement.src) {
                URL.revokeObjectURL(this.videoElement.src);
            }
            
            await this.loadChunk(nextIndex);
        } else {
            console.log('Reached end of all chunks');
            // Optional: loop back to beginning
            // this.loadChunk(0);
        }
    }

    handleTimeUpdate() {
        // Preload next chunk when current chunk is near the end
        const currentTime = this.videoElement.currentTime;
        const duration = this.videoElement.duration;
        
        // If we're in the last 2 seconds of the current chunk, preload next
        if (duration - currentTime < 2 && this.currentChunkIndex < this.manifest.chunks.length - 1) {
            this.preloadNextChunk();
        }
    }

    async preloadNextChunk() {
        const nextIndex = this.currentChunkIndex + 1;
        if (nextIndex >= this.manifest.chunks.length) return;
        
        // Just fetch and decrypt, don't switch the video source yet
        try {
            const chunk = this.manifest.chunks[nextIndex];
            const encryptedResponse = await fetch(`/enc_chunks/${chunk.filename}`);
            const encryptedData = await encryptedResponse.arrayBuffer();
            
            // Decrypt and cache (we don't use the result here, but this warms up the decryption)
            await this.decryptChunk(encryptedData, chunk);
            console.log(`Preloaded chunk ${nextIndex}`);
            
        } catch (error) {
            console.error(`Failed to preload chunk ${nextIndex}:`, error);
        }
    }

    // Public methods for external control
    play() {
        this.videoElement.play();
    }

    pause() {
        this.videoElement.pause();
    }

    seekToChunk(chunkIndex) {
        if (chunkIndex >= 0 && chunkIndex < this.manifest.chunks.length) {
            if (this.videoElement.src) {
                URL.revokeObjectURL(this.videoElement.src);
            }
            this.loadChunk(chunkIndex);
        }
    }

    getCurrentChunkInfo() {
        if (!this.manifest) return null;
        return {
            current: this.currentChunkIndex,
            total: this.manifest.chunks.length,
            chunk: this.manifest.chunks[this.currentChunkIndex]
        };
    }
}

// Initialize player when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.videoPlayer = new EncryptedVideoPlayer();
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EncryptedVideoPlayer;
}