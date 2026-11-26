# Connector pinout (measured)

First complete multimeter pass over all 36 contacts (18 per face) of the
Roomba i7+'s internal factory/debug connector. One unit, one session, one
handheld meter. Anything marked **inferred** is a hypothesis drawn from the
readings, not a confirmed function.

## Conditions

- The connector was reached through a PCIe x1 slot connector, with guide
  rails heat-formed into the sides of its plastic housing so the robot's
  edge connector seats reliably. Only the mechanical form factor matches
  PCIe; the signals are not PCIe.
- **Numbering:** face-up 1-18 with the keying notch between 7 and 8;
  face-down 1-18 with the notch between 11 and 12. Face-up pin *n* sits
  back to back with face-down pin *19 - n*. The table below lists each
  back-to-back pair on one row.
- **Robot OFF** = battery out. **Robot ON** = battery in, fully booted,
  sitting still, off the dock.
- Continuity and resistance were measured with the robot OFF. DC voltage
  was measured with the robot ON, referenced to the ground pins.
- "Open" means the meter showed OL to ground.

## Pin map

| Row | Face-up | Face-down |
|---|---|---|
| 1 | 1: **GND** | 18: **GND** |
| 2 | 2: 0 V, 360 kΩ to GND | 17: 0 V, open |
| 3 | 3: 0 V, 381 kΩ to GND | 16: 0 V, open |
| 4 | 4: **GND** | 15: 0 V, open |
| 5 | 5: 0 V, 37 kΩ to GND | 14: 3.13 V steady, open |
| 6 | 6: 1.62 V, open (**console TX**) | 13: 3.27 V **jumpy**, 40 kΩ to GND |
| 7 | 7: 1.62 V, 18 MΩ to GND (probable console RX) | 12: **GND** |
| 8 | 8: 3.14 V, 520 kΩ to GND | 11: **GND** |
| | *keying notch* | *keying notch* |
| 9 | 9: 0 V, open | 10: 0 V, open |
| 10 | 10: 0 V, open | 9: 0 V, open |
| 11 | 11: 0 V, open | 8: 0 V, open |
| 12 | 12: 0 V, 46 kΩ to GND | 7: 0 V, open |
| 13 | 13: **GND** | 6: **GND** |
| 14 | 14: 0 V, open | 5: 0 V, open |
| 15 | 15: 0 V, 137 kΩ to GND | 4: 3.29 V steady, 3 MΩ to GND |
| 16 | 16: 2.94 V **jumpy**, 137 kΩ to GND | 3: 0 V, open |
| 17 | 17: **5.0 V**, 5 kΩ to GND | 2: **5.0 V**, 5 kΩ to GND |
| 18 | 18: **5.0 V**, 5 kΩ to GND | 1: **5.0 V**, 5 kΩ to GND |

Same-wire (continuity) checks between pins that read the same voltage:

| Pair | Result |
|---|---|
| face-down 1 and face-down 2 | same wire |
| face-down 2 and face-up 17 | same wire |
| face-up 17 and face-up 18 | same wire |
| face-up 6 and face-up 7 | not the same wire |
| face-up 8 and face-down 14 | not the same wire |

## What the readings say

- **Ground, 7 pins:** face-up 1, 4, 13 and face-down 6, 11, 12, 18. Both
  faces carry ground at rows 1 and 13, and the notch-adjacent face-down
  pins 11 and 12 are both ground.
- **5 V, 4 pins, one wire:** face-up 17, 18 and face-down 1, 2. This is
  present with the robot on battery and off the dock, so the robot is
  sourcing it. About 5 kΩ to ground with the battery out.
- **Probable USB device port (inferred):** face-down 2 to 6 read in the
  same order as a micro-USB plug.

  | Face-down pin | Reading | USB role |
  |---|---|---|
  | 2 | 5.0 V | VBUS |
  | 3 | 0 V, open | D- |
  | 4 | 3.29 V steady | D+ |
  | 5 | 0 V, open | ID |
  | 6 | GND | GND |

  D+ high with D- low is the idle state of a full-speed USB device whose
  D+ pull-up is enabled. It also fits the USB gadget described in the
  README (VID `05C6`, PID `9091`; RNDIS, DIAG, ACM, ADB) and the OTG
  controller with a software-switched D+ pull-up found in the device tree
  (see [firmware-crosscheck.md](firmware-crosscheck.md)). Face-down 5 reads
  0 V and open, but an ID input handled by the PMIC would normally show a
  pull-up, so it may be unconnected. Not yet confirmed against a host.
- **Serial console on face-up 6 (confirmed):** a logic-analyzer capture of
  face-up 6 during power-on, decoded as async serial at 115200 baud, 8N1,
  produced the robot's own boot log: the bootloader banner and early boot
  messages, then the kernel command line that also appears in the
  firmware. This is the SoC's UART1 transmit line at its 1.8 V logic level;
  the meter reads about 1.6 to 1.8 V on it. An earlier reading of "28.9 kHz
  PWM" was wrong: 28.9 kHz is 115200 / 4, a serial data pattern. Face-up 7
  stayed silent during boot and is the probable receive line. Face-down 11
  and 12, directly behind face-up 7 and 8, are ground.
- **Other live-looking pins:** face-down 13 (3.27 V) and face-up 16
  (2.94 V) fluctuate on the meter, so they are the best candidates for
  another digital line. The SoC side is 1.8 V, so 3.3 V lines are probably
  on the motor-controller side. Face-up 7 reads the same 1.62 V as face-up 6
  but is not wired to it, and face-up 8 and face-down 14 read 3.14 V and
  3.13 V without being wired together. Readings that agree to a few
  millivolts can mean a shared source through resistors, since continuity
  only beeps below roughly 50 Ω. Resistance between each pair has not been
  measured yet.
- **Pulled-low inputs (inferred):** face-up 2, 3, 5, 12 and 15 sit at 0 V
  with 37 kΩ to 381 kΩ to ground, which looks like inputs with pull-down
  resistors.
- **Unconnected (inferred):** 11 pins read 0 V with no path to ground:
  face-up 9, 10, 11, 14 and face-down 7, 8, 9, 10, 15, 16, 17. Face-down 3
  and 5 also read open but are listed above as the probable USB D- and ID
  lines.
- **No battery rail:** no pin read above 5.0 V, so no unregulated battery
  voltage appears on this connector.

## Caveats

- One unit, one session. Not cross-checked on a second robot.
- A handheld meter averages fast signals, so a pin reading a mid-level
  voltage may be a PWM or serial line, not a DC level.
- Resistances are measured in circuit, so they include whatever else
  hangs off the net.
- Some resistance entries were recorded as "0" or "0L" and are read here as
  OL, because those pins did not show continuity to ground.

## Still to do

- Connect face-down 3, 4 and 6 (D-, D+, GND, with VBUS left unconnected) to
  a PC's USB port and check whether it enumerates a device; record the
  VID and PID.
- Logic-analyzer capture during boot of face-down 13, face-down 14 and
  face-up 16, to see what they carry. The console UART is already
  identified on face-up 6.
- Confirm face-up 7 as the console receive line by sending input through a
  1.8 V serial adapter. Never use a 3.3 V adapter on these pins.
- Measure resistance between face-up 6 and 7, and between face-up 8 and
  face-down 14, with the battery out.
- Repeat the readings on a second unit if one becomes available.
