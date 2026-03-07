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

        // 📂 Load Local Map
        try {
            const saved = await Filesystem.readFile({
                path: this.registryPath,
                directory: 'DATA',
                encoding: 'utf8'
            });
            localRegistry = JSON.parse(saved.data);
        } catch (e) { console.log("Fresh Registry required."); }

        let modified = false;

        // 🔄 Loop through the Commands (Shards)
        for (const [section, instruction] of Object.entries(serverRegistry.shards)) {
            const localData = localRegistry.shards[section] || { key: null };

            // 🛑 BRANCH 1: DELETE MODE
            if (instruction.mode === "delete") {
                if (localRegistry.shards[section]) {
                    console.warn(`🏛️ Cleanup Command: Deleting ${section}`);
                    try {
                        await Filesystem.deleteFile({
                            path: `intelligence/${section}.json`,
                            directory: 'DATA'
                        });
                    } catch (e) { /* Already gone */ }

                    delete localRegistry.shards[section];
                    modified = true;
                }
                continue;
            }

            // 📥 BRANCH 2: UPDATE MODE
            if (instruction.mode === "update") {
                // Check if the server's key for this section differs from our local key
                if (instruction.key !== localData.key) {
                    console.log(`🏛️ Sync Command: Fetching ${section}`);
                    const success = await this.executeShardFetch(section, instruction.key);
                    if (success) {
                        // Save the whole instruction object {key, mode} locally
                        localRegistry.shards[section] = instruction;
                        modified = true;
                    }
                }
            }
        }

        if (modified) {
            await Filesystem.writeFile({
                path: this.registryPath,
                data: JSON.stringify(localRegistry),
                directory: 'DATA',
                encoding: 'utf8'
            });
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