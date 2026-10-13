# ApexPad AI

**ApexPad AI** is an adaptive, ergonomic 3x4 mechanical macropad ecosystem powered by a **100% offline-first, ultra-low-memory hybrid Artificial Intelligence engine**. By combining local natural language reasoning (**Ollama LLM**) with stochastic spatial optimization (**Simulated Annealing ML**), ApexPad AI reorganizes your macro layouts based on real-world usage telemetry and conversational feedback—while keeping final approval strictly in your hands through a human-in-the-loop web application.

---

## Overview & Ultra-Light Architecture

Traditional macro pads suffer from static layout fatigue: users map keys arbitrarily, leading to awkward finger travel, accidental actuations of destructive scripts, and high cognitive load when switching layers.

ApexPad AI solves this without cloud APIs, heavy web frameworks, or background memory bloat (~20 MB RAM footprint):

1. **Single-Executable Tray Application:** Bundled via **PyInstaller** (`ApexPad.exe`), the Python `host-listener` runs silently in the system tray using Python's native `http.server` and `pyserial`. Double-clicking the tray icon (or using its context menu) opens the unified **Web Configurator** in your default browser, which replaces traditional desktop GUI windows for both keymap editing and live debug monitoring.
2. **The Qualitative Brain (Local LLM via Ollama):** Connects locally to Ollama (`http://127.0.0.1:11434`) using standard-library HTTP requests and strict JSON Schema enforcement. It interprets natural language complaints (e.g., _"I keep hitting Task Manager when reaching for Screenshot, and I want Discord in the top-left corner"_) and translates them into geometric constraints (`anchors`, `separations`, and `clusters`).
3. **The Quantitative Solver (Simulated Annealing ML):** Reads local keystroke transition frequencies and EC11 encoder layer-switch telemetry (`telemetry.json`). It evaluates thousands of 3x4 coordinate permutations (`C0R0`–`C2R3`), discarding any layout that violates the LLM's constraints and scoring valid candidates to minimize physical finger travel (X/Y axis) and cross-layer switching overhead (Z-axis).
4. **The Human Gatekeeper (Vanilla Web UI):** Layouts are never overwritten silently. Proposed configurations are rendered in a zero-dependency HTML/CSS/JS visual sandbox. You can inspect the diff, manually drag-and-drop keys to swap positions, toggle script execution flags (`runAsAdmin`, `runHeadless`), and deliberately **Import**, **Export (Download)**, or **Upload** the configuration directly to the macropad.

---

## System Architecture

```text
 ┌──────────────────────────────────────────────────────────────────────┐
 │                           APEXPAD HARDWARE                           │
 │  [ProS3 ESP32-S3]  [3x4 Key Matrix]  [EC11 Encoder]  [SSD1306 OLED]  │
 └───────────────┬──────────────────────────────────────▲───────────────┘
                 │ USB Serial / BLE HID                 │ Serial Payload
                 │ (Keystrokes, Layer Switches)         │ (Approved config.json)
                 ▼                                      │
 ┌──────────────────────────────────────────────────────┴───────────────┐
 │            HOST-LISTENER (PYINSTALLER .EXE / ~20MB RAM)              │
 │      [System Tray Icon: Double-Click / Menu -> Open Web UI | Exit]   │
 │                                                                      │
 │   ┌─────────────────────────┐          ┌─────────────────────────┐   │
 │   │ Serial & Execution      │─────────►│ telemetry.json          │   │
 │   │ Manager (pyserial)      │          │ (Transition Matrices)   │   │
 │   └─────────────────────────┘          └────────────┬────────────┘   │
 │                                                     │                │
 │   ┌─────────────────────────┐                       ▼                │
 │   │ Local Ollama Client     │          ┌─────────────────────────┐   │
 │   │ (urllib + JSON Schema   │─────────►│ Simulated Annealing     │   │
 │   │  Rule Extraction)       │          │ Spatial Optimizer (ML)  │   │
 │   └─────────────────────────┘          └────────────┬────────────┘   │
 └───────────────▲─────────────────────────────────────┼────────────────┘
                 │ Local HTTP API (http.server)        │ Proposed config.json
                 │ Prompts, Upload & Live Debug Logs   │ & Live Serial Status
                 │                                     ▼
 ┌───────────────┴──────────────────────────────────────────────────────┐
 │                 WEB-CONFIGURATOR (VANILLA HTML/CSS/JS)               │
 │                                                                      │
 │   ┌─────────────────────────┐          ┌─────────────────────────┐   │
 │   │ Conversational AI Chat  │          │ Before / After Diff     │   │
 │   │ & Live Debug Console    │          │ & Manual Drag-and-Drop  │   │
 │   └─────────────────────────┘          └────────────┬────────────┘   │
 │                                                     │                │
 │                  [ Import ]  [ Export ]  [ Upload ] ◄                │
 └──────────────────────────────────────────────────────────────────────┘
```

