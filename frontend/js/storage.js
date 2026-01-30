/**
 * Global Storage Utility for Capacitor Preferences
 * Handles the bridge between native storage and your JS logic.
 */
const { Preferences } = Capacitor.Plugins;

const AppStorage = {
    // Save data - always converts value to string for Capacitor safety
    async set(key, value) {
        try {
            await Preferences.set({
                key: key,
                value: String(value)
            });
            return true;
        } catch (e) {
            console.error(`Error setting ${key}:`, e);
            return false;
        }
    },

    // Get data - returns the raw string value or null
    async get(key) {
        try {
            const { value } = await Preferences.get({ key: key });
            return value;
        } catch (e) {
            console.error(`Error getting ${key}:`, e);
            return null;
        }
    },

    // Remove a specific key
    async remove(key) {
        try {
            await Preferences.remove({ key: key });
        } catch (e) {
            console.error(`Error removing ${key}:`, e);
        }
    },

    // Clear all app data (Useful for Logout)
    async clear() {
        try {
            await Preferences.clear();
        } catch (e) {
            console.error("Error clearing storage:", e);
        }
    }
};

async function hardResetApp() {
    // 1. Clear all local keys
    await AppStorage.remove('institutionToken');
    await AppStorage.remove('current_institution_name');
    await AppStorage.remove('cached_staff_list');
    // ... add any other keys you use

    // 2. Clear Capacitor Preferences entirely
    if (window.Capacitor) {
        // This is the "Nuclear Option" for storage
        await AppStorage.clear();
    }

    // 3. Send back to the very beginning
    window.location.replace("../../index.html");
}

window.hardResetApp = hardResetApp;

// Export it for use in other scripts
window.AppStorage = AppStorage;