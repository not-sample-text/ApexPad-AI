#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include <LittleFS.h>

struct KeyAction {
    String label;
    String value;
    String type;
    bool isValid;
};

class LayoutLoader {
public:
    static bool begin();
    static const KeyAction& getKeyAction(uint8_t layer, uint8_t row, uint8_t col);
    static uint8_t getPackedByte(uint8_t layer, uint8_t row, uint8_t col);

private:
    static void rebuildCache();
    static JsonDocument doc;
    static KeyAction cache[4][4][3];
    static KeyAction invalidAction;
};
