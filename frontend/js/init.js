const { PushNotifications } = Capacitor.Plugins;

async function initializePush() {
    // 1. Request Permission
    let permission = await PushNotifications.requestPermissions();

    if (permission.receive === 'granted') {
        // 2. Register with FCM/APNS
        await PushNotifications.register();
    }

    // 3. Capture the Token
    PushNotifications.addListener('registration', async (token) => {
        const fcmToken = token.value;
        console.log("Device Token:", fcmToken);

        // Logic: Store it in AppStorage so we don't spam the server
        const savedToken = await AppStorage.get('fcm_token');
        if (savedToken !== fcmToken) {
            await syncTokenWithBackend(fcmToken);
        }
    });

    // 4. Handle incoming notifications while app is open
    PushNotifications.addListener('pushNotificationReceived', (notification) => {
        // Use your custom red/green sign box from earlier
        showNotify(`Notification: ${notification.title}`, "success");
    });
}

async function syncTokenWithBackend(token) {
    const authToken = await AppStorage.get('user_email');
    if (!authToken) return;

    try {
        await fetch(`${API_BASE}/auth/update-fcm`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ fcm_token: token })
        });
        await AppStorage.set('fcm_token', token);
    } catch (e) {
        console.error("Token sync failed", e);
    }
}

// Run on startup
document.addEventListener('DOMContentLoaded', initializePush);