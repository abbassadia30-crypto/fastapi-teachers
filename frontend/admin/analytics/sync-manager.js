/**
 * Institutional Intelligence | Command Center Sync
 * One file, one purpose: Keep local shards synced with the Master Registry.
 */

class IntelligenceManager {
    constructor(instId) {
        this.instId = instId;
        this.baseUrl = "https://fastapi-teachers.onrender.com";
        this.wsUrl = `wss://fastapi-teachers.onrender.com/intelligence/ws/institution-sync/${this.instId}`;
        this.socket = null;
        this.registryPath = 'intelligence/registry.json';
        this.isConnecting = false;
    }

    async start() {
        if (!navigator.onLine) {
            this.showStatus("Working Offline", "orange");
            return;
        }
        this.connect();
    }

    connect() {
        if (this.socket || this.isConnecting) return;
        this.isConnecting = true;

        this.socket = new WebSocket(this.wsUrl);

        this.socket.onopen = () => {
            this.isConnecting = false;
            this.showStatus("Intelligence Synced", "green");
        };

        this.socket.onmessage = async (event) => {
            const serverRegistry = JSON.parse(event.data);
            await this.processSync(serverRegistry);
        };

        this.socket.onclose = () => {
            this.socket = null;
            this.isConnecting = false;
            console.log("📡 Sync Connection Lost. Retrying...");
            setTimeout(() => this.start(), 5000);
        };
    }

    async processSync(serverRegistry) {
        // 1. Load Local Keys
        let localRegistry = { shards: {} };
        try {
            const saved = await Capacitor.Plugins.Filesystem.readFile({
                path: this.registryPath,
                directory: 'DATA',
                encoding: 'utf8'
            });
            localRegistry = JSON.parse(saved.data);
        } catch (e) { console.log("Fresh initialization..."); }

        let updatedAnything = false;

        // 2. Loop through shards
        for (const section in serverRegistry.shards) {
            const sKey = serverRegistry.shards[section];
            const lKey = localRegistry.shards[section];

            if (sKey !== lKey) {
                console.log(`🔨 Updating Shard: ${section}`);
                const success = await this.downloadAndWriteShard(section, sKey);
                if (success) {
                    localRegistry.shards[section] = sKey;
                    updatedAnything = true;
                }
            }
        }

        // 3. Save Registry if keys changed
        if (updatedAnything) {
            await Capacitor.Plugins.Filesystem.writeFile({
                path: this.registryPath,
                data: JSON.stringify(localRegistry),
                directory: 'DATA',
                encoding: 'utf8'
            });
            this.showStatus("Data Updated", "green");
        }
    }

    async downloadAndWriteShard(section, key) {
        try {
            const res = await fetch(`${this.baseUrl}/intelligence/shard/${this.instId}/${section}?key=${key}`);
            if (!res.ok) throw new Error("Auth Failed");

            const data = await res.json();

            await Capacitor.Plugins.Filesystem.writeFile({
                path: `intelligence/${section}.json`,
                data: JSON.stringify(data),
                directory: 'DATA',
                encoding: 'utf8',
                recursive: true
            });
            return true;
        } catch (err) {
            console.error(`Sync error for ${section}:`, err);
            return false;
        }
    }

    showStatus(msg, type) {
        const color = type === 'red' ? '#f43f5e' : type === 'orange' ? '#f59e0b' : '#10b981';
        const box = document.createElement('div');
        box.className = "sync-status-box";
        box.style = `position:fixed; bottom:20px; right:20px; padding:10px 18px; 
                     background:${color}; color:white; border-radius:8px; z-index:10000; 
                     font-size:13px; font-weight:bold; box-shadow:0 4px 12px rgba(0,0,0,0.2);`;
        box.innerText = msg;
        document.body.appendChild(box);
        setTimeout(() => box.remove(), 4000);
    }
}

// --- INITIALIZATION ---
// Replace USER_INST_ID with your actual variable
const intelligence = new IntelligenceManager(USER_INST_ID);

// Start on Load
document.addEventListener('DOMContentLoaded', () => intelligence.start());

// Internet Awareness Listeners
window.addEventListener('online', () => intelligence.start());
window.addEventListener('offline', () => intelligence.showStatus("Offline Mode", "orange"));