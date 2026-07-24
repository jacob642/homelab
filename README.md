# Homelab

A self-hosted Ubuntu homelab environment (running as a VM) with custom
system monitoring, automated backups, file sharing over Samba, and basic
user-management tooling — built to get hands-on with Linux system
administration, networking, and shell/Python scripting.

## Why

I wanted practical experience with the kind of day-to-day sysadmin work
that doesn't show up in a classroom: writing scripts that actually work
against a real filesystem and a real network, debugging shell quoting
issues, and configuring services (systemd, Samba) the way they'd be
configured on a real server.

## Architecture

- **Host:** Windows
- **Guest:** Ubuntu Server (VirtualBox VM)
- **Networking:** dual adapters — NAT (`10.0.2.15`, internet access) and
  Host-Only (`192.168.56.101`, direct host↔guest communication)
- **File sharing:** Samba, bound explicitly to the Host-Only interface

## What's in here

| Path | What it does |
|---|---|
| `scripts/Monitor.py` | Pulls together CPU, memory, disk, IP, running services/processes, and an nmap scan into a single system report |
| `scripts/network_scan.py` | Standalone functions for IP detection, OS info, memory, CPU, disk usage, and nmap scanning |
| `scripts/service_check.py` | Lists running systemd services and processes in a readable table |
| `scripts/Backup.sh` | Backs up the home directory to a dated `.tgz` archive, excluding the backup folder itself |
| `scripts/System_update.sh` | Runs a full `apt`/`snap` update and cleanup |
| `scripts/create_user.sh` | Interactively creates a new Linux user with validation and a locked password until set |
| `systemd/backup.service` | Runs `Backup.sh` automatically on every boot |
| `samba/smb.conf.example` | Samba config restricting binding to the Host-Only network interface |

## Challenges & what I learned

- **Bash quoting bugs are unforgiving.** Spent a good while chasing an
  `unexpected EOF while looking for matching '"'` error in `Backup.sh`
  that turned out to be a stray/missing quote — learned to verify with
  `bash -n script.sh` (syntax check without running) and `cat -A` /
  `od -c` to inspect raw file bytes rather than trusting how a terminal
  renders it.
- **Path case-sensitivity.** A systemd service silently failed with
  `status=203/EXEC` because the `ExecStart` path used
  `/Home/Jacob/...` instead of the actual lowercase `/home/jacob/...`.
  Linux paths are case-sensitive; Windows habits don't transfer.
- **Samba interface binding.** By default Samba listens on every network
  interface. With three interfaces present (NAT, Host-Only, Docker's
  bridge), I explicitly restricted Samba to the Host-Only adapter using
  `interfaces` + `bind interfaces only` in `smb.conf`, so there's no
  ambiguity about which IP to connect to from the Windows host.
- **Modular Python over one big script.** Split system-report logic into
  separate importable modules (`network_scan.py`, `service_check.py`)
  called from one entry point (`Monitor.py`), so any individual scan can
  be tested or changed independently.

## Running it

```bash
# Full system report
python3 scripts/Monitor.py

# Manual backup
./scripts/Backup.sh

# Automate backups on boot
sudo cp systemd/backup.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now backup.service

# System update
./scripts/System_update.sh

# Create a new user (must be run as root)
sudo ./scripts/create_user.sh
```

## Notes

- IPs referenced here are private LAN/VirtualBox addresses, not publicly
  reachable.
- `Backup.sh` and `backup.service` use hardcoded paths (`/home/jacob/...`)
  matching my own setup — update these if reusing on another machine.
