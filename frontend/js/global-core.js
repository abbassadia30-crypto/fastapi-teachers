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

    async start() {
        // Get ID from your storage.js
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