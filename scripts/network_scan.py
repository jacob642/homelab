#!/usr/bin/env python3
"""
network_scan.py

Collects basic system, network, resource, and security-scan information.
Each function is self-contained so it can be imported individually
(see Monitor.py) or run standalone for testing.
"""

import psutil
import socket
import platform
import subprocess


def get_local_ip():
    """Return this machine's LAN-facing IP address.

    Uses a UDP 'connect' to a public IP (no data is actually sent) so the
    OS resolves which local interface would be used for outbound traffic.
    This is more reliable than socket.gethostbyname(socket.gethostname()),
    which often just returns a loopback address.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def os_scan():
    """Print basic OS name and kernel/release version."""
    print("============")
    print("OS:", platform.system(), platform.release())
    print("============")


def memory_scan():
    """Print total/free/used RAM and usage percentage."""
    print("Memory scan")
    print("============")
    memory = psutil.virtual_memory()
    print(f"Total RAM: {memory.total / (1024**3):.2f} GB")
    print(f"Free RAM: {memory.available / (1024**3):.2f}GB")
    print(f"Used RAM: {memory.used / (1024**3):.2f}GB")
    print(f"Usage: {memory.percent}%")


def CPU_scan():
    """Print per-core CPU usage percentage."""
    print("CPU Scan")
    print("============")
    cores = psutil.cpu_percent(interval=1, percpu=True)
    for i, usage in enumerate(cores, start=1):
        print(f"core {i} = {usage}%")
    print("============")


def disk_usage():
    """Print total/used/free disk space and usage percentage for '/'."""
    print("Disk usage")
    print("============")
    disk = psutil.disk_usage("/")
    print(f"Total: {disk.total / (1024**3):.2f} GB")
    print(f"Used: {disk.used / (1024**3):.2f} GB")
    print(f"Free: {disk.free / (1024**3):.2f} GB")
    print(f"Usage: {disk.percent}%")
    print("============")


def nmap_scan(target=None):
    """Run an nmap scan against the given target (defaults to this host)."""
    if target is None:
        target = get_local_ip()
    print("Nmap Scan")
    print("========")
    result = subprocess.run(["nmap", target], capture_output=True, text=True)
    print(result.stdout)
    print("========")


if __name__ == "__main__":
    os_scan()
    memory_scan()
    CPU_scan()
    disk_usage()
    print("IP:", get_local_ip())
    nmap_scan()
