#include "LayoutLoader.h"

JsonDocument LayoutLoader::doc;
KeyAction LayoutLoader::cache[4][4][3];
KeyAction LayoutLoader::invalidAction = {"UNUSED", "", "NONE", false};

bool LayoutLoader::begin() {
    if (!LittleFS.begin(true)) {
        return false;
    }
    
    File file = LittleFS.open("/config.json", FILE_READ);
    if (!file) {
        return false;
    }
    
    doc.clear();
    DeserializationError error = deserializeJson(doc, file);
    file.close();

    if (error) {
        return false;
    }

    rebuildCache();
    doc.clear();
    return true;
}

void LayoutLoader::rebuildCache() {
    for (uint8_t l = 0; l < 4; ++l) {
        for (uint8_t r = 0; r < 4; ++r) {
            for (uint8_t c = 0; c < 3; ++c) {
                cache[l][r][c] = {"UNUSED", "", "NONE", false};
            }
        }
    }

    JsonArray layers = doc["layers"].as<JsonArray>();
    for (JsonObject layerObj : layers) {
        uint8_t layerId = layerObj["id"] | 255;
        if (layerId >= 4) continue;

        JsonObject keysObj = layerObj["keys"].as<JsonObject>();
        if (keysObj.isNull()) continue;

        for (uint8_t r = 0; r < 4; ++r) {
            for (uint8_t c = 0; c < 3; ++c) {
                char keyId[8];
                snprintf(keyId, sizeof(keyId), "C%uR%u", c, r);
                JsonObject k = keysObj[keyId].as<JsonObject>();
                if (!k.isNull() && k["value"].is<const char*>()) {
                    String val = k["value"].as<String>();
                    if (val.length() > 0) {
                        cache[layerId][r][c] = {
                            k["label"] | val,
                            val,
                            k["type"] | "NONE",
                            true
                        };
                    }
                }
            }
        }
    }
}

const KeyAction& LayoutLoader::getKeyAction(uint8_t layer, uint8_t row, uint8_t col) {
    if (layer >= 4 || row >= 4 || col >= 3) {
        return invalidAction;
    }
    return cache[layer][row][col];
}

uint8_t LayoutLoader::getPackedByte(uint8_t layer, uint8_t row, uint8_t col) {
    // FIX: Clean 0-11 index matching the 3x4 grid shape
    // (row * 3) + col results in 0 through 11
    uint8_t index = (row * 3) + col;
    return (layer << 4) | (index & 0x0F);
}
