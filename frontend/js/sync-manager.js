/**
 * Institutional Intelligence | Execution Engine
 * Handles: Logic, HTTP fetching, and Disk I/O.
 */
class IntelligenceExecutor {
    constructor() {
        this.baseUrl = "https://fastapi-teachers.onrender.com";
        this.registryPath = 'intelligence/registry.json';
    }

    async reconcile(serverRegistry) {
        const { Filesystem } = Capacitor.Plugins;
        let localRegistry = { shards: {} };

        // 📂 1. Load Local State
        try {
            const saved = await Filesystem.readFile({
                path: this.registryPath,
                directory: 'DATA',
                encoding: 'utf8'
            });
            localRegistry = JSON.parse(saved.data);
        } catch (e) {
            console.log("Executor: Fresh start/Registry missing.");
        }

        let modified = false;

        // 🔄 2. Process the Server's Map
        // 'section' is the key (e.g., "9th-A"), 'serverKey' is the value
        for (const [section, serverKey] of Object.entries(serverRegistry.shards)) {
            const localKey = localRegistry.shards[section];

            // 🗑️ SITUATION: TOTAL DELETION
            // If the backend explicitly maps this specific section name to null
            if (serverKey === null || serverKey === "EMPTY") {
                if (localKey) {
                    console.warn(`Cleaning: Section ${section} is now empty/deleted.`);
                    try {
                        await Filesystem.deleteFile({
                            path: `intelligence/${section}.json`,
                            directory: 'DATA'
                        });
                    } catch (err) { /* File already gone */ }

                    delete localRegistry.shards[section];
                    modified = true;
                }
                continue;
            }

            // 📥 SITUATION: DATA UPDATE (Student deleted/added)
            // Since the section name (e.g., "9th-A") is the same, but the hash
            // changed, it fetches the specific file for THAT section name.
            if (serverKey !== localKey) {
                console.log(`Syncing: ${section} (Key change detected)`);
                const success = await this.executeShardFetch(section, serverKey);
                if (success) {
                    localRegistry.shards[section] = serverKey;
                    modified = true;
                }
            }
        }

        // 💾 3. Finalize
        if (modified) {
            await Filesystem.writeFile({
                path: this.registryPath,
                data: JSON.stringify(localRegistry),
                directory: 'DATA',
                encoding: 'utf8'
            });

            // Trigger the Super Console to refresh its view
            window.dispatchEvent(new CustomEvent('intelligence-updated'));
        }
    }

    async executeShardFetch(section, key) {
        try {
            const instId = await AppStorage.get('institution_id');
            const res = await fetch(`${this.baseUrl}/state/shard/${instId}/${section}?key=${key}`);
            if (!res.ok) return false;

            const data = await res.json();
            await Capacitor.Plugins.Filesystem.writeFile({
                path: `intelligence/${section}.json`,
                data: JSON.stringify(data),
                directory: 'DATA',
                encoding: 'utf8',
                recursive: true
            });
            return true;
        } catch (e) { return false; }
    }
}

window.IntelligenceExecutor = new IntelligenceExecutor();