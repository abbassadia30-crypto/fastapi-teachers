/**
 * init.js - Institutional Intelligence Notification System
 * Purpose: Digitalize paper-based alerts with 100% delivery reliability.
 */
const { PushNotifications } = Capacitor.Plugins;

window.initializePush = function() {
    return new Promise(async (resolve) => {
        console.log("🏛️ Neural Link: Initializing...");

        // 1. Create the Android Urgent Channel
        if (Capacitor.getPlatform() === 'android') {
            try {
                await PushNotifications.createChannel({
                    id: 'institution_alerts',
                    name: 'Institution Alerts',
                    importance: 5, // Urgent pop-up
                    visibility: 1,
                    lights: true,
                    lightColor: '#43a047',
                    vibration: true,
                });
            } catch (e) { console.error("Channel Error:", e); }
        }

        // 2. Request Permissions
        let permStatus = await PushNotifications.checkPermissions();
        if (permStatus.receive === 'prompt') {
            permStatus = await PushNotifications.requestPermissions();
        }

        if (permStatus.receive === 'granted') {
            // Setup listeners before registering
            setupPushListeners(resolve);

            // 🚀 FORCE CHECK: If we already have a token, sync it now
            // even before the 'registration' event fires.
            const cachedToken = await AppStorage.get('fcm_token');
            const jwt = await AppStorage.get('auth_token');
            if (cachedToken && jwt) {
                console.log("🔄 Re-verifying existing token with DB...");
                await syncTokenWithBackend(cachedToken);
            }

            await PushNotifications.register();

            // Safety timeout: resolve if FCM takes too long
            setTimeout(() => resolve(null), 8000);
        } else {
            console.warn("Push Access Denied");
            resolve(null);
        }
    });
};

function setupPushListeners(resolve) {
    // Clear old listeners to prevent duplicate requests
    PushNotifications.removeAllListeners();

    PushNotifications.addListener('registration', async (token) => {
        console.log("🛰️ Device Registered. Token:", token.value);
        await AppStorage.set('fcm_token', token.value);

        // Always attempt sync if logged in
        const jwt = await AppStorage.get('auth_token');
        if (jwt) {
            await syncTokenWithBackend(token.value);
        }
        resolve(token.value);
    });

    PushNotifications.addListener('registrationError', (err) => {
        console.error("FCM Registration Error:", err);
        resolve(null);
    });
}

async function syncTokenWithBackend(token) {
    const jwtToken = await AppStorage.get('auth_token');
    if (!jwtToken) return;
    API_BASE = "https://fastapi-teachers.onrender.com";

    try {
        console.log("📤 Syncing Token to Institution DB...");
        const response = await fetch(`${API_BASE}/auth/update-fcm`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({ fcm_token: token })
        });

        if (response.ok) {
            console.log("✅ Neural Link Active: Token Tied to Email");
        }
    } catch (e) {
        console.error("Neural Link Failure:", e);
    }
}

// Auto-run if user session exists
document.addEventListener('DOMContentLoaded', async () => {
    const hasToken = await AppStorage.get('auth_token');
    if (hasToken) {
        setTimeout(window.initializePush, 1000);
    }
});