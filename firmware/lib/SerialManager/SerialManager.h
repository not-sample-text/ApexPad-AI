#pragma once
#include <Arduino.h>

class SerialManager {
public:
    static void begin();
    static void check();
    static void sendResponse(const char* str);
    static void sendFormat(const char* fmt, ...);

private:
    static void handleConfigRead();
    static void handleConfigWrite();
    static void processByte(char c);

    static char serialBuffer[64];
    static uint8_t bufferIndex;
};
