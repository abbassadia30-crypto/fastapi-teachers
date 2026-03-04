/**
 * init.js - Super Console Notification & Initialization logic
 */
const { PushNotifications } = Capacitor.Plugins;

window.initializePush = function() {
    return new Promise(async (resolve) => {
        console.log("🏛️ Institutional Intelligence: Starting Push Handshake...");

        // ... (Keep your channel and permission logic) ...

        if (permStatus.receive === 'granted') {
            setupPushListeners();

            // 🚀 CHECK IF TOKEN EXISTS ALREADY
            const existingFcmToken = await AppStorage.get('fcm_token');
            const jwtToken = await AppStorage.get('auth_token');

            if (existingFcmToken && jwtToken) {
                console.log("Found existing token, syncing immediately...");
                await syncTokenWithBackend(existingFcmToken);
                await PushNotifications.register(); // Keep it registered
                resolve(existingFcmToken);
                return;
            }

            // If no existing token, wait for the registration listener
            await PushNotifications.register();

            // Fallback timeout so login doesn't hang if FCM fails
            setTimeout(() => resolve(null), 5000);
        } else {
            resolve(null);
        }
    });
};

function setupPushListeners() {
    PushNotifications.removeAllListeners(); // Prevent duplicate listeners

    PushNotifications.addListener('registration', async (token) => {
        const fcmToken = token.value;
        console.log("Device Registered. Token:", fcmToken);
        await AppStorage.set('fcm_token', fcmToken);

        const jwtToken = await AppStorage.get('auth_token');
        if (jwtToken) {
            await syncTokenWithBackend(fcmToken);
        }
        // This resolves the promise in initializePush
        if (window.registrationResolver) window.registrationResolver(fcmToken);
    });
}

async function syncTokenWithBackend(token) {
    const jwtToken = await AppStorage.get('auth_token');
    if (!jwtToken) return;

    try {
        const response = await fetch(`${API_BASE}/auth/update-fcm`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({ fcm_token: token })
        });

        if (response.ok) {
            console.log("🏛️ Institutional DB: FCM Token Synced");
        }
    } catch (e) { console.error("Sync Error:", e); }
}

// Global foreground listener (needs to be outside the promise)
PushNotifications.addListener('pushNotificationReceived', (notification) => {
    if (typeof showNotify === 'function') {
        showNotify(`${notification.title}: ${notification.body}`, "success");
    }
});

// Auto-run on load ONLY if user is already logged in
document.addEventListener('DOMContentLoaded', async () => {
    const loggedIn = await AppStorage.get('auth_token');
    if (loggedIn) {
        setTimeout(window.initializePush, 500);
    }
});