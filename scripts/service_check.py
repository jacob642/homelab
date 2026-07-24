#!/usr/bin/env python3
"""
service_check.py

Checks running systemd services and processes on the host.
"""

import subprocess
import psutil


def check_process_status(process_name):
    """Print PID, name, and status for any running process matching process_name."""
    process_status = [proc for proc in psutil.process_iter() if proc.name() == process_name]
    if process_status:
        for current_process in process_status:
            print("Process id is %s, name is %s, status is %s" % (
                current_process.pid, current_process.name(), current_process.status()))
    else:
        print("Process name not valid:", process_name)


def list_running_services():
    """List all currently running systemd services in a simple table."""
    print("=" * 70)
    print("RUNNING SERVICES")
    print("=" * 70)
    print(f"{'SERVICE':40} {'STATE'}")
    print("-" * 70)

    try:
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--state=running",
                "--no-pager",
                "--no-legend",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 4:
                print(f"{fields[0]:40} {fields[2]}")

    except subprocess.CalledProcessError as err:
        print(f"Error retrieving services: {err}")


def list_running_processes():
    """List all running processes with PID, name, and status."""
    print("\n" + "=" * 70)
    print("RUNNING PROCESSES")
    print("=" * 70)
    print(f"{'PID':>8} {'NAME':30} {'STATUS'}")
    print("-" * 70)

    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            print(
                f"{proc.info['pid']:>8} "
                f"{(proc.info['name'] or 'Unknown')[:30]:30} "
                f"{proc.info['status']}"
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def main():
    list_running_services()
    list_running_processes()


if __name__ == "__main__":
    main()
