/**
 * init.js - Super Console Notification & Initialization logic
 * Purpose: Move institutions to a paperless system with real-time alerts.
 */

const { PushNotifications } = Capacitor.Plugins;

async function initializePush() {
    console.log("Initializing Starlight Push System...");

    // 1. Mandatory Android Channel (Urgent Importance for Institution Alerts)
    if (Capacitor.getPlatform() === 'android') {
        try {
            await PushNotifications.createChannel({
                id: 'institution_alerts',
                name: 'Institution Alerts',
                description: 'Critical updates for staff and students',
                importance: 5, // 5 = Urgent/Pop-up (essential for high-priority alerts)
                visibility: 1, // Visible on lockscreen
                lights: true,
                lightColor: '#43a047',
                vibration: true,
            });
            console.log("Notification channel 'institution_alerts' created.");
        } catch (e) {
            console.error("Failed to create channel:", e);
        }
    }

    // 2. Check and Request Permissions
    let permStatus = await PushNotifications.checkPermissions();

    if (permStatus.receive === 'prompt') {
        permStatus = await PushNotifications.requestPermissions();
    }

    if (permStatus.receive !== 'granted') {
        console.warn("User denied push permissions. Alerts will not be received.");
        return;
    }

    // 3. Setup Listeners BEFORE Registering (Ensures no data is dropped)
    setupPushListeners();

    // 4. Register Device with FCM
    await PushNotifications.register();
}

function setupPushListeners() {
    // 📍 Registration: Capture the FCM Token
    PushNotifications.addListener('registration', async (token) => {
        const fcmToken = token.value;
        console.log("Device Registered. Token:", fcmToken);

        const savedToken = await AppStorage.get('fcm_token');
        if (savedToken !== fcmToken) {
            await syncTokenWithBackend(fcmToken);
        }
    });

    // 📍 Registration Error: Debugging for Capacitor
    PushNotifications.addListener('registrationError', (error) => {
        console.error("FCM Registration Error:", JSON.stringify(error));
    });

    // 📍 Foreground Alert: Displayed when app is OPEN
    PushNotifications.addListener('pushNotificationReceived', (notification) => {
        // Using your requirement: Green box for success/info alerts
        if (typeof showNotify === 'function') {
            showNotify(`${notification.title}: ${notification.body}`, "success");
        } else {
            console.log("Notification received in foreground:", notification);
        }
    });

    // 📍 Tap Action: Logic for when user clicks the notification
    PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
        const data = action.notification.data;
        console.log("User tapped notification. Data:", data);

        // Logic for Mailbox/Chat redirection
        if (data.type === 'mailbox') {
            window.location.href = '../mailbox/inbox.html';
        } else if (data.type === 'chat') {
            window.location.href = '../chat/whatsapp_clone.html';
        }
    });
}

/**
 * Syncs the device FCM token with the FastAPI backend
 */
async function syncTokenWithBackend(token) {
    // Use the actual JWT access token as per your login logic
    const jwtToken = await AppStorage.get('auth_token');
    if (!jwtToken) {
        console.warn("Cannot sync FCM token: No auth_token found.");
        return;
    }

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
            await AppStorage.set('fcm_token', token);
            console.log("Backend FCM Sync: SUCCESS");
        } else {
            const errData = await response.json();
            console.error("Backend FCM Sync: FAILED", errData.detail);
        }
    } catch (e) {
        console.error("Backend FCM Sync: CONNECTION ERROR", e);
    }
}

// Ensure initialization runs after DOM and Storage are ready
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure AppStorage (Capacitor Preferences) is fully linked
    setTimeout(initializePush, 500);
});