#!/usr/bin/env bash
#
# create_user.sh
# Interactively creates a new local Linux user account, with basic
# validation and a locked password until one is set manually.
#
# Must be run as root: sudo ./create_user.sh

set -euo pipefail

# Must be run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi

read -rp "Enter username: " uname

# Check if username was provided
if [[ -z "$uname" ]]; then
    echo "Username cannot be empty."
    exit 1
fi

# Validate username (lowercase letters/numbers/underscore/hyphen, max 32 chars)
if [[ ! "$uname" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
    echo "Invalid username."
    exit 1
fi

# Check if user already exists
if id "$uname" &>/dev/null; then
    echo "User already exists."
    exit 0
fi

# Create the user
useradd -m -s /bin/bash "$uname"

# Lock the account until a password is set
passwd -l "$uname" >/dev/null

chmod 700 "/home/$uname"

echo "User '$uname' created successfully. Set a password with: passwd $uname"
