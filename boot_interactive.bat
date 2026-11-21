@echo off
rem Boots the emulated robot with its console in THIS window. No network device.
rem Quit QEMU: press Ctrl+A, then X.
rem Set QEMU_SYSTEM_ARM if qemu-system-arm.exe isn't on your PATH or in the default install location.
set "QEMU_BIN=%QEMU_SYSTEM_ARM%"
if "%QEMU_BIN%"=="" set "QEMU_BIN=qemu-system-arm.exe"
where "%QEMU_BIN%" >nul 2>&1 || set "QEMU_BIN=C:\Program Files\qemu\qemu-system-arm.exe"
"%QEMU_BIN%" -M virt -cpu cortex-a15 -m 1536 ^
  -kernel "%~dp0work\kernel\vmlinuz-6.1.0-50-armmp" ^
  -initrd "%~dp0work\robot-initramfs.cpio.gz" ^
  -append "console=ttyAMA0 rdinit=/init panic=-1" ^
  -nographic -nic none -no-reboot
