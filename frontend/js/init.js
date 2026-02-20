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
    // FIX: Use the actual JWT access token, not the email
    const jwtToken = await AppStorage.get('auth_token');
    if (!jwtToken) return;

    try {
        const response = await fetch(`${API_BASE}/auth/update-fcm`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}` // Valid JWT
            },
            body: JSON.stringify({ fcm_token: token })
        });

        if(response.ok) {
            await AppStorage.set('fcm_token', token);
            console.log("FCM Token Synced Successfully");
        }
    } catch (e) {
        console.error("Token sync failed", e);
    }
}

// Run on startup
document.addEventListener('DOMContentLoaded', initializePush);