import { dom } from "../dom.js";
import { configData } from "../state.js";
import { PersistenceHandler } from "../utils/storage.js";
import { OLEDHandler } from "./oled.js";

export const IOHandler = {
    init: () => {
        // EXPORT JSON (Download file)
        dom.exportBtn.addEventListener("click", () => {
            const cleanPayload = {
                layers: configData.layers
            };
            const dataStr =
                "data:text/json;charset=utf-8," +
                encodeURIComponent(JSON.stringify(cleanPayload, null, 2));
            const downloadAnchor = document.createElement("a");
            downloadAnchor.setAttribute("href", dataStr);
            downloadAnchor.setAttribute("download", "config.json");
            document.body.appendChild(downloadAnchor);
            downloadAnchor.click();
            downloadAnchor.remove();
            OLEDHandler.updateMain("EXPORTED");
        });

        // IMPORT JSON
        dom.importBtn.addEventListener("click", () => dom.importInput.click());

        dom.importInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const parsed = JSON.parse(event.target.result);
                    PersistenceHandler.applyConfig(parsed);
                    PersistenceHandler.saveToLocal();
                    OLEDHandler.updateMain("IMPORTED");
                } catch (err) {
                    alert("Error: Invalid JSON file.");
                }
            };
            reader.readAsText(file);
            dom.importInput.value = "";
        });

        // UPLOAD TO MACROPAD OVER SERIAL
        if (dom.uploadBtn) {
            dom.uploadBtn.addEventListener("click", async () => {
                const originalHTML = dom.uploadBtn.innerHTML;
                dom.uploadBtn.disabled = true;
                dom.uploadBtn.innerHTML = `<i class="ti ti-loader"></i> Uploading...`;
                OLEDHandler.updateMain("SYNCING...");

                try {
                    const res = await fetch("/api/upload", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            config: { layers: configData.layers }
                        })
                    });
                    const data = await res.json();
                    if (!res.ok || !data.ok) {
                        throw new Error(
                            data.error || "Failed to upload to ApexPad."
                        );
                    }
                    OLEDHandler.updateMain("UPLOAD OK");
                } catch (err) {
                    OLEDHandler.updateMain("UPLOAD ERR");
                    alert(`Upload Error: ${err.message}`);
                } finally {
                    dom.uploadBtn.disabled = false;
                    dom.uploadBtn.innerHTML = originalHTML;
                }
            });
        }
    }
};
