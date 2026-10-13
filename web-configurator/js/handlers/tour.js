import { ModalHandler } from "./modal.js";

export const TourHandler = {
    currentStep: 0,
    steps: [
        {
            target: "#main-sidebar ul",
            title: "Macro Layers",
            text: "Organize your workflow across 4 distinct layers. Layer 1 is reserved for native F13–F24 keys, while Layers 2–4 handle Shortcuts, Scripts, and Apps."
        },
        {
            target: ".macropad-container",
            title: "Click or Drag & Drop",
            text: "Click any key to edit its macro and execution toggles (Run as Admin / Headless), or drag and drop keys across the grid to swap their positions."
        },
        {
            target: ".rotary-encoder",
            title: "Tactile Control",
            text: "Scroll the knob to adjust system volume. Click the knob to toggle into Layer Navigation mode."
        },
        {
            target: "#ai-chat-widget",
            title: "Floating AI Assistant",
            text: "Click the bottom-right chat bar to open the AI Layout Assistant. Describe misclicks or grouping preferences and preview proposed changes live."
        },
        {
            target: "#btn-upload-pad",
            title: "Direct Hardware Sync",
            text: "Export your config as a JSON file or click Upload to Pad to stream the layout directly to your ApexPad over USB Serial."
        }
    ],

    init: () => {
        document
            .getElementById("btn-tour-next")
            .addEventListener("click", () => {
                TourHandler.currentStep++;
                if (TourHandler.currentStep >= TourHandler.steps.length) {
                    TourHandler.end();
                } else {
                    TourHandler.renderStep();
                }
            });

        document
            .getElementById("btn-tour-close")
            .addEventListener("click", TourHandler.end);
    },

    start: () => {
        TourHandler.currentStep = 0;
        document.getElementById("tour-overlay").classList.remove("hidden");
        TourHandler.renderStep();
    },

    renderStep: () => {
        const step = TourHandler.steps[TourHandler.currentStep];
        const targetEl = document.querySelector(step.target);
        const highlight = document.getElementById("tour-highlight");
        const tooltip = document.getElementById("tour-tooltip");

        if (!targetEl) return;

        const rect = targetEl.getBoundingClientRect();
        const padding = 10;

        highlight.style.top = `${rect.top - padding}px`;
        highlight.style.left = `${rect.left - padding}px`;
        highlight.style.width = `${rect.width + padding * 2}px`;
        highlight.style.height = `${rect.height + padding * 2}px`;

        document.getElementById("tour-title").innerText = step.title;
        document.getElementById("tour-text").innerText = step.text;
        document.getElementById("tour-progress").innerText =
            `${TourHandler.currentStep + 1} / ${TourHandler.steps.length}`;

        document.getElementById("btn-tour-next").innerText =
            TourHandler.currentStep === TourHandler.steps.length - 1
                ? "Finish"
                : "Next";

        let tooltipTop = rect.bottom + 20;
        let tooltipLeft = rect.left;

        if (tooltipTop + 200 > window.innerHeight) {
            tooltipTop = rect.top - 210;
        }
        if (tooltipLeft + 300 > window.innerWidth) {
            tooltipLeft = window.innerWidth - 320;
        }

        tooltip.style.top = `${tooltipTop}px`;
        tooltip.style.left = `${tooltipLeft}px`;
    },

    end: () => {
        document.getElementById("tour-overlay").classList.add("hidden");
        setTimeout(() => ModalHandler.showSamplePrompt(), 300);
    }
};
