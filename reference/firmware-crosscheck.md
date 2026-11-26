# Firmware cross-check

What the firmware says about how the robot talks to the outside world,
compared against what we measured on the connector (see
[connector-pinout.md](connector-pinout.md)). Everything here is original
analysis of an image the author sourced independently; no firmware content
is reproduced, only values and behavior. See [Firmware analyzed](../README.md#firmware-analyzed)
for the exact version.

The firmware can tell us which interfaces the SoC has and how the software
uses them. It cannot tell us which pins of the physical connector they are
wired to. Only measurements can do that.

## What is in the package

Six parts: four signed boot-chain images (TrustZone, RPM, the LK
bootloader and SBL1), a SquashFS root filesystem, and an Android-format
boot image holding the kernel. There is no initramfs; the kernel mounts the
SquashFS from eMMC.

## Boot chain and console

- SBL1 hands off to the LK bootloader, which loads the kernel. Both print
  progress on the SoC's UART1.
- Kernel command line (from the boot image header): `console=ttyHSL0,115200,n8`,
  `androidboot.hardware=qcom`, `ehci-hcd.park=3`, `usbcore.autosuspend=-1`,
  `rootwait`, `androidboot.bootdevice=7824900.sdhci`, `quiet loglevel=3`,
  `ipv6.disable=1`, `systemd.show_status=0`, `noinitrd`.
- The bootloader knows two special boot modes, `androidboot.mode=charger` and
  fast factory boot mode (`ffbm`, which selects `ffbm.target`).
- `serial-getty@ttyHSL0` is enabled at 115200 baud in the image. The
  lock-down step in `firmware-links.sh` stops it, and also switches ADB off,
  unless the provisioning file sets `SYSTEM_ACCESS` to `unlocked` or `beta`.

## Kernel and device tree

- Linux 3.18.71, built 2023-10-03, the same date as the firmware version string.
- Kernel config includes the MSM USB OTG driver, the MSM EHCI host driver,
  the Android gadget driver with ACM and FunctionFS functions, host-side
  CDC-ECM, CDC-NCM, ACM and USB-serial drivers, the MSM high-speed and
  low-speed UART drivers with a UART console, and an SMB135x battery-charger driver.
- 52 device trees are appended to the kernel. They are Qualcomm's stock set
  for MSM8909 and APQ8009 reference boards; none mention iRobot.
- The bootloader's console log names the one it selects: msm-id 265
  (APQ8009) with board-id 8 / 0x10e, which is the "APQ8009 Robot Reference
  Board" tree.
- Of the 52 trees, only three set the USB controller to OTG mode and the
  rest are device-only, going by the upstream `msm-hsusb` binding (1 =
  peripheral, 2 = host, 3 = OTG). The tree the robot uses is one of the three.
- That tree's USB node: OTG mode, ID and VBUS handled through the PMIC,
  and `qcom,dp-manual-pullup`, meaning software switches the D+ pull-up.
- UART1 (the console) is on SoC GPIO 4 and 5. A second, high-speed UART with
  flow control uses GPIO 20, 21, 111 and 112. These GPIOs are 1.8 V.

## USB behavior in the root filesystem

- The `usb` init script builds the gadget at boot. On this SoC it selects
  composition `9091`, which is VID `05C6`, PID `9091`.
- Production functions are RNDIS, DIAG, ACM and ADB. Fast factory mode uses
  DIAG, serial, a modem-style network interface and ADB.
- When locked down, ADB is disabled but RNDIS, DIAG and ACM stay on.
- The robot's RNDIS interface is `rndis0` at 192.168.186.2, with an alias at
  192.168.184.2.
- The beta firewall profile allows SSH, the two diag ports and FTP on `usb0`
  and `rndis0`.
- The robot can also act as a USB host. udev starts a service when the
  gadget state changes (an Edison logger on the other end, reached at
  192.168.186.1) and when a USB root hub appears (an SD logger, VID `0483`
  PID `572a`, CDC-ECM). The logger scripts are empty stubs in this release,
  so the hooks exist but do nothing.

## Other serial links

- The motor-controller link is a separate internal UART: udev maps `ttyHS0`
  to `/dev/ttyMobility0`. That is the SoC's high-speed UART2.
- The `manufacturing` daemon is a Wi-Fi and Bluetooth test reached over a
  network socket. It is not a wired factory protocol.

## Cross-check against our measurements

| Our finding | What the firmware says | Verdict |
|---|---|---|
| Face-up 6 is console TX at 115200 8N1, 1.8 V (boot capture decoded) | Console is UART1 at 115200 8N1; SBL1 and LK print there | Confirmed |
| Face-up 6 earlier labeled PWM | n/a | Retracted: 28.9 kHz is 115200 / 4, a data pattern |
| Face-up 7 silent, about 1.6 V | UART1 has an RX line on GPIO 5 | Plausible console RX, unconfirmed |
| Face-down 3 and 4 as D- and D+, D+ at 3.29 V | OTG controller, software-switched D+ pull-up, gadget `05C6:9091` | Consistent; needs a PC test |
| Face-down 5 (ID) at 0 V, open | ID goes through the PMIC, where a pull-up would be expected | Unexplained; may not be ID |
| Four 5 V pins sourced by the robot | Not mentioned; the Create 3 docs list 5.13 V at 3 A for the companion computer | Consistent with Create 3 |
| Jumpy 3.3 V pins (face-down 13, face-up 16) | The SoC side is 1.8 V, so 3.3 V lines are probably on the motor-controller side | Unidentified |

## What the firmware does not tell us

Nothing in the image mentions the physical connector, an adapter board, or
which pin carries which signal. The two interfaces above (USB and the UART
console) are the ones the software is built around, and our measurements
match both; whether the connector exposes more is a hardware question.

## Reproducing this

After step 2 of the README walkthrough, find the part that begins with the
bytes `ANDROID!`, then:

```
python -I bootimg_split.py work/parts/<boot_image_part>.bin work/bootimg
python -I fdt_dump.py work/bootimg/kernel.bin work/bootimg/dts
```

`bootimg_split.py` prints the command line and kernel version and writes the
kernel config. `fdt_dump.py` writes each embedded device tree as text. Outputs
under `work/` are git-ignored and must never be committed.

**Level warning:** the console is 1.8 V. Do not attach a 3.3 V serial adapter
to it.
