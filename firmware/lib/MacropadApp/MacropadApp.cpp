#include "MacropadApp.h"
#include "config.h"
#include "BoardSupport.h"
#include "MatrixScanner.h"
#include "EncoderHandler.h"
#include "OledHandler.h"
#include "RgbHandler.h"
#include "EventQueue.h"
#include "LayoutLoader.h"
#include "KeymapTranslator.h"
#include "UsbHid.h"
#include "SerialManager.h"

enum EncoderMode : uint8_t {
    MODE_VOL = 0,
    MODE_LYR = 1
};

uint8_t MacropadApp::currentLayer = 0;
char MacropadApp::currentLabel[32] = "IDLE";
EncoderMode currentEncoderMode = MODE_VOL;

void MacropadApp::begin() {
    delay(500);
    
    BoardSupport::begin();
    KeymapTranslator::init();

    // Initialize USB stack before Serial CDC
    UsbHid::begin();
    SerialManager::begin();

    LayoutLoader::begin();

    MatrixScanner::begin();
    EncoderHandler::begin();
    OledHandler::begin();
    OledHandler::showBootAnimation();
    RgbHandler::begin();

    OledHandler::update();
    SerialManager::sendResponse("[SYSTEM] Application Vector Ready.\n");
}

void MacropadApp::run() {
    SerialManager::check();
    MatrixScanner::scan();
    EncoderHandler::run();
    processEvents();
    delay(1);
}

void MacropadApp::processEvents() {
    InputEvent event;
    
    while (EventQueue::dequeue(event)) {
        switch (event.type) {
            case EventType::KeyPress: {
                SerialManager::sendFormat(
                    "[EVENT] Key Pressed - Layer: %d, Row: %d, Col: %d\n",
                    currentLayer, event.row, event.col
                );
                
                const KeyAction& action = LayoutLoader::getKeyAction(currentLayer, event.row, event.col);
                
                if (!action.isValid) {
                    strncpy(currentLabel, "UNUSED", sizeof(currentLabel) - 1);
                    currentLabel[sizeof(currentLabel) - 1] = '\0';
                    OledHandler::update();
                    break;
                }

                strncpy(currentLabel, action.label.c_str(), sizeof(currentLabel) - 1);
                currentLabel[sizeof(currentLabel) - 1] = '\0';

                if (action.type == "KEY" || action.type == "SHORTCUT") {
                    HidCode code;
                    if (currentLayer == 0) {
                        uint8_t linearKeyIndex = (event.row * kMatrixColumnCount) + event.col;
                        code.keycode = 104 + linearKeyIndex; 
                        code.modifiers = 0;
                    } else {
                        code = KeymapTranslator::translate(action.value);
                    }
                    UsbHid::sendKey(code.keycode, code.modifiers, true);
                }
                
                if (action.type == "APP" || action.type == "SCRIPT") {
                    uint8_t packed = LayoutLoader::getPackedByte(currentLayer, event.row, event.col);
                    SerialManager::sendFormat("[CMD:%02X]\n", packed);
                }
                
                OledHandler::update();
                break;
            }

            case EventType::KeyRelease: {
                const KeyAction& action = LayoutLoader::getKeyAction(currentLayer, event.row, event.col);
                
                if (action.isValid && (action.type == "KEY" || action.type == "SHORTCUT")) {
                    HidCode code;
                    if (currentLayer == 0) {
                        uint8_t linearKeyIndex = (event.row * kMatrixColumnCount) + event.col;
                        code.keycode = 104 + linearKeyIndex;
                        code.modifiers = 0;
                    } else {
                        code = KeymapTranslator::translate(action.value);
                    }
                    UsbHid::sendKey(code.keycode, code.modifiers, false);
                }
                break;
            }

            case EventType::EncoderCW:
                if (currentEncoderMode == MODE_VOL) {
                    strncpy(currentLabel, "Volume Up", sizeof(currentLabel) - 1);
                    UsbHid::sendConsumerKey(0x00E9, true);
                    delay(2);
                    UsbHid::sendConsumerKey(0x00E9, false);
                } else if (currentEncoderMode == MODE_LYR) {
                    currentLayer = (currentLayer + 1) % 4;
                    strncpy(currentLabel, "Next Layer", sizeof(currentLabel) - 1);
                    SerialManager::sendFormat("[LOG] Switched to Layer %d\n", currentLayer);
                }
                currentLabel[sizeof(currentLabel) - 1] = '\0';
                OledHandler::update();
                break;
                
            case EventType::EncoderCCW:
                if (currentEncoderMode == MODE_VOL) {
                    strncpy(currentLabel, "Volume Down", sizeof(currentLabel) - 1);
                    UsbHid::sendConsumerKey(0x00EA, true);
                    delay(2);
                    UsbHid::sendConsumerKey(0x00EA, false);
                } else if (currentEncoderMode == MODE_LYR) {
                    currentLayer = (currentLayer == 0) ? 3 : currentLayer - 1;
                    strncpy(currentLabel, "Previous Layer", sizeof(currentLabel) - 1);
                    SerialManager::sendFormat("[LOG] Switched to Layer %d\n", currentLayer);
                }
                currentLabel[sizeof(currentLabel) - 1] = '\0';
                OledHandler::update();
                break;
                
            case EventType::EncoderButton:
                currentEncoderMode = (EncoderMode)((currentEncoderMode + 1) % 2);
                if (currentEncoderMode == MODE_VOL) {
                    strncpy(currentLabel, "Mode: Volume", sizeof(currentLabel) - 1);
                } else {
                    strncpy(currentLabel, "Mode: Layer", sizeof(currentLabel) - 1);
                }
                currentLabel[sizeof(currentLabel) - 1] = '\0';
                OledHandler::update();
                break;
        }
    }
}
