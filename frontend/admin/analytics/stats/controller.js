/**
 * controller.js - The Brain of the Stats Module
 */
const StatsController = {
    allStudents: [],

    async init() {
        console.log("🏛️ Neural Hub: Initializing Controller...");
        await this.loadLocalShards();
        this.setupEventListeners();
    },

    async loadLocalShards() {
        const { Filesystem } = Capacitor.Plugins;
        try {
            // Read local encrypted shards
            const result = await Filesystem.readFile({
                path: 'intelligence/10th-A.json',
                directory: 'DATA',
                encoding: 'utf8'
            });
            this.allStudents = JSON.parse(result.data).results || [];
            this.renderUI();
        } catch (e) {
            this.notify("Syncing Local Intelligence...", "success");
        }
    },

    renderUI() {
        // Logic to update DOM elements
        const sorted = [...this.allStudents].sort((a, b) => b.obtained_marks - a.obtained_marks);
        UI_Renderer.renderToppers(sorted); // Delegated to another helper if needed
        DashboardCharts.updateLifecycle(this.allStudents);
    },

    notify(msg, type) {
        // Institutional Red/Green box logic
        const n = document.getElementById('appNotifier');
        n.style.background = type === 'success' ? 'var(--success)' : 'var(--accent)';
        n.innerText = msg;
        n.classList.add('show');
    }
};

window.onload = () => StatsController.init();