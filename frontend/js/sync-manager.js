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

        try {
            const saved = await Filesystem.readFile({
                path: this.registryPath,
                directory: 'DATA',
                encoding: 'utf8'
            });
            localRegistry = JSON.parse(saved.data);
        } catch (e) { console.log("Executor: Fresh start."); }

        let modified = false;

        for (const section in serverRegistry.shards) {
            if (serverRegistry.shards[section] !== localRegistry.shards[section]) {
                const success = await this.executeShardFetch(section, serverRegistry.shards[section]);
                if (success) {
                    localRegistry.shards[section] = serverRegistry.shards[section];
                    modified = true;
                }
            }
        }

        if (modified) {
            await Filesystem.writeFile({
                path: this.registryPath,
                data: JSON.stringify(localRegistry),
                directory: 'DATA',
                encoding: 'utf8',
                recursive: true
            });
            // Notify UI
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