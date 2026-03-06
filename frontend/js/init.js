const { PushNotifications } = Capacitor.Plugins;

const autoInitializePush = async () => {
    // Check if plugin is actually available (Capacitor safety)
    if (!Capacitor.isPluginAvailable('PushNotifications')) {
        console.warn("Push Notifications not supported on this platform.");
        return;
    }

    const userEmail = await AppStorage.get('user_email');

    if (!userEmail) {
        console.log("No user session found. Skipping push registration.");
        return;
    }

    let permStatus = await PushNotifications.checkPermissions();
    if (permStatus.receive !== 'granted') {
        permStatus = await PushNotifications.requestPermissions();
    }

    if (permStatus.receive === 'granted') {
        await PushNotifications.register();
    }
};

// THE LISTENER - Keep this global so it catches the event after .register()
PushNotifications.addListener('registration', async (token) => {
    const userEmail = await AppStorage.get('user_email');
    const savedToken = await AppStorage.get('fcm_token');
    const authToken = await AppStorage.get('auth_token');

    if (token.value !== savedToken) {
        console.log("New Token detected! Syncing with FastAPI...");
        await AppStorage.set('fcm_token', token.value);

        if (userEmail && authToken) {
            try {
                await fetch('https://fastapi-teachers.onrender.com/auth/users/update-push-token', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({ token: token.value })
                });
                console.log("✅ FastAPI Address Book Updated.");
            } catch (err) {
                console.error("❌ Sync failed:", err);
            }
        }
    }
});

// REMOVED: autoInitializePush(); -> We call this manually in the gatekeeper now.