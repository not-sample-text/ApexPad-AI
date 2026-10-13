# ApexPad AI

ApexPad AI is an adaptive, ergonomic 3x4 macro controller driven by a hybrid Artificial Intelligence engine. By combining natural language semantic reasoning (LLMs) with physical travel optimization (Stochastic Machine Learning), ApexPad AI dynamically reorganizes your macro key layouts based on real-world usage telemetry and conversational feedback—while keeping full control in your hands through a human-in-the-loop web sandbox.

---

## What It Is

Traditional macro keypads require tedious manual mapping, often resulting in awkward finger travel, accidental key actuations, or cognitive friction when switching between functions.

**ApexPad AI solves layout fatigue using a dual-engine architecture:**

1. **The Qualitative Brain (LLM):** Interprets your natural language feedback (e.g., _"I keep misclicking Task Manager when hitting Screenshot"_) and extracts rigid geometric rules (clustering, separation, corner anchoring).
2. **The Quantitative Solver (ML):** Takes telemetry logs (transition frequencies, keystroke sequences, and layer-switch costs) and runs a Simulated Annealing algorithm to find the mathematically optimal grid permutation that satisfies the LLM's rules.
3. **The Human Gatekeeper (Vanilla Web UI):** Renders the proposed layout side-by-side with your active layout in an interactive visual sandbox. You inspect the layout, manually adjust any switch assignments if desired, and deliberately push the configuration to the hardware.

---

## System Architecture

```text
 ┌───────────────────────────────────────────────────────────────┐
 │                      APEXPAD HARDWARE                         │
 │  [3x4 Key Matrix]  [EC11 Rotary Encoder]  [SSD1306 OLED]      │
 └──────────────┬───────────────────────────────▲────────────────┘
                │ Raw Keystroke                 │ Serial Payload
                │ & Layer Telemetry             │ (Updated config.json)
                ▼                               │
 ┌──────────────────────────────────────────────┴────────────────┐
 │                   PYTHON BACKEND (LOCAL)                      │
 │                                                               │
 │   ┌──────────────────────┐        ┌───────────────────────┐   │
 │   │ Serial Host Listener │───────►│  telemetry.json       │   │
 │   │ (pyserial broker)    │        │  (Transition Matrix)  │   │
 │   └──────────────────────┘        └──────────┬────────────┘   │
 │                                              │                │
 │   ┌──────────────────────┐                   ▼                │
 │   │ LLM Rule Generator   │        ┌───────────────────────┐   │
 │   │ (Natural Language    │───────►│  Simulated Annealing  │   │
 │   │  to Spatial Rules)   │        │  Spatial Solver (ML)  │   │
 │   └──────────────────────┘        └──────────┬────────────┘   │
 └──────────────▲───────────────────────────────┼────────────────┘
                │ Natural Language              │ Proposed
                │ Layout Feedback               │ config.json
                │                               ▼
 ┌──────────────┴────────────────────────────────────────────────┐
 │             LOCAL WEB CONFIGURATOR (VANILLA JS)               │
 │                                                               │
 │   ┌──────────────────────┐        ┌───────────────────────┐   │
 │   │ Conversational Chat  │        │ Visual Sandbox Diff   │   │
 │   │ Layout Assistant     │        │ & Manual Drag-and-Drop│   │
 │   └──────────────────────┘        └──────────┬────────────┘   │
 │                                              │                │
 │                       [ Upload to Macropad ] ◄               │
 └───────────────────────────────────────────────────────────────┘

```

---

## Core Principles

- **Human-in-the-Loop Control:** Layouts are never flashed silently in the background. The AI functions as an ergonomic consultant, presenting proposed layout diffs in a visual sandbox for manual verification and approval.
- **Zero Dependency Rot (Local-First):** The frontend is written in pure vanilla HTML5, CSS3, and modern JavaScript—no build tools, bundlers, or framework dependencies. The Python backend serves the static files locally and operates completely offline, connecting to the network only to execute API requests to the LLM.
- **Firmware Decoupling:** The ESP32 firmware remains purely execution-focused. It parses standard JSON over USB Serial, updates active keymap arrays in RAM, and refreshes the display immediately without requiring recompilation or flashing.
- **Strict Layer Safety:** Functional domains remain isolated. The AI can rearrange keys _within_ a layer or align complementary keys across layers on the vertical Z-axis, but it cannot alter functional definitions or modify protected hardware baselines.

---

## Layer Organization

ApexPad operates across four dedicated functional layers navigated via the Alps EC11 rotary encoder:

