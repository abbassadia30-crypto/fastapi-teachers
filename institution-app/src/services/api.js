// src/services/api.js

const API_BASE_URL = "https://fastapi-teachers.onrender.com";

/**
 * Global function to show our custom status boxes
 * (Avoiding 'alerts' as per our institution rules)
 */
export function showStatus(message, type = 'green') {
    const box = document.createElement('div');
    box.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 15px 25px;
        border-radius: 8px; color: white; font-weight: bold; z-index: 9999;
        background-color: ${type === 'green' ? '#28a745' : '#dc3545'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    box.innerText = message;
    document.body.appendChild(box);
    setTimeout(() => box.remove(), 3000);
}

export const api = {
    async getChallenges() {
        try {
            const response = await fetch(`${API_BASE_URL}/challenges`);
            if (!response.ok) throw new Error("Could not fetch challenges");
            return await response.json();
        } catch (err) {
            showStatus(err.message, 'red');
            return [];
        }
    },

    async login(credentials) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials)
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Login failed");
            showStatus("Welcome to Starlight!", "green");
            return data;
        } catch (err) {
            showStatus(err.message, 'red');
        }
    }
};