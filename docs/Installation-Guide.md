# ApexPad AI — First-Time User & Installation Guide

Welcome to **ApexPad AI**. This guide walks you through connecting your macropad, setting up the background companion software, enabling the offline AI layout assistant, and customizing your first macros.

---

## 1. What You Need

1. **ApexPad Hardware Unit** (pre-flashed with ApexPad firmware)
2. **USB-C Data Cable** (ensure it is a data-capable cable, not a charge-only cable)
3. **ApexPad Software Folder** containing:
    - `ApexPad.exe` (Background Service & Web Configurator)
    - `config.json` (Default 4-layer keymap configuration)
4. **Ollama** _(Optional, required only for AI layout generation)_

---

## 2. Step-by-Step Installation

### Step 1: Install the Local AI Engine (Ollama)

ApexPad AI processes your layout feedback 100% offline using a local Large Language Model so your data never leaves your PC.

1. Download and install **Ollama** for your operating system from [https://ollama.com](https://ollama.com).
2. Open a terminal (Command Prompt or PowerShell) and download the lightweight `llama3.2` model (~2 GB):
    ```bash
    ollama pull llama3.2
    ```
3. Leave Ollama running in your system tray. _(Note: All macro execution and manual configuration features work even if Ollama is not installed)._

### Step 2: Connect the ApexPad Hardware

1. Plug the ApexPad into your computer using a USB-C data cable.
2. Wait 2 seconds for the device to initialize:

- The onboard status LED will illuminate in **solid cyan**.
- The OLED screen will play a brief boot animation and display the default header (`FN KEYS`), a **USB lightning bolt icon** in the top-right corner, the current state (`IDLE`), and the encoder mode (`VOLUME`) at the bottom.

### Step 3: Launch the ApexPad Companion App

1. Place the `ApexPad` folder somewhere permanent on your computer (for example, `C:\Program Files\ApexPad\` or `Desktop\ApexPad\`), making sure `ApexPad.exe` and `config.json` are in the same folder.
2. Double-click **`ApexPad.exe`** to start the background service.

- No terminal window will pop up—the app runs silently in the background using ~20 MB of RAM.

3. Look at your Windows **System Tray** (bottom-right corner of your taskbar, near the clock) for the **cyan-and-navy ApexPad square icon**.

- _Tip:_ Drag the icon out of the hidden overflow menu (`^`) onto your main taskbar so it is always visible.

4. _(Optional — Run on Windows Startup)_:

- Right-click `ApexPad.exe` and select **Create shortcut**.
- Press `Win + R`, type `shell:startup`, and press **Enter**.
- Move the shortcut into the Startup folder that opens.

---

## 3. Opening & Using the Web Configurator

To open the configuration interface:

- **Double-click** the ApexPad icon in your system tray, **OR**
- **Right-click** the tray icon and click **Open Configurator**.

Your default web browser will open to `http://127.0.0.1:8765`.

### Checking Your Connection

Look at the status pill in the top-right navigation bar:

- **Green Dot (`ApexPad (COMx)`):** Your macropad is connected and communicating over USB Serial.
- **Red Dot (`Pad Disconnected`):** The daemon is scanning for the hardware. Check your USB-C cable.

### Navigating the 4 Layers

Use the left sidebar (or the virtual rotary knob) to switch between your 4 layers:

| Layer       | Name          | Purpose                                                                                                                                                                         |
| ----------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Layer 1** | **FN Keys**   | Native `F13`–`F24` keys for binding inside apps like Discord, OBS, or games. You can rename the OLED display labels, while the underlying F-keys stay locked for compatibility. |
| **Layer 2** | **Shortcuts** | Keyboard combinations sent directly over USB HID (e.g., `Ctrl + Shift + Esc`, `Win + Shift + S`).                                                                               |
| **Layer 3** | **Commands**  | Scripts (`.ps1`, `.bat`, `.py`, `.sh`, `.ahk`) and web URLs (`https://...`) launched by the companion app.                                                                      |
| **Layer 4** | **Launcher**  | Desktop applications and games launched via their `.exe` path (with optional launch arguments).                                                                                 |

### Editing a Key

1. Click any keycap on the 3x4 visualizer (or in the sidebar list) to open the **Edit Key** modal.
2. Set a **Display Name** (this text is shown centered on your physical OLED screen when pressed).
3. Configure the action based on the active layer:

- **Shortcuts (Layer 2):** Click the **Shortcut Recorder** box and press your desired key combination on your keyboard, or toggle the `Win`/`Cmd`, `Ctrl`, `Shift`, and `Alt` buttons below it.
- **Commands & Apps (Layers 3 & 4):** Paste the full file path (e.g., `C:\Scripts\cleanup.ps1`) or website URL (`https://gemini.google.com/`).
- **Execution Options (Layers 3 & 4):**
- **Run as Administrator:** Launches the script or app with elevated Windows UAC privileges.
- **Run Headless (Hidden):** Runs scripts silently in the background without flashing a terminal window.

4. Click **Save**.

### Rearranging Keys (Drag & Drop)

On **Layers 2, 3, and 4**, you can quickly reorganize your layout without retyping paths:

- Click and hold any keycap on the 3x4 grid, drag it onto another keycap, and release to **swap their positions**.

### Saving & Syncing to Hardware

In the top-right navigation bar, you have three file/hardware actions:

- **Import:** Load a previously saved `.json` configuration file from your computer.
- **Export:** Download a backup copy of your current `config.json` to your computer.
- **Upload to Pad:** Stream your current configuration directly over USB to the ApexPad. The physical OLED screen will briefly display `SYNCING...` followed by `SUCCESS`, applying your new layout immediately without rebooting.

---

## 4. Optimizing Your Layout with AI

As you use your ApexPad, the background daemon passively counts your keypresses, tracks which macros you press one after another, and records how often you switch layers.

To let the AI optimize your layout:

1. Click **AI Layout Assistant** at the bottom of the left sidebar.
2. Choose your **Target Scope** (the active layer, a specific layer, or all editable layers) and verify your local Ollama model name (default: `llama3.2`).
3. Type a natural language request in the chat box. Examples:

- _"I keep accidentally hitting Task Manager when reaching for Screenshot, and I want Copy History in the top-right corner."_
- _"Group my photo editing apps (Photoshop, RawTherapee, Figma) together on the bottom rows and separate Cyberpunk from VS Code."_
- _"Optimize this layer for ergonomics based on my usage telemetry."_

4. Click **Generate Layout Suggestion** (or press `Ctrl + Enter`).
5. **Review in the Visual Sandbox:**

- The AI's suggested layout loads into a temporary preview mode.
- Any key that moved is highlighted in **cyan** with a badge showing its previous coordinate (e.g., `from C0R1`).
- You can still **drag and drop** keys in preview mode to manually tweak the AI's suggestion.

6. Click **Accept Changes** in the top banner to keep the layout (or **Discard** to revert), then click **Upload to Pad** to push the new arrangement to your hardware.

---

## 5. Using the Physical Macropad

### The 3x4 Key Matrix

- Pressing any key executes its assigned action for the active layer and displays the key's custom **Display Name** in the center of the OLED screen.

### The Rotary Encoder Knob (Alps EC11)

The rotary knob supports two modes, displayed on the bottom line of the OLED screen:

1. **VOLUME Mode (Default):**

- **Rotate Clockwise:** Volume Up
- **Rotate Counter-Clockwise:** Volume Down

2. **LAYER SELECT Mode:**

- **Press (Click) the Knob Down:** Toggles between `VOLUME` mode and `LAYER SELECT` mode.
- **Rotate Clockwise / Counter-Clockwise:** Cycles through Layers 1 to 4 (`FN KEYS` $\leftrightarrow$ `SHORTCUTS` $\leftrightarrow$ `COMMANDS` $\leftrightarrow$ `APPS`).
- **Press (Click) the Knob Again:** Locks in your chosen layer and returns to `VOLUME` mode.

---

## 6. Hardware Console & Recovery Tools

Click the **Console** button (or the connection status pill) in the top-right bar of the Web Configurator to open the **ApexPad Daemon & Debug Console**:

- **Live Stats:** View your active COM port, sync state, total logged keypresses, and layer-switch count.
- **Recover Config from Pad:** Reads the `/config.json` file currently stored inside the macropad's onboard flash memory, saves it locally, and places a backup copy in your `Downloads` folder.
- **Force Dump to Desktop:** Performs a raw emergency dump of the macropad's memory to `Desktop/emergency_dump.json` (bypassing JSON validation) for troubleshooting.
- **Reset Telemetry:** Clears your recorded keypress transition history if you want to start training the AI optimizer from scratch.
