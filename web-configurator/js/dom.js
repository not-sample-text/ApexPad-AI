export const dom = {
    macropad: document.querySelector(".macropad-container"),
    title: document.getElementById("layer-title"),
    dragHint: document.getElementById("drag-hint"),
    sidebar: document.getElementById("main-sidebar"),
    hamburger: document.getElementById("hamburger-btn"),
    keys: document.querySelectorAll(".macropad-container .key"),
    oled: {
        layerName: document.getElementById("oled-layer-name"),
        mainText: document.getElementById("oled-display-text")
    },
    knob: {
        container: document.querySelector(".rotary-encoder"),
        element: document.querySelector(".knob")
    },
    modal: {
        overlay: document.getElementById("config-modal"),
        keyId: document.getElementById("modal-key-id"),
        labelInput: document.getElementById("key-label"),
        shortcutDisplay: document.getElementById("shortcut-display"),
        shortcutValue: document.getElementById("shortcut-value"),
        scriptDisplay: document.getElementById("script-path-display"),
        appInput: document.getElementById("app-path-input"),
        execOptions: document.getElementById("execution-options"),
        runAdmin: document.getElementById("opt-run-admin"),
        runHeadless: document.getElementById("opt-run-headless"),
        cancelBtn: document.getElementById("btn-cancel"),
        resetBtn: document.getElementById("btn-reset"),
        saveBtn: document.getElementById("btn-save"),
        samplePrompt: document.getElementById("sample-prompt"),
        sampleLoadBtn: document.getElementById("btn-sample-load"),
        sampleCancelBtn: document.getElementById("btn-sample-cancel")
    },
    welcome: {
        overlay: document.getElementById("welcome-modal"),
        loadBtn: document.getElementById("btn-welcome-load"),
        skipBtn: document.getElementById("btn-welcome-skip")
    },
    ai: {
        widget: document.getElementById("ai-chat-widget"),
        header: document.getElementById("ai-chat-header"),
        toggleBtn: document.getElementById("btn-ai-toggle"),
        toggleIcon: document.getElementById("ai-toggle-icon"),
        settingsBtn: document.getElementById("btn-ai-settings"),
        settingsDrawer: document.getElementById("ai-settings-drawer"),
        targetLayer: document.getElementById("ai-target-layer"),
        modelInput: document.getElementById("ai-model-input"),
        chatLog: document.getElementById("ai-chat-log"),
        promptInput: document.getElementById("ai-prompt-input"),
        optimizeBtn: document.getElementById("btn-ai-optimize"),
        banner: document.getElementById("ai-sandbox-banner"),
        bannerSummary: document.getElementById("ai-sandbox-summary"),
        acceptBtn: document.getElementById("btn-ai-accept"),
        discardBtn: document.getElementById("btn-ai-discard")
    },
    debug: {
        statusPill: document.getElementById("device-status-pill"),
        statusText: document.getElementById("device-status-text"),
        openBtn: document.getElementById("btn-open-debug"),
        modal: document.getElementById("debug-modal"),
        closeBtn: document.getElementById("btn-close-debug"),
        portVal: document.getElementById("debug-port-val"),
        syncVal: document.getElementById("debug-sync-val"),
        keysVal: document.getElementById("debug-keys-val"),
        layersVal: document.getElementById("debug-layers-val"),
        recoverBtn: document.getElementById("btn-recover-pad"),
        forceDumpBtn: document.getElementById("btn-force-dump"),
        resetTelemetryBtn: document.getElementById("btn-reset-telemetry"),
        clearLogsBtn: document.getElementById("btn-clear-logs"),
        logOutput: document.getElementById("debug-log-output")
    },
    exportBtn: document.getElementById("btn-export-json"),
    importBtn: document.getElementById("btn-import-json"),
    importInput: document.getElementById("import-file-input"),
    uploadBtn: document.getElementById("btn-upload-pad")
};
