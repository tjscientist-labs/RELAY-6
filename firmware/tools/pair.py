#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Make a new pairing for one controller + one RELAY-6 pad box.

    python3 tools/pair.py [bank]

Prints one `pair ...` line. Paste the SAME line into the serial console (115200 baud) of the pad box and of
the controller; each saves it and restarts. A new pairing resets both counters. Keep the line private:
anyone with it can talk to that pad box.
"""
import secrets, sys

bank = int(sys.argv[1]) if len(sys.argv) > 1 else 1
if not 1 <= bank <= 99:
    sys.exit("bank must be 1..99")
key = secrets.token_hex(16)
system = secrets.token_hex(4)
while int(system, 16) == 0:
    system = secrets.token_hex(4)
print(f"pair {key} {system} {bank}")
