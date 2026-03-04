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
    // This fires when a notification arrives
    PushNotifications.addListener('pushNotificationReceived', (notification) => {
        console.log('🏛️ Alert Received:', notification);
        // Use your "No Alerts" rule: Show a Green/Red box instead of window.alert
        if(window.showSignBox) {
            window.showSignBox(notification.body, "green"); [cite, 2025-12-22]
        }
    });

    // This fires when the user TAPS the notification (even if app was killed)
    PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
        console.log('🏛️ Action Performed:', notification.actionId);
        // Logic to navigate to the specific Mailbox or Wallet
        window.location.href = 'mailbox.html';
    });

    PushNotifications.addListener('registration', async (token) => {
        await AppStorage.set('fcm_token', token.value);
        await syncTokenWithBackend(token.value);
        resolve(token.value);
    });
}
async function syncTokenWithBackend(token) {
    const jwtToken = await AppStorage.get('auth_token');
    if (!jwtToken) return;
    API_BASE = "https://fastapi-teachers.onrender.com";

    try {
        const response = await fetch(`${API_BASE}/auth/update-fcm`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({ fcm_token: token })
        });

        if (!response.ok) {
            console.error("❌ Neural Link Sync Failed");
            // If the user is no longer in DB, show red box [cite: 2025-12-22]
            if(window.showSignBox) window.showSignBox("Sync Failed: Re-login required", "error");
        }
    } catch (e) {
        console.error("Network Error during Sync:", e);
    }
}

// Auto-run if user session exists
document.addEventListener('DOMContentLoaded', async () => {
    const hasToken = await AppStorage.get('auth_token');
    if (hasToken) {
        setTimeout(window.initializePush, 1000);
    }
});