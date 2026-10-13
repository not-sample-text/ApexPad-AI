import { dom } from "../dom.js";
import { configData, state } from "../state.js";
import { SidebarHandler } from "./sidebar.js";
import { KeyHandler } from "./key.js";
import { PersistenceHandler } from "../utils/storage.js";
import { OLEDHandler } from "./oled.js";

let lastLogId = 0;

export const AIHandler = {
    toggleWidget: (forceExpand = null) => {
        if (!dom.ai.widget) return;
        const isCollapsed = dom.ai.widget.classList.contains("collapsed");
        const shouldExpand = forceExpand !== null ? forceExpand : isCollapsed;

        if (shouldExpand) {
            dom.ai.widget.classList.remove("collapsed");
            if (dom.ai.toggleIcon) {
                dom.ai.toggleIcon.className = "ti ti-minus";
            }
            setTimeout(() => dom.ai.promptInput?.focus(), 150);
        } else {
            dom.ai.widget.classList.add("collapsed");
            if (dom.ai.toggleIcon) {
                dom.ai.toggleIcon.className = "ti ti-chevron-up";
            }
        }
    },

    appendMessage: (role, text) => {
        if (!dom.ai.chatLog) return;
        const msg = document.createElement("div");
        msg.className = `ai-msg ${role}`;
        msg.innerText = text;
        dom.ai.chatLog.appendChild(msg);
        dom.ai.chatLog.scrollTop = dom.ai.chatLog.scrollHeight;
    },

    computeMovedMap: (oldLayers, newLayers) => {
        const movedMap = {};
        for (let i = 1; i < 4; i++) {
            const oldKeys = oldLayers[i]?.keys || {};
            const newKeys = newLayers[i]?.keys || {};
            movedMap[i] = {};

            for (const [newCoord, newObj] of Object.entries(newKeys)) {
                if (!newObj || !newObj.label) continue;
                for (const [oldCoord, oldObj] of Object.entries(oldKeys)) {
                    if (
                        oldObj &&
                        oldObj.label === newObj.label &&
                        oldObj.value === newObj.value
                    ) {
                        if (oldCoord !== newCoord) {
                            movedMap[i][newCoord] = oldCoord;
                        }
                        break;
                    }
                }
            }
        }
        return movedMap;
    },

    runOptimization: async () => {
        const prompt = dom.ai.promptInput.value.trim();
        if (!prompt) return;

        const targetScope = dom.ai.targetLayer.value;
        let targetLayerId = null;
        if (targetScope === "active") {
            targetLayerId =
                state.activeLayerIndex > 0 ? state.activeLayerIndex : 1;
        } else if (targetScope !== "all") {
            targetLayerId = parseInt(targetScope, 10);
        }

        const modelName = dom.ai.modelInput.value.trim() || "llama3.2";

        AIHandler.appendMessage("user", prompt);
        dom.ai.promptInput.value = "";
        dom.ai.optimizeBtn.disabled = true;
        dom.ai.optimizeBtn.innerHTML = `<i class="ti ti-loader"></i>`;

        try {
            const baselineConfig = state.aiPreview.active
                ? state.aiPreview.backupConfig
                : JSON.parse(JSON.stringify(configData));

            const res = await fetch("/api/optimize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt,
                    layer_id: targetLayerId,
                    model: modelName,
                    config: baselineConfig
                })
            });

            const data = await res.json();
            if (!res.ok || !data.ok) {
                throw new Error(data.error || "Optimization failed.");
            }

            if (!state.aiPreview.active) {
                state.aiPreview.backupConfig = baselineConfig;
                state.aiPreview.active = true;
            }

            state.aiPreview.movedMap = AIHandler.computeMovedMap(
                state.aiPreview.backupConfig.layers,
                data.proposed_config.layers
            );

            PersistenceHandler.applyConfig(data.proposed_config);

            if (targetLayerId && state.activeLayerIndex !== targetLayerId) {
                const headers = document.querySelectorAll(
                    ".sidebar .category-header[data-layer]"
                );
                if (headers[targetLayerId]) {
                    SidebarHandler.toggleLayer(
                        targetLayerId,
                        headers[targetLayerId]
                    );
                }
            } else {
                KeyHandler.updateFromData(state.activeLayerIndex);
            }

            dom.ai.banner.classList.remove("hidden");
            dom.ai.bannerSummary.innerText =
                data.summary ||
                "Review highlighted key moves below. Drag and drop keys to tweak before accepting.";
            AIHandler.appendMessage(
                "assistant",
                data.explanation ||
                    "Proposed layout loaded into the visual sandbox."
            );
            OLEDHandler.updateMain("AI PREVIEW");
        } catch (err) {
            AIHandler.appendMessage("assistant", `Error: ${err.message}`);
        } finally {
            dom.ai.optimizeBtn.disabled = false;
            dom.ai.optimizeBtn.innerHTML = `<i class="ti ti-send"></i>`;
        }
    },

    acceptSuggestion: () => {
        if (!state.aiPreview.active) return;
        state.aiPreview.active = false;
        state.aiPreview.backupConfig = null;
        state.aiPreview.movedMap = {};
        dom.ai.banner.classList.add("hidden");

        PersistenceHandler.saveToLocal();
        KeyHandler.updateFromData(state.activeLayerIndex);
        SidebarHandler.render();
        OLEDHandler.updateMain("AI ACCEPTED");
        AIHandler.appendMessage(
            "assistant",
            "Changes accepted! Click 'Upload to Pad' or 'Export' in the top bar when you're ready."
        );
    },

    discardSuggestion: () => {
        if (!state.aiPreview.active || !state.aiPreview.backupConfig) return;
        const restored = state.aiPreview.backupConfig;
        state.aiPreview.active = false;
        state.aiPreview.backupConfig = null;
        state.aiPreview.movedMap = {};
        dom.ai.banner.classList.add("hidden");

        PersistenceHandler.applyConfig(restored);
        KeyHandler.updateFromData(state.activeLayerIndex);
        OLEDHandler.updateMain("REVERTED");
        AIHandler.appendMessage(
            "assistant",
            "Reverted to your previous layout."
        );
    },

    pollDaemonStatus: async () => {
        try {
            const res = await fetch("/api/status", { cache: "no-store" });
            if (!res.ok) throw new Error("Daemon offline");
            const status = await res.json();

            if (status.connected) {
                dom.debug.statusPill.classList.remove("disconnected");
                dom.debug.statusPill.classList.add("connected");
                dom.debug.statusText.innerText = `ApexPad (${status.port})`;
            } else {
                dom.debug.statusPill.classList.remove("connected");
                dom.debug.statusPill.classList.add("disconnected");
                dom.debug.statusText.innerText = "Pad Disconnected";
            }

            dom.debug.portVal.innerText = status.port || "Searching...";
            dom.debug.syncVal.innerText = status.sync_status || "IDLE";
            dom.debug.keysVal.innerText = status.total_keypresses ?? 0;
            dom.debug.layersVal.innerText = status.layer_switches ?? 0;

            if (status.sync_status === "RECOVER_SUCCESS") {
                await PersistenceHandler.loadFromBackendOrLocal();
            }

            if (!dom.debug.modal.classList.contains("hidden")) {
                const logRes = await fetch(`/api/logs?since=${lastLogId}`, {
                    cache: "no-store"
                });
                if (logRes.ok) {
                    const logData = await logRes.json();
                    if (
                        Array.isArray(logData.logs) &&
                        logData.logs.length > 0
                    ) {
                        if (lastLogId === 0)
                            dom.debug.logOutput.textContent = "";
                        for (const entry of logData.logs) {
                            dom.debug.logOutput.textContent += `[${entry.timestamp}] ${entry.message}\n`;
                            lastLogId = Math.max(lastLogId, entry.id);
                        }
                        dom.debug.logOutput.scrollTop =
                            dom.debug.logOutput.scrollHeight;
                    }
                }
            }
        } catch (_) {
            dom.debug.statusPill.classList.remove("connected");
            dom.debug.statusPill.classList.add("disconnected");
            dom.debug.statusText.innerText = "Daemon Offline";
        }
    },

    init: () => {
        // Messenger header click to expand/collapse
        if (dom.ai.header) {
            dom.ai.header.addEventListener("click", (e) => {
                if (e.target.closest("#btn-ai-settings")) return;
                AIHandler.toggleWidget();
            });
        }

        // Settings gear drawer toggle
        if (dom.ai.settingsBtn) {
            dom.ai.settingsBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                AIHandler.toggleWidget(true);
                dom.ai.settingsDrawer.classList.toggle("hidden");
            });
        }

        if (dom.ai.optimizeBtn) {
            dom.ai.optimizeBtn.addEventListener(
                "click",
                AIHandler.runOptimization
            );
        }

        // Enter to send, Shift+Enter for newline
        if (dom.ai.promptInput) {
            dom.ai.promptInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    AIHandler.runOptimization();
                }
            });
        }

        if (dom.ai.acceptBtn) {
            dom.ai.acceptBtn.addEventListener(
                "click",
                AIHandler.acceptSuggestion
            );
        }
        if (dom.ai.discardBtn) {
            dom.ai.discardBtn.addEventListener(
                "click",
                AIHandler.discardSuggestion
            );
        }

        // Debug & Hardware Console Modal Listeners
        const openDebug = () => {
            dom.debug.modal.classList.remove("hidden");
            AIHandler.pollDaemonStatus();
        };
        if (dom.debug.openBtn)
            dom.debug.openBtn.addEventListener("click", openDebug);
        if (dom.debug.statusPill)
            dom.debug.statusPill.addEventListener("click", openDebug);
        if (dom.debug.closeBtn) {
            dom.debug.closeBtn.addEventListener("click", () =>
                dom.debug.modal.classList.add("hidden")
            );
        }
        if (dom.debug.modal) {
            dom.debug.modal.addEventListener("click", (e) => {
                if (e.target === dom.debug.modal)
                    dom.debug.modal.classList.add("hidden");
            });
        }

        if (dom.debug.recoverBtn) {
            dom.debug.recoverBtn.addEventListener("click", async () => {
                const res = await fetch("/api/recover", { method: "POST" });
                const data = await res.json();
                alert(data.message || data.error);
            });
        }
        if (dom.debug.forceDumpBtn) {
            dom.debug.forceDumpBtn.addEventListener("click", async () => {
                const res = await fetch("/api/force-dump", { method: "POST" });
                const data = await res.json();
                alert(data.message || data.error);
            });
        }
        if (dom.debug.resetTelemetryBtn) {
            dom.debug.resetTelemetryBtn.addEventListener("click", async () => {
                await fetch("/api/telemetry/reset", { method: "POST" });
                AIHandler.pollDaemonStatus();
            });
        }
        if (dom.debug.clearLogsBtn) {
            dom.debug.clearLogsBtn.addEventListener("click", async () => {
                await fetch("/api/logs/clear", { method: "POST" });
                lastLogId = 0;
                dom.debug.logOutput.textContent = "";
            });
        }

        AIHandler.pollDaemonStatus();
        setInterval(AIHandler.pollDaemonStatus, 300);
    }
};
