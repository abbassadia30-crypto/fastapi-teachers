// js/init.js
const { PushNotifications } = Capacitor.Plugins;

const autoInitializePush = async () => {
    // 🏛️ Logic: Use the correct spelling 'AppStorage'
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

// THE LISTENER
PushNotifications.addListener('registration', async (token) => {
    // 🏛️ CRITICAL: We must fetch all 3 pieces of data from the 'Pocket'
    const userEmail = await AppStorage.get('user_email');
    const savedToken = await AppStorage.get('fcm_token');
    const authToken = await AppStorage.get('auth_token'); // Don't forget this!

    if (token.value !== savedToken) {
        console.log("New Token detected! Syncing with FastAPI...");

        await AppStorage.set('fcm_token', token.value);

        if (userEmail && authToken) {
            try {
                await fetch('https://fastapi-teachers.onrender.com/auth/users/update-push-token', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}` // Now it's defined!
                    },
                    body: JSON.stringify({
                        token: token.value
                    })
                });
                console.log("✅ FastAPI Address Book Updated.");
            } catch (err) {
                console.error("❌ Sync failed:", err);
            }
        }
    }
});

autoInitializePush();