/**
 * charts.js - High-Performance Graphics
 */
const DashboardCharts = {
    lifecycle: null,

    initLifecycle(ctx) {
        this.lifecycle = new Chart(ctx, {
            type: 'line',
            data: { /* ... data ... */ },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 2000, easing: 'easeOutQuart' }
            }
        });
    },

    updateLifecycle(data) {
        // Smoothly update the graph without flickering
        this.lifecycle.data.datasets[0].data = data.map(s => s.obtained_marks);
        this.lifecycle.update('none'); // Update without full re-render for speed
    }
};