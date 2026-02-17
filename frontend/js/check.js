// js/checking.js
const API_BASE = "https://fastapi-teachers.onrender.com";

async function checkUserExistence() {
    try {
        // 1. Fetch Local State
        const email = await AppStorage.get('user_email');
        const token = await AppStorage.get('institutionToken');

        // SECURITY GATE: If no credentials, force back to login
        if (!email || !token) {
            if (!window.location.pathname.endsWith('index.html')) {
                window.location.href = "../../index.html";
            }
            return;
        }

        // 2. REMOTE SYNC (The Truth from DB)
        // We do this to handle Reinstalls, Deletions, or Role Changes
        const response = await fetch(`${API_BASE}/auth/sync-state`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const server = await response.json();

            // Sync local storage with Server truth
            await AppStorage.set("user_role", server.user_role);
            await AppStorage.set("institution_id", server.institution_id);

            // Handle Identity Token sync
            if (server.has_identity) {
                await AppStorage.set(`${server.user_role}_identity`, "verified");
            } else {
                await AppStorage.remove(`${server.user_role}_identity`);
            }

            // 3. NAVIGATION LOGIC (The "State Machine")
            const role = server.user_role;
            const instID = server.institution_id;
            const hasIden = server.has_identity;

            let targetPath = "";

            if (!role || role === "verified_user") {
                targetPath = "roles/role.html";
            }
            else if (!hasIden) {
                // Determine folder structure based on role
                const idFolder = (role === 'owner' || role === 'admin') ? `${role}_identity` : 'setups';
                targetPath = `${role}/${idFolder}/create_identity.html`;
            }
            else if (!instID) {
                // UNIVERSAL HANDLER: Everyone goes here if they have no institution
                targetPath = `${role}/setups/no-institution.html`;
            }
            else {
                // FULL ACCESS
                targetPath = `${role}/dashboard/dashboard.html`;
            }

            // 4. THE REALITY REDIRECT
            // We use includes to check if the current page is where they belong
            if (!window.location.href.includes(targetPath)) {
                console.log(`State mismatch detected. Bouncing to: ${targetPath}`);
                // Use absolute-style pathing for Capacitor stability
                window.location.href = `../../${targetPath}?token=${email}`;
            } else {
                // If they are where they belong, reveal the content
                document.body.classList.add('state-verified');
            }
        }
        else {
            // Logic: The token is dead or user doesn't exist in DB
            console.warn("Unauthorized: Clearing stale credentials.");
            await AppStorage.remove('user_email');
            await AppStorage.remove('institutionToken');

            // If we are already on index.html, reveal it so they can log in.
            // If not, send them there.
            if (window.location.pathname.endsWith('index.html')) {
                document.body.classList.add('state-verified');
            } else {
                window.location.href = "../index.html";
            }
        }
    } catch (e) {
        console.warn("Reality Check: Server Wake-up or Offline. Trusting Local Storage.");
        document.body.classList.add('state-verified');
    }
}

// 5. AUTO-EXECUTION
document.addEventListener('DOMContentLoaded', () => {
    // Inject a tiny bit of CSS to prevent flicker
    const style = document.createElement('style');
    style.innerHTML = `body { opacity: 0; transition: opacity 0.2s; } body.state-verified { opacity: 1; }`;
    document.head.appendChild(style);

    checkUserExistence();
});