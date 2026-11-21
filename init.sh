#!/bin/busybox sh
# Our own PID 1 for the emulated robot. Replaces the real systemd/hardware bring-up.
/bin/busybox mount -t proc proc /proc
/bin/busybox mount -t sysfs sysfs /sys
/bin/busybox mount -t devtmpfs devtmpfs /dev 2>/dev/null
/bin/busybox mount -t tmpfs tmpfs /tmp
/bin/busybox mount -t tmpfs tmpfs /run
/bin/busybox --install -s 2>/dev/null
ifconfig lo 127.0.0.1 up
echo "=== emulated robot userland up (offline: loopback only) ==="
uname -a
cat /etc/version
echo "--- /opt/irobot/bin:"
ls /opt/irobot/bin | head -40
echo "Tip: Ctrl+C now works. Start daemons with '&' and redirect output to /tmp/x.log"
exec setsid /bin/busybox cttyhack /bin/sh
