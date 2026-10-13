import { dom } from "../dom.js";
import { configData, state } from "../state.js";
import { PersistenceHandler } from "../utils/storage.js";
import { SidebarHandler } from "./sidebar.js";
import { OLEDHandler } from "./oled.js";

let draggedKeyId = null;

export const KeyHandler = {
    updateFromData: (layerIndex) => {
        const layer = configData.layers[layerIndex];
        if (!layer) return;

        const layerKeys = layer.keys || {};
        const isEditableLayer = layerIndex > 0;
        const movedForLayer = state.aiPreview.active
            ? state.aiPreview.movedMap[layerIndex] || {}
            : {};

        if (dom.dragHint) {
            dom.dragHint.innerText = isEditableLayer
                ? "Tip: Click a key to edit, or drag & drop keys to swap positions."
                : "Layer 1 (F13–F24): Click a key to rename its label. Positions are hardware-locked.";
        }

        dom.keys.forEach((key) => {
            const id = key.getAttribute("data-id");
            key.classList.remove(
                "unassigned-key",
                "ai-moved",
                "dragging",
                "drag-over"
            );
            key.setAttribute("draggable", isEditableLayer ? "true" : "false");

            if (layerKeys[id] && layerKeys[id].value) {
                key.innerHTML = "";
                const labelSpan = document.createElement("span");
                labelSpan.innerText = layerKeys[id].label;
                key.appendChild(labelSpan);

                if (movedForLayer[id] && movedForLayer[id] !== id) {
                    key.classList.add("ai-moved");
                    const badge = document.createElement("span");
                    badge.className = "key-diff-badge";
                    badge.innerText = `from ${movedForLayer[id]}`;
                    key.appendChild(badge);
                }
            } else {
                key.innerText = "Unassigned";
                key.classList.add("unassigned-key");
            }
        });
    },

    swapKeys: (layerIndex, sourceId, targetId) => {
        if (layerIndex <= 0 || sourceId === targetId) return;

        const layerKeys = configData.layers[layerIndex].keys;
        const sourceObj = layerKeys[sourceId]
            ? JSON.parse(JSON.stringify(layerKeys[sourceId]))
            : undefined;
        const targetObj = layerKeys[targetId]
            ? JSON.parse(JSON.stringify(layerKeys[targetId]))
            : undefined;

        if (sourceObj) {
            layerKeys[targetId] = sourceObj;
        } else {
            delete layerKeys[targetId];
        }

        if (targetObj) {
            layerKeys[sourceId] = targetObj;
        } else {
            delete layerKeys[sourceId];
        }

        // Update diff badge tracking if in AI preview sandbox
        if (state.aiPreview.active && state.aiPreview.movedMap[layerIndex]) {
            const map = state.aiPreview.movedMap[layerIndex];
            const prevSourceOrigin = map[sourceId] || sourceId;
            const prevTargetOrigin = map[targetId] || targetId;
            map[sourceId] = prevTargetOrigin;
            map[targetId] = prevSourceOrigin;
        } else {
            PersistenceHandler.saveToLocal();
        }

        KeyHandler.updateFromData(layerIndex);
        SidebarHandler.render();
        OLEDHandler.updateMain(`SWAPPED`);
    },

    initDragAndDrop: () => {
        dom.keys.forEach((key) => {
            key.addEventListener("dragstart", (e) => {
                if (state.activeLayerIndex <= 0) {
                    e.preventDefault();
                    return;
                }
                draggedKeyId = key.getAttribute("data-id");
                key.classList.add("dragging");
                if (e.dataTransfer) {
                    e.dataTransfer.effectAllowed = "move";
                    e.dataTransfer.setData("text/plain", draggedKeyId);
                }
            });

            key.addEventListener("dragover", (e) => {
                if (state.activeLayerIndex <= 0 || !draggedKeyId) return;
                e.preventDefault();
                const targetId = key.getAttribute("data-id");
                if (targetId !== draggedKeyId) {
                    key.classList.add("drag-over");
                }
            });

            key.addEventListener("dragleave", () => {
                key.classList.remove("drag-over");
            });

            key.addEventListener("drop", (e) => {
                e.preventDefault();
                key.classList.remove("drag-over");
                if (state.activeLayerIndex <= 0 || !draggedKeyId) return;

                const targetId = key.getAttribute("data-id");
                if (targetId && targetId !== draggedKeyId) {
                    state.justDragged = true;
                    setTimeout(() => {
                        state.justDragged = false;
                    }, 150);
                    KeyHandler.swapKeys(
                        state.activeLayerIndex,
                        draggedKeyId,
                        targetId
                    );
                }
                draggedKeyId = null;
            });

            key.addEventListener("dragend", () => {
                draggedKeyId = null;
                dom.keys.forEach((k) =>
                    k.classList.remove("dragging", "drag-over")
                );
            });
        });
    },

    simulatePress: (keyId) => {
        const key = document.querySelector(
            `.macropad-container .key[data-id="${keyId}"]`
        );
        if (key) {
            key.classList.add("pressed-simulation");
            setTimeout(() => key.classList.remove("pressed-simulation"), 200);
        }
    }
};
