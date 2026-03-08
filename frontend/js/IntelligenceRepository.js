/**
 * 🏛️ Intelligence Repository (The Manager)
 * Concept: Data Sovereignty & Disk Persistence
 */
const IntelligenceRepository = {
    registryPath: 'intelligence/registry.json',

    async reconcile(serverRegistry) {
        const { Filesystem } = Capacitor.Plugins;
        let localRegistry = { shards: {} };

        // 1. Load Local Manifest
        try {
            const res = await Filesystem.readFile({
                path: this.registryPath,
                directory: 'DATA',
                encoding: 'utf8'
            });
            localRegistry = JSON.parse(res.data);
        } catch (e) { /* New Install */ }

        let modified = false;

        for (const [section, instruction] of Object.entries(serverRegistry.shards)) {
            const localKey = localRegistry.shards[section]?.key;

            // Phenomenon: Targeted Deletion
            if (instruction.mode === "delete") {
                await Filesystem.deleteFile({ path: `intelligence/${section}.json`, directory: 'DATA' }).catch(()=>{});
                delete localRegistry.shards[section];
                modified = true;
                window.dispatchEvent(new CustomEvent(`clear-ui-${section}`));
            }

            // Phenomenon: Versioned Update
            else if (instruction.mode === "update" && instruction.key !== localKey) {
                const success = await this.downloadShard(section, instruction.key);
                if (success) {
                    localRegistry.shards[section] = instruction;
                    modified = true;
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
            // Android Concept: Broadcast the update
            window.dispatchEvent(new CustomEvent('intelligence-ready'));
        }
    },

    async downloadShard(section, key) {
        try {
            const instId = await AppStorage.get('institution_id');
            const res = await fetch(`https://fastapi-teachers.onrender.com/state/shard/${instId}/${section}?key=${key}`);
            const data = await res.json();

            window.dispatchEvent(new CustomEvent(`clear-ui-${section}`));

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
};
window.IntelligenceRepository = IntelligenceRepository;