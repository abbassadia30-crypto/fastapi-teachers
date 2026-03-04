import OneSignal from 'onesignal-cordova-plugin';

export const setupNotifications = async (myInternalUserId) => {
    // 1. Initialize
    OneSignal.setAppId("94695d55-27d6-4fb4-bb47-e98e167728cb");

    // 2. Link your Database User ID to OneSignal (Recommended!)
    // This lets you send notifications using your own User ID later
    OneSignal.setExternalUserId(myInternalUserId.toString());

    // 3. Get the OneSignal 'Subscription ID' (the "Token")
    OneSignal.getDeviceState((state) => {
        const onesignalId = state.userId; // This is the unique key for this phone

        if (onesignalId) {
            // 4. Send this to your FastAPI backend
            saveTokenToBackend(myInternalUserId, onesignalId);
        }
    });
};

async function saveTokenToBackend(userId, token) {
    await fetch('https://fastapi-teachers.onrender.com/auth/users/update-push-token', { ... }, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, push_token: token })
    });
}