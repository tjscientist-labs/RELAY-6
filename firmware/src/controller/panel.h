// SPDX-License-Identifier: GPL-2.0-only
// The three panels differ only here: how pad selection, FIRE, the cover and the lights are read and written.
#pragma once
#include <cstdint>

#include "controller.h"

namespace panel {

struct Read {
  bool keyOn = false, fireHeld = false, coverOk = true;
  uint8_t padsLevel = 0;        // FLIGHTDECK toggles / MONOLITH levers: the selection itself
  uint8_t padsPressed = 0;      // HALO keys: new presses this loop (toggle selection)
  bool modePressed = false;     // MODE / encoder push, new press
  int encoderSteps = 0;         // detents since last read (+ clockwise)
};

const char* name();
bool begin();                   // false if a required chip is missing
void read(Read& r);
// Pad lights: per-pad colour from the pad box state, plus the panel's effects (halo ring, bars, columns).
void lights(uint32_t now, uint8_t selected, const relay6::Controller& c);
bool selectionIsLevel();        // true for FLIGHTDECK and MONOLITH (the switches are the selection)

}  // namespace panel
