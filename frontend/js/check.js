// js/check.js
const API_BASE = "https://fastapi-teachers.onrender.com";

// ────────────────────────────────────────────────
// Fast local decision – no await, no promises
// ────────────────────────────────────────────────
function getLocalTargetPath() {
    const email    = AppStorage.getSync ? AppStorage.getSync('user_email')    : null;
    const token    = AppStorage.getSync ? AppStorage.getSync('institutionToken') : null;
    const role     = AppStorage.getSync ? AppStorage.getSync('user_role')     : null;
    const instID   = AppStorage.getSync ? AppStorage.getSync('institution_id') : null;
    const hasIden  = AppStorage.getSync ? AppStorage.getSync(`${role}_identity`) === "verified" : false;

    if (!email || !token) {
        return "index.html";
    }

    if (!role || role === "verified_user") {
        return "roles/role.html";
    }

    const base = (role === "owner" || role === "admin") ? "admin" : role;

    if (hasIden && instID) {
        return `${base}/dashboard/dashboard.html`;
    }
    if (hasIden && !instID) {
        return `${base}/setups/no-institution.html`;
    }

    // no identity yet
    const folder = (role === "owner") ? "owner_identity" : "admin_identity";
    return (role === "owner" || role === "admin")
        ? `admin/${folder}/create_identity.html`
        : `${role}/setups/create_identity.html`;
}

// ────────────────────────────────────────────────
// Background validation – never blocks UI
// ────────────────────────────────────────────────
async function silentBackendSync() {
    const token = await AppStorage.get('institutionToken');
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/auth/sync-state`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
            // Token invalid → logout
            await AppStorage.clearAll?.(); // or implement your own clear function
            if (!window.location.pathname.includes('index.html')) {
                window.location.replace('../index.html');
            }
            return;
        }

        const server = await res.json();

        let changed = false;

        const localRole = await AppStorage.get('user_role');
        if (server.user_role !== localRole) {
            await AppStorage.set('user_role', server.user_role);
            changed = true;
        }

        const localInst = await AppStorage.get('institution_id');
        if (server.institution_id !== localInst) {
            await AppStorage.set('institution_id', server.institution_id);
            changed = true;
        }

        const identityKey = `${server.user_role}_identity`;
        const localHasIden = (await AppStorage.get(identityKey)) === "verified";

        if (server.has_identity !== localHasIden) {
            if (server.has_identity) {
                await AppStorage.set(identityKey, "verified");
            } else {
                await AppStorage.remove(identityKey);
            }
            changed = true;
        }

        if (changed) {
            const expected = getLocalTargetPath();
            if (!window.location.pathname.includes(expected)) {
                window.location.replace(`../../${expected}`);
            }
        }
    } catch (err) {
        // Offline → local wins
        console.debug("[silent sync] offline / failed → using local state", err);
    }
}

// ────────────────────────────────────────────────
// Main entry point – called on every page
// ────────────────────────────────────────────────
function initializePage() {
    const currentPath = window.location.pathname.toLowerCase();
    const isLoginPage =
        currentPath.endsWith('index.html') ||
        currentPath === '/' ||
        currentPath === '' ||
        currentPath.endsWith('/');

    // 1. Login page → always show immediately + background check only
    if (isLoginPage) {
        document.body.classList.add('state-verified');
        silentBackendSync(); // fire & forget
        return;
    }

    // 2. Protected pages → decide target + redirect if wrong
    const target = getLocalTargetPath();

    if (!currentPath.includes(target.toLowerCase())) {
        window.location.replace(`../../${target}`);
        return;
    }

    // Correct page → reveal + background sync
    document.body.classList.add('state-verified');
    silentBackendSync();
}

// Execute when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}