#include "SerialManager.h"
#include <LittleFS.h>
#include <cstdarg>
#include "LayoutLoader.h"
#include "OledHandler.h"

char SerialManager::serialBuffer[64];
uint8_t SerialManager::bufferIndex = 0;

void SerialManager::begin() {
    Serial.begin(115200);
    // Tell the Native USB CDC stack to instantly drop overflow logs 
    // rather than freezing the entire board waiting for the host to read them.
    Serial.setTxTimeoutMs(0);
    
    bufferIndex = 0;
    memset(serialBuffer, 0, sizeof(serialBuffer));
}

void SerialManager::sendResponse(const char* str) {
    if (!str) return;
    // Native USB CDC is non-blocking. Let the ESP32 core handle the FIFO buffer.
    if (Serial) {
        Serial.print(str);
    }
}

void SerialManager::sendFormat(const char* fmt, ...) {
    char buf[96];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    sendResponse(buf);
}

void SerialManager::check() {
    while (Serial.available() > 0) {
        processByte(static_cast<char>(Serial.read()));
    }
}

void SerialManager::processByte(char c) {
    if (c == '\n' || c == '\r' || c == ']') {
        if (c == ']') {
            if (bufferIndex < sizeof(serialBuffer) - 1) {
                serialBuffer[bufferIndex++] = c;
            }
        }
        
        serialBuffer[bufferIndex] = '\0';
        String cmd(serialBuffer);
        
        if (cmd.indexOf("[PING]") >= 0) {
            sendResponse("[PONG:APEXPAD]\n");
        } else if (cmd.indexOf("[CFG_READ_REQ]") >= 0) {
            handleConfigRead();
        } else if (cmd.indexOf("[CFG_WRITE_REQ]") >= 0) {
            handleConfigWrite();
        }
        
        bufferIndex = 0;
        memset(serialBuffer, 0, sizeof(serialBuffer));
    } else {
        if (bufferIndex < sizeof(serialBuffer) - 1) {
            serialBuffer[bufferIndex++] = c;
        }
    }
}

void SerialManager::handleConfigRead() {
    Serial.print("[CFG_READ_START]\n");
    
    File file = LittleFS.open("/config.json", FILE_READ);
    if (file) {
        char buf[64];
        while (file.available()) {
            size_t len = file.readBytes(buf, sizeof(buf) - 1);
            buf[len] = '\0';
            Serial.print(buf);
        }
        file.close();
    }
    
    Serial.print("\n[CFG_READ_END]\n");
}

void SerialManager::handleConfigWrite() {
    OledHandler::showSystemMessage("SYNCING...");
    
    if (LittleFS.exists("/config.bak")) {
        LittleFS.remove("/config.bak");
    }
    if (LittleFS.exists("/config.json")) {
        LittleFS.rename("/config.json", "/config.bak");
    }
    
    File file = LittleFS.open("/config.json", FILE_WRITE);
    Serial.print("[CFG_WRITE_ACK]\n");
    
    uint32_t lastDataTime = millis();
    String currentLine = "";
    
    while (true) {
        while (Serial.available() > 0) {
            char c = static_cast<char>(Serial.read());
            if (c == '\n' || c == '\r') {
                if (currentLine.indexOf("[CFG_WRITE_EOF]") >= 0) {
                    file.close();
                    if (LayoutLoader::begin()) {
                        LittleFS.remove("/config.bak");
                        Serial.print("[CFG_WRITE_OK]\n");
                        OledHandler::showSystemMessage("SUCCESS");
                        delay(400);
                        OledHandler::update();
                    } else {
                        LittleFS.remove("/config.json");
                        if (LittleFS.exists("/config.bak")) {
                            LittleFS.rename("/config.bak", "/config.json");
                        }
                        LayoutLoader::begin();
                        Serial.print("[CFG_WRITE_ERR]\n");
                        OledHandler::showSystemMessage("ERROR");
                        delay(800);
                        OledHandler::update();
                    }
                    return;
                } else {
                    if (currentLine.length() > 0) {
                        file.print(currentLine);
                        file.print("\n");
                    }
                }
                currentLine = "";
            } else {
                currentLine += c;
            }
            lastDataTime = millis();
        }
        
        if (millis() - lastDataTime > 5000) {
            file.close();
            LittleFS.remove("/config.json");
            
            if (LittleFS.exists("/config.bak")) {
                LittleFS.rename("/config.bak", "/config.json");
            }
            LayoutLoader::begin();
            
            Serial.print("[CFG_WRITE_ERR]\n");
            OledHandler::showSystemMessage("ERROR");
            delay(800);
            OledHandler::update();
            return;
        }
        delay(1);
    }
}