---

## Hardware Specifications

- **Microcontroller:** Unexpected Maker ProS3 (ESP32-S3, dual-core Xtensa LX7 @ 240MHz, 16MB Flash, 8MB PSRAM, native USB CDC/HID, and BLE 5.0).
- **Switch Matrix:** 12 mechanical switches arranged in a 3-column by 4-row (`3x4`) grid, mapped to physical coordinates `C0R0` through `C2R3`.
- **Rotary Encoder:** Alps EC11 incremental encoder with integrated push-button:
- **Push Action:** Toggles between **Volume Mode** and **Layer Switch Mode**.
- **Rotate Action:** Adjusts system audio or cycles through Layers `0`–`3`.

- **Display:** 0.96" SSD1306 I2C OLED (128x64) driven by `OledHandler`, displaying the active layer name, current key labels, encoder mode, and connection status.
- **Connectivity:** Dual-mode USB-C (native USB HID + Serial CDC for real-time telemetry and dynamic JSON injection) and Bluetooth Low Energy (`BleHid`).

---

## Layer Architecture & Configuration Schema

ApexPad operates across 4 functional layers stored in `config.json`. To protect user workflows and prevent AI hallucinations, the optimizer strictly permutes coordinate assignments (`C0R0`–`C2R3`) within individual layers without altering functional values, executable paths, or Layer 0 bindings.

| Layer ID    | Layer Name  | Key Type   | AI Optimization Policy   | Description & Examples                                                                                                                                                                                            |
| ----------- | ----------- | ---------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Layer 0** | `FN Keys`   | `KEY`      | **Locked (Immutable)**   | Hardcoded `F13`–`F24` assignments bound to external app actions (e.g., `Mute`, `Deafen`, `Push To Talk`, `Toggle Game Overlay`). Never modified by AI.                                                            |
| **Layer 1** | `Shortcuts` | `SHORTCUT` | **Intra-Layer + Z-Axis** | OS and software keybinds executed via HID (e.g., `Screenshot` $\rightarrow$ `Meta + Shift + S`, `Photoshop Export` $\rightarrow$ `Ctrl + Shift + Alt + W`, `Task Manager` $\rightarrow$ `Ctrl + Shift + ESCAPE`). |
| **Layer 2** | `Commands`  | `SCRIPT`   | **Intra-Layer + Z-Axis** | Local scripts (`.ps1`, `.bat`, `.py`) with configurable `runAsAdmin` and `runHeadless` toggles (e.g., `Clean-TempFiles.ps1`, `import.py`) and web URLs (`https://gemini.google.com/`).                            |
| **Layer 3** | `Launcher`  | `APP`      | **Intra-Layer + Z-Axis** | Application binaries and launch flags executed by the host listener (e.g., `VS Code`, `Discord`, `Firefox`, `Photoshop`, `RawTherapee`, `OBS Studio`, `Cyberpunk 2077`).                                          |

### Configuration Structure (`config.json`)

