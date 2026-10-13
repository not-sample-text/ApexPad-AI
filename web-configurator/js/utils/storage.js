import { configData, defaultLayer1Keys, state } from "../state.js";
import { KeyHandler } from "../handlers/key.js";
import { SidebarHandler } from "../handlers/sidebar.js";

export const PersistenceHandler = {
    STORAGE_KEY: "macropad_config_v2",

    saveToLocal: () => {
        try {
            localStorage.setItem(
                PersistenceHandler.STORAGE_KEY,
                JSON.stringify(configData)
            );
        } catch (e) {
            console.warn("LocalStorage failed:", e);
        }

        // Also persist to local Python daemon if running
        fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config: configData })
        }).catch(() => {});
    },

    loadFromBackendOrLocal: async () => {
        try {
            const res = await fetch("/api/config", { cache: "no-store" });
            if (res.ok) {
                const data = await res.json();
                if (
                    data &&
                    Array.isArray(data.layers) &&
                    data.layers.length > 0
                ) {
                    PersistenceHandler.applyConfig(data);
                    localStorage.setItem(
                        PersistenceHandler.STORAGE_KEY,
                        JSON.stringify(configData)
                    );
                    return true;
                }
            }
        } catch (_) {
            // Offline static file fallback
        }
        return PersistenceHandler.loadFromLocal();
    },

    loadFromLocal: () => {
        const saved = localStorage.getItem(PersistenceHandler.STORAGE_KEY);
        if (saved) {
            try {
                let parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) {
                    parsed = { layers: parsed };
                }
                PersistenceHandler.applyConfig(parsed);
                return true;
            } catch (e) {
                console.error("Corrupt data, clearing storage.", e);
                localStorage.removeItem(PersistenceHandler.STORAGE_KEY);
                return false;
            }
        }
        return false;
    },

    applyConfig: (newData) => {
        if (!newData || !Array.isArray(newData.layers)) {
            throw new Error("Invalid Config Structure");
        }

        configData.layers = newData.layers;

        const incomingLayer0 = newData.layers[0]?.keys || {};
        configData.layers[0].keys = {};

        for (const keyId in defaultLayer1Keys) {
            const customLabel = incomingLayer0[keyId]?.label;
            configData.layers[0].keys[keyId] = {
                label: customLabel
                    ? customLabel
                    : defaultLayer1Keys[keyId].label,
                value: defaultLayer1Keys[keyId].value,
                type: "KEY"
            };
        }

        SidebarHandler.render();
        if (state.activeLayerIndex !== -1) {
            KeyHandler.updateFromData(state.activeLayerIndex);
        }
    }
};
