#include "MatrixScanner.h"
#include "EventQueue.h"
#include "SerialManager.h"

// Explicit hardware pin mappings
static constexpr uint8_t ROWS_PINS[4] = {12, 13, 14, 5};
static constexpr uint8_t COLS_PINS[3] = {15, 37, 35};

bool MatrixScanner::stableState[4][3] = {false};
bool MatrixScanner::rawStateTracking[4][3] = {false};
uint32_t MatrixScanner::lastChangeTime[4][3] = {0};

void MatrixScanner::begin() {
    // Keep inactive rows weakly pulled HIGH instead of floating high-impedance
    for (uint8_t r = 0; r < MATRIX_ROWS; r++) {
        pinMode(ROWS_PINS[r], INPUT_PULLUP);
    }

    // Columns are initialized with internal pull-ups
    for (uint8_t c = 0; c < MATRIX_COLS; c++) {
        pinMode(COLS_PINS[c], INPUT_PULLUP);
    }

    delay(5);

    // Emit initial resting column states to help diagnose stuck pins
    SerialManager::sendFormat(
        "[SYSTEM] Matrix Init Cols (1=HIGH/Idle, 0=LOW): C0(15)=%d, C1(37)=%d, C2(35)=%d\n",
        digitalRead(COLS_PINS[0]),
        digitalRead(COLS_PINS[1]),
        digitalRead(COLS_PINS[2])
    );
}

void MatrixScanner::scan() {
    uint32_t now = millis();

    for (uint8_t r = 0; r < MATRIX_ROWS; r++) {
        // Drive target row LOW to act as active ground path
        pinMode(ROWS_PINS[r], OUTPUT);
        digitalWrite(ROWS_PINS[r], LOW);
        
        // Allow column RC capacitance to settle cleanly across all power domains
        delayMicroseconds(30);

        for (uint8_t c = 0; c < MATRIX_COLS; c++) {
            // Read column line (LOW = connection closed / key pressed)
            bool currentRaw = (digitalRead(COLS_PINS[c]) == LOW);

            if (currentRaw != rawStateTracking[r][c]) {
                rawStateTracking[r][c] = currentRaw;
                lastChangeTime[r][c] = now;
            }

            if ((now - lastChangeTime[r][c]) >= DEBOUNCE_DELAY_MS) {
                if (stableState[r][c] != rawStateTracking[r][c]) {
                    stableState[r][c] = rawStateTracking[r][c];

                    EventType type = stableState[r][c] ? EventType::KeyPress : EventType::KeyRelease;
                    EventQueue::enqueue({type, r, c, now});
                }
            }
        }

        // Actively pull row HIGH briefly to discharge capacitance, then return to INPUT_PULLUP
        digitalWrite(ROWS_PINS[r], HIGH);
        pinMode(ROWS_PINS[r], INPUT_PULLUP);
        delayMicroseconds(5);
    }
}