```json
{
    "layers": [
        {
            "id": 0,
            "name": "FN Keys",
            "keys": {
                "C0R0": { "label": "Mute", "value": "F13", "type": "KEY" }
            }
        },
        {
            "id": 1,
            "name": "Shortcuts",
            "keys": {
                "C0R0": {
                    "label": "Screenshot",
                    "value": "Meta + Shift + S",
                    "type": "SHORTCUT"
                }
            }
        },
        {
            "id": 2,
            "name": "Commands",
            "keys": {
                "C0R0": {
                    "label": "Clean Temporary Files",
                    "value": "C:\\Users\\User\\Desktop\\utilities\\Clean-TempFiles.ps1",
                    "type": "SCRIPT",
                    "runAsAdmin": true,
                    "runHeadless": false
                }
            }
        },
        {
            "id": 3,
            "name": "Launcher",
            "keys": {
                "C2R0": {
                    "label": "VS Code",
                    "value": "C:\\Program Files\\Microsoft VS Code\\Code.exe",
                    "type": "APP"
                }
            }
        }
    ]
}
```

---

## Repository Structure

```text
ApexPad-AI/
├── docs/
│   └── Documentatie.md              # Project technical documentation
├── firmware/                        # PlatformIO ESP32-S3 C++ Firmware
│   ├── include/
│   │   └── config.h                 # Firmware-level constants and definitions
│   ├── lib/
│   │   ├── BleHid/                  # Bluetooth Low Energy HID implementation
│   │   ├── BoardSupport/            # Hardware pinout and board initialization
│   │   ├── Core/                    # Non-blocking EventQueue and system Events
│   │   ├── EncoderHandler/          # Alps EC11 rotation and mode-switch driver
│   │   ├── Keymap/                  # In-memory keymap state structures
│   │   ├── KeymapTranslator/        # HID keycode and shortcut parser
│   │   ├── LayoutLoader/            # Dynamic JSON deserializer & LittleFS storage
│   │   ├── MacropadApp/             # Top-level application state coordinator
│   │   ├── MatrixScanner/           # 3x4 diode matrix debouncing & scanning
│   │   ├── OledHandler/             # SSD1306 128x64 I2C display renderer
│   │   ├── SerialManager/           # USB CDC serial telemetry & JSON ingestion
│   │   └── UsbHid/                  # Native USB HID keyboard/consumer control
│   ├── src/
│   │   └── main.cpp                 # Firmware entry point
│   └── platformio.ini               # PlatformIO build environment configuration
├── host-listener/                   # Ultra-Light Python Backend & Tray Service
│   ├── ai/                          # Stdlib Ollama LLM + Simulated Annealing ML
│   │   ├── llm_engine.py            # Zero-dependency urllib Ollama client
│   │   ├── ml_optimizer.py          # Simulated Annealing spatial solver
│   │   ├── orchestrator.py          # End-to-end optimization coordinator
│   │   └── schemas.py               # JSON Schema definitions & rule validators
│   ├── core/
│   │   ├── config_manager.py        # Reads, validates, and backs up config.json
│   │   ├── serial_manager.py        # Manages pyserial lock, telemetry & uploads
│   │   ├── telemetry_manager.py     # Logs keystroke & layer transition matrices
│   │   └── web_server.py            # Stdlib ThreadingHTTPServer for UI & REST API
│   ├── handlers/
│   │   └── execution_handler.py     # Launches local APP binaries, SCRIPTs, and URLs
│   ├── ui/
│   │   └── tray_icon.py             # System tray icon (Double-Click / Menu launcher)
│   ├── utils/
│   │   └── logger.py                # Ring-buffer logger streaming to Web UI
│   ├── ApexPad.spec                 # PyInstaller single-executable build spec
│   ├── config.json                  # Active host configuration file
│   └── main.py                      # Host listener entry point
└── web-configurator/                # Dependency-Free Vanilla Web Application
    ├── css/
    │   ├── components/              # Modular styles (key, knob, oled, modal, etc.)
    │   ├── base.css                 # Reset and foundational typography
    │   ├── layout.css               # Grid and split-pane layout definitions
    │   ├── main.css                 # Master stylesheet entry
    │   └── variables.css            # Theme tokens and CSS custom properties
    ├── js/
    │   ├── handlers/                # UI controllers (io, key, knob, oled, sidebar, etc.)
    │   ├── utils/
    │   │   └── storage.js           # LocalStorage & backend state sync
    │   ├── dom.js                   # DOM element references and helpers
    │   ├── main.js                  # Frontend initialization and event binding
    │   └── state.js                 # Active and proposed layout state management
    └── index.html                   # Unified Web UI (Configurator, AI & Debug)

```

