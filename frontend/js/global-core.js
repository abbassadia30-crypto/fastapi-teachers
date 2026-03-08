/**
 * Institutional Intelligence | WebSocket Signaling
 */
class IntelligenceWS {
    constructor() {
        this.instId = null;
        this.socket = null;
        this.reconnectDelay = 5000;
        this.connectTimeout = null;
        this.baseUrl = "https://fastapi-teachers.onrender.com";
    }

    async start() {/**
     * Institutional Intelligence | WebSocket Signaling
     */
    class IntelligenceWS {
        constructor() {
            this.instId = null;
            this.socket = null;
            this.reconnectDelay = 5000;
            this.connectTimeout = null;
            this.baseUrl = "https://fastapi-teachers.onrender.com";
        }

        async start() {
            this.instId = await AppStorage.get('institution_id');
            if (!this.instId) return;

            this.initiateLink();
        }

        initiateLink() {
            // 🔥 DEBOUNCE: Wait 500ms before actually connecting to save server CPU
            clearTimeout(this.connectTimeout);
            this.connectTimeout = setTimeout(() => this.connect(), 2000);
        }

        // Inside IntelligenceWS class in global-core.js
        connect() {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) return;

            const wsUrl = `${this.baseUrl.replace("https", "wss")}/state/ws/institution-sync/${this.instId}`;
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log("🏛️ Intelligence Link Established");
                // Send a heartbeat every 30 seconds to keep Render connection alive
                this.heartbeat = setInterval(() => {
                    if (this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(JSON.stringify({ type: "ping" }));
                    }
                }, 30000);
            };

            this.socket.onmessage = async (event) => {
                try {
                    const registry = JSON.parse(event.data);
                    if (registry.type === "pong") return; // Ignore heartbeat responses
                    if (registry && registry.shards) {
                        window.IntelligenceExecutor.reconcile(registry);
                    }
                } catch (e) { console.error("WS Parse Error"); }
            };

            this.socket.onclose = () => {
                clearInterval(this.heartbeat); // Stop pinging
                this.socket = null;
                setTimeout(() => this.initiateLink(), this.reconnectDelay);
            };
        }
    }



        window.IntelligenceWS = new IntelligenceWS();
        window.IntelligenceWS.start();
        this.instId = await AppStorage.get('institution_id');
        if (!this.instId) return;

        this.initiateLink();
    }

    initiateLink() {
        // 🔥 DEBOUNCE: Wait 500ms before actually connecting to save server CPU
        clearTimeout(this.connectTimeout);
        this.connectTimeout = setTimeout(() => this.connect(), 2000);
    }

    connect() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) return;
        if (!navigator.onLine) {
            setTimeout(() => this.initiateLink(), this.reconnectDelay);
            return;
        }

        const wsUrl = `${this.baseUrl.replace("https", "wss")}/state/ws/institution-sync/${this.instId}`;
        this.socket = new WebSocket(wsUrl);

        this.socket.onmessage = async (event) => {
            try {
                const registry = JSON.parse(event.data);
                if (registry && registry.shards) {
                    // 🔥 DELEGATE to the separate Executor
                    window.IntelligenceExecutor.reconcile(registry);
                }
            } catch (e) { console.error("WS Parse Error"); }
        };

        this.socket.onclose = () => {
            this.socket = null;
            setTimeout(() => this.initiateLink(), this.reconnectDelay);
        };

        this.socket.onerror = () => this.socket.close();
    }
}



window.IntelligenceWS = new IntelligenceWS();
window.IntelligenceWS.start();