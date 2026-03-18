const LEGACY_SCRIPT_URLS = [
    "/static/js/socket.io.min.js",
    "/static/js/crypto-js.min.js",
    "/static/js/utils.js?v=4.8",
    "/static/js/i18n.js?v=4.9",
    "/static/js/toast.js?v=4.8",
    "/static/js/theme.js?v=4.8",
    "/static/js/auth.js?v=4.8",
    "/static/js/profile.js?v=4.8",
    "/static/js/features.js?v=4.8",
    "/static/js/rooms.js?v=4.8",
    "/static/js/messages.js?v=4.8",
    "/static/js/socket-handlers.js?v=4.8",
    "/static/js/storage.js?v=4.8",
    "/static/js/notification.js?v=4.8",
    "/static/js/app.js?v=4.8",
];

let bootPromise = null;

function loadLegacyScript(src) {
    const existing = document.querySelector(`script[data-legacy-src="${src}"]`);
    if (existing) {
        return Promise.resolve();
    }
    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = src;
        script.async = false;
        script.defer = false;
        script.dataset.legacySrc = src;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load legacy script: ${src}`));
        document.head.appendChild(script);
    });
}

export function initApp() {
    if (bootPromise) {
        return bootPromise;
    }
    bootPromise = (async () => {
        for (const src of LEGACY_SCRIPT_URLS) {
            await loadLegacyScript(src);
        }
        window.__messengerLegacyBooted = true;
    })().catch((error) => {
        console.error("[messenger] legacy bootstrap failed", error);
        throw error;
    });
    return bootPromise;
}

void initApp();
