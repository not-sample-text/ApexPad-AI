import { dom } from "./dom.js";
import { SidebarHandler } from "./handlers/sidebar.js";
import { ModalHandler } from "./handlers/modal.js";
import { WelcomeHandler } from "./handlers/welcome.js";
import { KnobHandler } from "./handlers/knob.js";
import { IOHandler } from "./handlers/io.js";
import { OLEDHandler } from "./handlers/oled.js";
import { KeyHandler } from "./handlers/key.js";
import { AIHandler } from "./handlers/ai.js";
import { PersistenceHandler } from "./utils/storage.js";
import { state } from "./state.js";
import { TourHandler } from "./handlers/tour.js";

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Render Initial Sidebar
    SidebarHandler.render();

    // 2. Bind Layer Headers
    const headers = document.querySelectorAll(
        ".sidebar .category-header[data-layer]"
    );
    headers.forEach((header, index) => {
        header.addEventListener("click", () =>
            SidebarHandler.toggleLayer(index, header)
        );
    });

    // 3. Bind Key Clicks & Drag-and-Drop
    KeyHandler.initDragAndDrop();

    dom.keys.forEach((key) => {
        key.addEventListener("click", () => {
            if (state.justDragged) return;
            const keyId = key.getAttribute("data-id");
            const savedKey =
                state.activeLayerIndex >= 0
                    ? key.querySelector("span")?.innerText || key.innerText
                    : key.innerText;
            OLEDHandler.updateMain(savedKey);

            if (!dom.macropad.classList.contains("hidden")) {
                ModalHandler.open(keyId);
            }
        });
    });

    if (dom.hamburger) {
        dom.hamburger.addEventListener("click", SidebarHandler.toggleSidebar);
    }

    // 4. Initialize Sub-Systems
    ModalHandler.init();
    WelcomeHandler.init();
    KnobHandler.init();
    IOHandler.init();
    TourHandler.init();
    AIHandler.init();

    // 5. Load Configuration from Python Daemon or LocalStorage
    const loaded = await PersistenceHandler.loadFromBackendOrLocal();
    if (!loaded) {
        WelcomeHandler.show();
    }

    // 6. Auto-open first layer
    if (headers.length > 0) headers[0].click();
});
