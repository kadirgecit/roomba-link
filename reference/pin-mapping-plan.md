# Connector pin-mapping plan

Working notes for mapping the factory/debug connector (18 contacts per
face, 36 total).

**Status:** the first complete multimeter pass is done, and the results are
in [connector-pinout.md](connector-pinout.md). The multimeter procedure
below is kept as the method. The logic-analyzer sections are still the plan
for the remaining unknowns: confirming USB and identifying the remaining
signal pins. The console UART has already been found on face-up 6 by
decoding a boot capture at 115200 8N1 (see the worked example below).

## What we're looking for, in priority order

1. **GND** — multiple pins are almost certainly ground/shield. Find these
   first; everything else is measured relative to them.
2. **VBUS / power rails** — look for a pin sitting at a steady DC voltage
   (5V = USB VBUS, 3.3V = logic rail) with the robot powered on.
3. **USB D+ / D-** — a differential pair, usually with small (~1.5kΩ)
   pull resistors nearby on one side for full-speed detection. This is
   the highest-value find, since USB is what carries ADB/serial/RNDIS
   per the firmware (`rndis,diag,acm,adb` — see README).
4. **UART TX/RX** — console output is a real possibility on a
   factory/debug connector. Idles high at logic level (1.8V/3.3V), toggles
   during boot.
5. **STM32 SWD (SWDIO/SWCLK) or UART** — if any pins go to the
   motor-controller board instead of the Qualcomm side.

## Reference: STM32F030C8T6 (LQFP48) pins that matter here

Confirm against ST's official datasheet (DS9773) before wiring anything
— pin numbers below are from datasheet/community cross-references, not
independently verified by us yet.

| Signal | Pin # | Notes |
|---|---|---|
| PA9 (USART1_TX) | 30 | default USART1 TX |
| PA10 (USART1_RX) | 31 | default USART1 RX |
| PA13 (SWDIO) | 34 | internal pull-up, default function after reset |
| PA14 (SWCLK) | 37 | internal pull-down, default function after reset; also USART2_TX — conflict if USART2 is used |
| BOOT0 | 44 | sampled at reset: low = user flash, high = system bootloader |

If continuity tracing shows a connector pin running straight to one of
these STM32 pins, that tells us which signal it is without needing to
power anything up.

## MSM8909 side: no public pinout, and we don't need one

Qualcomm doesn't publish MSM8909 ball-map datasheets, and it wouldn't
help anyway — the SoC is embedded in a daughtercard module, so the only
pins we can physically reach are the module's own edge pads / the
connector itself, not SoC balls. We identify signals by behavior, not by
a datasheet:

- **USB D+/D-**: differential pair, each line ~0.6-3.3V range depending
  on state, small series/pull resistors nearby on the PCB
  (see `TP3`/`TP1`/`C150`/`C167` etc. visible in the teardown photos in
  the README) — since D-signal routing on the production USB composite
  gadget uses the standard `android_usb` ConfigFS framework (confirmed
  in firmware — see README "Firmware analyzed"), stock USB electrical
  characteristics apply.
- **UART console**: look for a pin that idles at a steady logic-high and
  has burst activity right at power-on (boot log).

## Multimeter procedure (robot powered OFF unless noted)

1. **Continuity mode, connector to connector**: map which of the 18
   pins are shorted together or to the metal shield/chassis — these are
   GND/shield.
2. **Continuity mode, connector to known test points**: probe from each
   connector pin to the STM32's SWDIO/SWCLK/BOOT0/USART1 pins (see table
   above) and to any labeled test points near the connector in the
   teardown photos. A dead short (near-0Ω) means that pin is that net.
3. **Resistance to GND**: pins with a consistent small pull-up/pull-down
   resistor to GND or 3.3V are often control/strap pins (BOOT0-style) or
   part of a USB pull network.
4. **Power ON, DC voltage mode**: measure each pin relative to GND.
   Steady 5V → VBUS. Steady 3.3V/1.8V → logic rail or idle-high
   UART/SWD line. ~0V with noise → likely an active data line (USB,
   switching UART).

**Safety note:** don't apply any external voltage to the connector while
the robot is powered from its own battery — only measure. If back-driving
a rail is a risk, power the robot off entirely while doing continuity
checks (step 1-3), and only reintroduce power for step 4.

## Logic analyzer procedure

1. Clip onto the pins identified as "probably data" from the multimeter
   pass above (keep GND reference attached).
2. Power on the robot and capture the first ~10 seconds of activity ignoring the power pins.
3. Look for:
   - A **UART-shaped signal**: single line, idle high, start bit low,
     8N1-ish framing, common baud rates (115200, 921600) — try standard
     UART decoders at a few baud rates if the framing doesn't lock in
     immediately.
   - A **USB-shaped signal**: two lines, differential, bus resets
     (SE0 state), packet structure — a USB protocol decoder (if your
     analyzer software has one) will confirm this far faster than
     reading raw transitions.
   - An **SWD-shaped signal**: two lines (SWDIO bidirectional, SWCLK
     constant toggling at a fixed rate from the debugger side) — only
     relevant if something external is also driving SWD, which won't be
     the case just from robot power-on; more useful once we're actively
     trying to drive SWD ourselves.

### Worked example: finding the console UART

Capture the suspect pin with a shared ground, start recording before
powering the robot on, and keep the capture running through boot. In Logic 2,
add an Async Serial analyzer on that channel at 115200 baud, 8 bits, 1 stop
bit, no parity, not inverted, and open the terminal view. At power-on the
robot printed its bootloader log, which confirmed face-up 6. Strings from
the firmware, such as the bootloader banner, make a good check. The SoC
side is 1.8 V, so make sure your analyzer reads 1.8 V as high, and never
attach a 3.3 V serial adapter.

## Once we have a confirmed pinout

- The measured table lives in [connector-pinout.md](connector-pinout.md)
  and is summarized in the main [README](../README.md).
- Remaining before the adapter board: connect the probable USB D-/D+ pins
  to a PC to confirm them, and capture the live-looking signal pins with
  the logic analyzer.
- Then start the `adapter-board/` KiCad files referenced in the README's
  Tools section.
