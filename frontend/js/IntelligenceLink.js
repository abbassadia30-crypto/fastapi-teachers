/**
 * 🏛️ Intelligence Link (The Messenger)
 * Concept: Background Service | Phenomenon: Reliable Signaling
 */
class IntelligenceLink {
    constructor() {
        this.socket = null;
        this.instId = null;
        this.baseUrl = "https://fastapi-teachers.onrender.com";
        this.pingInterval = null;
        this.reconnectTimeout = null;
    }

    async start() {
        // Clear any pending reconnection attempts to prevent duplicates
        clearTimeout(this.reconnectTimeout);

        this.instId = await AppStorage.get('institution_id');
        if (!this.instId) {
            console.warn("🏛️ Intelligence Link: No Institution ID found. Standby.");
            return;
        }
        this.connect();
    }

    connect() {
        // 1. Guard: Don't connect if already open
        if (this.socket && this.socket.readyState === WebSocket.OPEN) return;

        // 2. Protocol Transformation: Ensure wss for production
        const wsUrl = `${this.baseUrl.replace("https", "wss")}/state/ws/institution-sync/${this.instId}`;

        console.log("🏛️ Intelligence Link: Connecting...");
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log("✅ Intelligence Link: Online");

            // 3. Phenomenon: The Heartbeat
            // We send 'ping' every 25s. If server doesn't respond, the link is dead.
            if (this.pingInterval) clearInterval(this.pingInterval);
            this.pingInterval = setInterval(() => {
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send("ping");
                }
            }, 25000);
        };

        this.socket.onmessage = (event) => {
            // Phenomenon: Filter internal signaling (pong) from real data
            if (event.data === "pong" || event.data.includes('"type":"pong"')) return;

            try {
                const registry = JSON.parse(event.data);
                // 4. Safe Hand-off to the Repository
                if (window.IntelligenceRepository) {
                    window.IntelligenceRepository.reconcile(registry);
                } else {
                    console.error("❌ Intelligence Repository not found in global scope!");
                }
            } catch (e) {
                console.error("❌ Registry Parse Error:", e);
            }
        };

        this.socket.onerror = (err) => {
            console.error("⚠️ Intelligence Link Error:", err);
            this.socket.close(); // Force trigger onclose for recovery
        };

        this.socket.onclose = () => {
            console.warn("🔌 Intelligence Link: Offline. Retrying in 5s...");
            clearInterval(this.pingInterval);

            // 5. Phenomenon: Exponential Backoff (Simplified)
            // Prevents spamming the server if it's actually down
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = setTimeout(() => this.connect(), 5000);
        };
    }

    // Concept: Clean Shutdown (Used when user logs out)
    stop() {
        clearTimeout(this.reconnectTimeout);
        clearInterval(this.pingInterval);
        if (this.socket) {
            this.socket.close();
        }
    }
}

window.IntelligenceLink = new IntelligenceLink();