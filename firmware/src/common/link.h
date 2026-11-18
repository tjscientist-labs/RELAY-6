// SPDX-License-Identifier: GPL-2.0-or-later
// Radio + persistent pairing/counters + the serial console, shared by the pad box and the controllers.
#pragma once
#include <Arduino.h>

#include "protocol.h"

namespace r6link {

struct Rx {
  uint8_t buf[relay6::kMaxPacket];
  size_t len = 0;
  int16_t rssi = 0;
  int8_t snr = 0;
};

bool radioBegin();
bool receive(Rx& rx);                         // true when a packet arrived (radio re-armed for the next)
bool send(const uint8_t* p, size_t n);        // blocking transmit, then back to receive

// Pairing and counters in NVS ("relay6" namespace).
bool loadKeys(relay6::LinkKeys& k);
void saveKeys(const relay6::LinkKeys& k);
uint32_t bootTxCounter();                     // first counter to use this boot (block reserved in NVS)
void afterSend(uint32_t nextCounter);         // advances the reserved block when needed
uint32_t bootRxFloor();                       // last stored floor of the peer's counter
void afterReceive(uint32_t lastAccepted);     // stores a new floor once per block
uint16_t getU16(const char* key, uint16_t def);
void putU16(const char* key, uint16_t v);

// Serial console: "show", "pair <32 hex key> <8 hex system> [bank]", plus role-specific commands.
// Returns true if the line was handled here; role code handles the rest.
bool console(const String& line, const relay6::LinkKeys& k);
String readLine();                            // non-blocking; empty until a full line arrives

}  // namespace r6link
