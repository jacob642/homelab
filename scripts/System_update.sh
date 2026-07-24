#!/usr/bin/env bash
#
# System_update.sh
# Runs a full system update: apt update/upgrade, cleanup, and snap refresh.

echo "===================================="
echo "starting to update"
echo "Date: $(date)"
echo "===================================="

sudo apt update -y &&
sudo apt full-upgrade -y &&
sudo apt autoremove -y &&
sudo apt autoclean -y &&
sudo snap refresh

echo "===================================="
echo "System update completed"
echo "Update Finished $(date)"