---

## How the Hybrid AI Pipeline Works

### 1. Telemetry Collection (`host-listener`)

While `host-listener` runs silently in the system tray (~20 MB RAM), it listens to the macropad over USB Serial and records:

- **Intra-Layer Transitions (X/Y):** Frequency of sequential key presses within the same layer (e.g., pressing `RawTherapee` followed by `Photoshop` on Layer 3).
- **Cross-Layer Transitions (Z-Axis):** Sequences where the user switches layers via the EC11 encoder and immediately actuates a key (e.g., launching `VS Code` on Layer 3, switching to Layer 2, and running a utility script).

### 2. Local Semantic Rule Extraction (Ollama)

When the user submits feedback in the `web-configurator` chat interface, the Python backend strips out file paths and sends only the target layer's `label` list to the local **Ollama** API (`http://127.0.0.1:11434/api/chat`). Using JSON schema enforcement at `temperature: 0`, Ollama returns deterministic spatial rules:

```json
{
    "layer_id": 3,
    "anchors": {
        "Discord": "C0R0"
    },
    "separations": [["Cyberpunk 2077", "VS Code"]],
    "clusters": [
        ["RawTherapee", "Photoshop", "Figma"],
        ["OBS Studio", "EOS Webcam Utility"]
    ]
}
```

### 3. Simulated Annealing Optimization (ML)

The Python optimizer runs a local Simulated Annealing search over the 12 grid coordinates (`C0R0`–`C2R3`):

- **Hard Constraints:** Any candidate permutation that violates an `anchor`, places `separated` keys on adjacent coordinates, or splits a `cluster` receives an infinite cost penalty.
- **Ergonomic Cost Function:** Valid permutations are scored against `telemetry.json` to minimize Euclidean finger travel distance within a layer and align high-frequency cross-layer pairs on identical physical coordinates (`C_x R_y`) across stacked layers.
- **Object Integrity:** Full JSON key objects (`label`, `value`, `type`, `runAsAdmin`, `runHeadless`) are swapped as atomic units.

### 4. Visual Sandbox & Deliberate Hardware Update

- The optimized `config.json` is returned to the `web-configurator` and displayed as a proposed layout diff.
- The user can review the changes, manually drag-and-drop keys on the 3x4 grid to swap placements, and deliberately click **Export** (to download the JSON file) or **Upload** (to push the configuration directly to the macropad over serial).
- On the ESP32-S3, `SerialManager` receives the payload, `LayoutLoader` updates RAM and persistent flash storage, and `OledHandler` refreshes the screen immediately without rebooting.

---

## Getting Started

### 1. Prerequisites

- **Firmware:** [PlatformIO](https://platformio.org/) (VS Code extension or CLI).
- **Local LLM:** [Ollama](https://ollama.com/) installed and running locally (`ollama pull llama3.2`).
- **Host Environment:** Python 3.10+ (for development or building the `.exe` with PyInstaller).

### 2. Build & Flash Firmware

Connect the Unexpected Maker ProS3 via USB-C and upload the firmware:

```bash
cd firmware
pio run --target upload

```

### 3. Run in Development or Build the `.exe`

Run directly with Python:

```bash
cd host-listener
pip install pyserial pystray Pillow pyinstaller
python main.py

```

Or bundle the entire application (backend + web configurator) into a standalone executable:

```bash
cd host-listener
pyinstaller ApexPad.spec

```

Double-click the system tray icon (or right-click $\rightarrow$ **Open Configurator**) to launch the web interface.

```

```
