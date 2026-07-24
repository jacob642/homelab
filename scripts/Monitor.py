#!/usr/bin/env python3
"""
Monitor.py

Main entry point that runs a full system report by pulling together
all the individual scan functions from network_scan.py and service_check.py.

Usage:
    ./Monitor.py
"""

from network_scan import os_scan, memory_scan, get_local_ip, CPU_scan, disk_usage, nmap_scan
from service_check import list_running_services, list_running_processes

os_scan()
CPU_scan()
memory_scan()
disk_usage()
print("IP:", get_local_ip())
nmap_scan()
list_running_services()
list_running_processes()
