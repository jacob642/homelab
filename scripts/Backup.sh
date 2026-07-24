#!/bin/bash
#
# Backup.sh
# Creates a compressed tar.gz backup of the home directory, excluding
# the backup destination folder itself to avoid recursive bloat.
#
# Run manually with: ./Backup.sh
# Or automated on boot via systemd (see systemd/backup.service)

echo "Backup started"

backup=/home/jacob
dest="/home/jacob/Backup"
day=$(date +%A)
hostname=$(hostname -s)
archive="$hostname-$day.tgz"

tar czf "$dest/$archive" --exclude="$dest" "$backup"

echo "Backup finished"
