/**
* Institutional Intelligence | Command Center Sync
* Handles state reconciliation: compares server registry to local storage
* and fetches missing/outdated shards via HTTP.
*/
class IntelligenceManager {
    constructor() {
        this.instId = null;
        this.baseUrl = "https://fastapi-teachers.onrender.com";
        this.socket = null;
        this.registryPath = 'intelligence/registry.json';
        this.isConnecting = false;
        this.wsUrl = null;
    }

    async start() {
        // Correct reference to AppStorage from storage.js
        this.instId = await AppStorage.get('institution_id');

        if (!this.instId) {
            console.error("Sync Manager: No institution_id found.");
            return;
        }

        // Matches /state prefix from FastAPI state.py
        this.wsUrl = `wss://fastapi-teachers.onrender.com/state/ws/institution-sync/${this.instId}`;

        if (!navigator.onLine) {
            this.showStatus("Working Offline", "orange");
            return;
        }
        this.connect();
    }

    connect() {
        if (this.socket || this.isConnecting || !this.wsUrl) return;
        this.isConnecting = true;

        this.socket = new WebSocket(this.wsUrl);

        this.socket.onopen = () => {
            this.isConnecting = false;
            this.showStatus("Intelligence Synced", "green");
            console.log("✅ Sync Link Established");
            // The backend is designed to push the registry immediately upon this connection.
        };

        this.socket.onmessage = async (event) => {
            try {
                const serverRegistry = JSON.parse(event.data);
                // Handle multiple registries/shards if provided
                if (serverRegistry && serverRegistry.shards) {
                    await this.processSync(serverRegistry);
                }
            } catch (e) {
                console.error("Invalid Registry Received:", e);
            }
        };

        this.socket.onclose = () => {
            this.socket = null;
            this.isConnecting = false;
            // Attempt to reconnect if the institution management console is still open
            setTimeout(() => this.start(), 5000);
        };
    }

    async processSync(serverRegistry) {
        const { Filesystem } = Capacitor.Plugins;
        let localRegistry = { shards: {} };

        // 1. Load the existing local registry for comparison
        try {
            const saved = await Filesystem.readFile({
                path: this.registryPath,
                directory: 'DATA',
                encoding: 'utf8'
            });
            localRegistry = JSON.parse(saved.data);
        } catch (e) {
            console.log("Initializing local storage for the first time...");
        }

        let updatedAnything = false;

        // 2. Iterate through all shards in the server registry
        for (const section in serverRegistry.shards) {
            const serverKey = serverRegistry.shards[section];
            const localKey = localRegistry.shards[section];

            // 3. If the shard is missing or the key (version) has changed, fetch it
            if (serverKey !== localKey) {
                console.log(`Mismatch detected for [${section}]. Fetching update...`);
                const success = await this.downloadAndWriteShard(section, serverKey);
                if (success) {
                    localRegistry.shards[section] = serverKey;
                    updatedAnything = true;
                }
            }
        }

        // 4. Update the local registry file if any shards were changed
        if (updatedAnything) {
            await Filesystem.writeFile({
                path: this.registryPath,
                data: JSON.stringify(localRegistry),
                directory: 'DATA',
                encoding: 'utf8',
                recursive: true
            });
            this.showStatus("Intelligence Updated", "green");
        }
    }

    async downloadAndWriteShard(section, key) {
        try {
            // Fetch the specific missing registry data through the HTTP route
            const res = await fetch(`${this.baseUrl}/state/shard/${this.instId}/${section}?key=${key}`);
            if (!res.ok) throw new Error(`Fetch failed for ${section}`);

            const shardData = await res.json();

            // Check if data is empty to avoid overwriting good local data with nulls
            if (!shardData || (Object.keys(shardData).length === 0)) {
                console.warn(`Shard for ${section} was empty. Skipping write.`);
                return false;
            }

            const { Filesystem } = Capacitor.Plugins;
            await Filesystem.writeFile({
                path: `intelligence/${section}.json`,
                data: JSON.stringify(shardData),
                directory: 'DATA',
                encoding: 'utf8',
                recursive: true
            });
            console.log(`✅ Shard [${section}] successfully synced to local storage.`);
            return true;
        } catch (err) {
            console.error(`Sync error for ${section}:`, err);
            return false;
        }
    }

    showStatus(msg, type) {
        const color = type === 'red' ? '#f43f5e' : type === 'orange' ? '#f59e0b' : '#10b981';
        const box = document.createElement('div');
        // Red or green sign box as per instructions
        box.style = `position:fixed; bottom:20px; right:20px; padding:10px 18px; 
                     background:${color}; color:white; border-radius:8px; z-index:10000; 
                     font-size:13px; font-weight:bold; box-shadow:0 4px 12px rgba(0,0,0,0.2);`;
        box.innerText = msg;
        document.body.appendChild(box);
        setTimeout(() => box.remove(), 4000);
    }
}

// Initialize when the institution management page is ready
const intelligence = new IntelligenceManager();
document.addEventListener('DOMContentLoaded', () => intelligence.start());