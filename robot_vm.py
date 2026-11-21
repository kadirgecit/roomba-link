#!/usr/bin/env python3
"""Boot the emulated robot in QEMU (no network device) and run shell commands
over the serial console. Usage:  robot_vm.py "cmd1" "cmd2" ...
Each command's output is printed; the VM is powered off at the end.
"""
import os
import shutil
import socket
import subprocess
import sys
import time

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work")
QEMU = os.environ.get("QEMU_SYSTEM_ARM") or shutil.which("qemu-system-arm") or r"C:\Program Files\qemu\qemu-system-arm.exe"
PORT = 4555


def main(cmds):
    p = subprocess.Popen(
        [QEMU, "-M", "virt", "-cpu", "cortex-a15", "-m", "1536",
         "-kernel", BASE + r"\kernel\vmlinuz-6.1.0-50-armmp",
         "-initrd", BASE + r"\robot-initramfs.cpio.gz",
         "-append", "console=ttyAMA0 rdinit=/init panic=-1",
         "-display", "none", "-monitor", "none", "-nic", "none", "-no-reboot",
         "-serial", f"tcp:127.0.0.1:{PORT},server,nowait"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    s = None
    for _ in range(60):
        try:
            s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
            break
        except OSError:
            time.sleep(1)
    s.settimeout(1)

    def read_until(marker, timeout):
        buf, end = b"", time.time() + timeout
        while time.time() < end and marker not in buf:
            try:
                d = s.recv(65536)
                if not d:
                    break
                buf += d
            except socket.timeout:
                pass
        return buf.decode("latin1")

    try:
        read_until(b"/ #", 180)
        for c in cmds:
            tag = f"__DONE{int(time.time()*1000)}__"
            s.sendall((c + f"\necho {tag}\n").encode())
            out = read_until(tag.encode() + b"\r\n", 90)
            out = out.split(tag)[-2] if out.count(tag) >= 2 else out
            print(f"$ {c}\n{out.strip()}\n", flush=True)
    finally:
        try:
            s.sendall(b"poweroff -f\n")
        except OSError:
            pass
        time.sleep(1)
        p.kill()


if __name__ == "__main__":
    main(sys.argv[1:])
