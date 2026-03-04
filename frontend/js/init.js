/**
 * init.js - Super Console Notification Logic
 * Purpose: Ensure real-time alerts for the paperless institution.
 */

const setupNotifications = async (myInternalUserId) => {
    return new Promise((resolve) => {
        // Check if OneSignal is available (Capacitor Environment)
        if (typeof window.plugins === 'undefined' || !window.plugins.OneSignal) {
            console.warn("OneSignal plugin not found. Skipping sync.");
            return resolve(false);
        }

        const OneSignal = window.plugins.OneSignal;

        // 1. Initialize with your App ID
        OneSignal.setAppId("94695d55-27d6-4fb4-bb47-e98e167728cb");

        // 2. Link External ID for targeted mailbox/chat alerts [cite: 2026-02-19]
        OneSignal.setExternalUserId(myInternalUserId.toString());

        // 3. Get Device State & Sync to FastAPI
        OneSignal.getDeviceState(async (state) => {
            const onesignalId = state.userId;
            if (onesignalId) {
                const success = await saveTokenToBackend(myInternalUserId, onesignalId);
                resolve(success);
            } else {
                resolve(false);
            }
        });
    });
};

async function saveTokenToBackend(userId, token) {
    try {
        const response = await fetch('https://fastapi-teachers.onrender.com/auth/users/update-push-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, push_token: token })
        });
        return response.ok;
    } catch (e) {
        console.error("FCM Sync Error:", e);
        return false;
    }
}