| Layer       | Type          | Optimization Behavior       | Description                                                                        |
| ----------- | ------------- | --------------------------- | ---------------------------------------------------------------------------------- |
| **Layer 0** | **FN Keys**   | **Immutable (Locked)**      | Hardcoded `F13`–`F24` keys for custom app assignments. Excluded from AI shuffling. |
| **Layer 1** | **Shortcuts** | **Intra-Layer Permutation** | Complex key combinations (e.g., `Ctrl+Shift+Esc`, `Meta+Shift+S`).                 |
| **Layer 2** | **Commands**  | **Intra-Layer Permutation** | Shell scripts (`.ps1`, `.bat`, `.py`), utilities, and browser URLs.                |
| **Layer 3** | **Launcher**  | **Intra-Layer Permutation** | Executables, game binaries, and daily productivity software.                       |

---

## Hardware Specifications

- **Microcontroller:** ESP32-S3 architecture (USB native CDC/HID support).
- **Matrix:** 12-key Cherry MX-compatible mechanical switches arranged in a 3x4 grid.
- **Rotary Control:** Alps EC11 incremental encoder with integrated push-switch (dual-action: push to toggle mode, rotate to adjust system volume or cycle layers).
- **Display:** 0.96" SSD1306 I2C OLED (128x64) providing dynamic key labeling, active layer visualization, and battery/connection telemetry.
- **Enclosure:** Modular layered structure (base plate, switch plate, hardware housing).

---

## Repository Structure

```text
ApexPad-AI/
├── firmware/                 # PlatformIO ESP32-S3 C++ firmware
│   ├── include/              # Pin configurations and protocol headers
│   ├── lib/                  # Modular drivers (MatrixScanner, OledHandler, etc.)
│   └── src/main.cpp          # Non-blocking event loop execution
├── backend/                  # Local Python engine & hardware bridge
│   ├── host_listener.py      # Serial telemetry monitor & transition logger
│   ├── optimizer/            # LLM rule parser & Simulated Annealing solver
│   ├── server.py             # Local FastAPI/Flask static server & REST API
│   └── telemetry.json        # Keystroke frequency & transition matrices
├── frontend/                 # Zero-dependency local web configurator
│   ├── index.html            # Split-view chat interface and 3x4 layout grids
│   ├── style.css             # Lightweight theme & grid styles
│   └── app.js                # State management, diff viewer, and serial dispatch
└── config/
    └── config.json           # Active device configuration and layer bindings

```

---

## How It Works: Step by Step

### 1. Telemetry Capture

The local Python background process maintains an exclusive serial lock with the macropad. Every physical actuation logs:

- The active physical coordinate (`C0R0` through `C2R3`).
- The active Layer ID.
- Time elapsed between sequential actuations (inter-key latency).
- Layer-switch frequency via the EC11 encoder.

### 2. Conversational Intent Parsing

In the web configurator's chat panel, the user enters natural language feedback:

> _"I keep opening Cyberpunk when I mean to launch VS Code on Layer 3, and I want Discord anchored in the top corner."_

The backend extracts only the relevant layer's key labels and sends them with the prompt to the LLM. The LLM returns a structured spatial schema:

```json
{
    "layer_id": 3,
    "anchors": { "Discord": "C0R0" },
    "separations": [["Cyberpunk 2077", "VS Code"]],
    "clusters": []
}
```

### 3. Spatial Math Optimization (ML)

The Simulated Annealing engine takes over locally:

- It generates candidate permutations of the 12 key coordinate bindings for Layer 3.
- Layouts violating the LLM constraints receive an infinite cost penalty and are discarded.
- Valid permutations are scored against the `telemetry.json` transition matrix to minimize physical hand strain and finger travel distance.
- Key object metadata (`type`, `value`, `runAsAdmin`, `runHeadless`) remains untouched; only the coordinate keys (`C0R0`–`C2R3`) are permuted.

### 4. Interactive Review & Device Flash

The optimized configuration is pushed back to the browser:

- The web UI highlights proposed relocations using an interactive Before/After diff.
- The user can manually drag and swap keys to fine-tune the result.
- Clicking **Apply to Device** posts the JSON to the local backend, which writes the configuration down the serial stream.
- The macropad's `LayoutLoader` updates RAM immediately, and the OLED redraws the active layer labels with zero downtime.

---

## Getting Started

### Prerequisites

- **Firmware:** [PlatformIO Core](https://platformio.org/) or PlatformIO IDE for VS Code.
- **Backend:** Python 3.10+ with `pyserial` and your preferred local web framework (`fastapi` + `uvicorn` or `flask`).
- **Hardware:** Assembled ApexPad hardware connected via USB-C.

### Running Locally

1. **Flash the Controller:**

```bash
cd firmware
pio run --target upload

```

2. **Start the Local Engine:**

```bash
cd backend
pip install -r requirements.txt
python server.py

```

3. **Open the Configurator:**
   Navigate to `http://localhost:8000` in any modern web browser. The app will automatically connect to the active serial session and load your current layout.
