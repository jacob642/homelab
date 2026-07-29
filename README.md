# Homelab

My Ubuntu homelab, running as a VM. It's got custom scripts for system monitoring, automated backups, file sharing over Samba, and basic user management. I built this to get real hands-on practice with Linux system administration, networking, and shell/Python scripting. It's the kind of stuff that doesn't really click until you break something and have to fix it yourself.

## Why I built this

I wanted practical experience with day-to-day sysadmin work that you don't really get in a classroom. Writing scripts that actually work against a real filesystem and network, debugging shell quoting issues, setting up services like systemd and Samba properly instead of just reading about them.

## Setup

- Host: Windows
- Guest: Ubuntu Server, running in VirtualBox
- Networking: two adapters, NAT (10.0.2.15, for internet access) and Host-Only (192.168.56.101, so the Windows host can talk directly to the VM)
- File sharing: Samba, bound to the Host-Only interface
- Web server: nginx, serving a static homepage
- Reverse proxy: Traefik, routing to the various services below
- Containers: Docker, managed through Portainer, running at `https://192.168.56.101:9443`
- Monitoring: Uptime Kuma, watching nginx, Portainer, the VM itself, and SSH
- Metrics: Prometheus, scraping Node-Exporter (host metrics) and cAdvisor (per-container metrics)
- Dashboard: Homepage, a single page with tiles for everything running (containers, servers, infrastructure)
- Logs: Dozzle, a lightweight log viewer for Docker containers
- Container updates: Watchtower, keeps images up to date automatically
- DNS: Bind9
- Other VMs on the network: a Windows host, and a Kali box (from an earlier course, added to the same network so it's easy to reach from Ubuntu)

## What's in here

| Path | What it does |
|---|---|
| `scripts/Monitor.py` | Main system report: CPU, memory, disk, IP, running services/processes, and an nmap scan |
| `scripts/network_scan.py` | The individual functions Monitor.py pulls from: IP detection, OS info, memory, CPU, disk usage, nmap |
| `scripts/service_check.py` | Lists running systemd services and processes in a readable table |
| `scripts/Backup.sh` | Backs up the home directory to a dated .tgz archive, skips the backup folder itself so it doesn't back up its own backups |
| `scripts/System_update.sh` | Runs apt update/upgrade/cleanup and a snap refresh |
| `scripts/create_user.sh` | Creates a new Linux user, validates the username, locks the account until a password is set |
| `systemd/backup.service` | Runs Backup.sh automatically on boot |
| `samba/smb.conf.example` | Samba config, restricted to the Host-Only interface |
| `nginx/default.conf.example` | nginx config for the static homepage |
| `docker/portainer/` | Notes on the Portainer setup |
| `docker/uptime-kuma/` | Uptime Kuma's docker-compose.yml and setup notes |
| `docker/homepage/` | Homepage dashboard config (services.yaml, widgets.yaml) |
| `docker/traefik/` | Traefik reverse proxy config |
| `docker/dozzle/` | Dozzle log viewer setup |
| `docker/watchtower/` | Watchtower auto-update setup |
| `docker/dns/` | Bind9 DNS config |
| `docker/node-exporter/` | Node-Exporter setup, feeds host metrics to Prometheus |
| `docker/cadvisor/` | cAdvisor setup, feeds per-container metrics to Prometheus |
| `docker/prometheus/` | Prometheus config, scraping Node-Exporter and cAdvisor |
| `diagrams/` | Architecture/network diagrams |
| `screenshots/` | Screenshots referenced from this README |

## Problems I ran into

**Bash quoting is unforgiving.** I spent way too long chasing an "unexpected EOF" error in Backup.sh. Turned out to be a missing quote near the end of a long line, easy to miss just by reading it. Learned to use `bash -n script.sh` to check syntax without running it, and `cat -A` or `od -c` to look at the raw bytes when I couldn't trust what the terminal was showing me.

**Paths are case-sensitive on Linux.** My systemd service kept failing with `status=203/EXEC` and I couldn't figure out why, until I noticed the ExecStart path was `/Home/Jacob/...` instead of `/home/jacob/...`. Old Windows habit, doesn't work here.

**Samba binds to every interface by default.** I've got three network interfaces on this VM (NAT, Host-Only, and Docker's bridge), so I had to tell Samba explicitly which one to use with `interfaces` and `bind interfaces only` in smb.conf, otherwise it's ambiguous which IP you're supposed to connect to from Windows.

**Splitting one big script into smaller pieces.** Monitor.py used to be one long file doing everything. Now it just imports functions from network_scan.py and service_check.py, so I can test or change one piece without touching the rest.

**Monitoring a container from another container.** Set up Uptime Kuma to watch Portainer, and it kept showing 0% up with a timeout error, even though Portainer was clearly running fine. Since Uptime Kuma runs in its own Docker container, `127.0.0.1` and even the VM's real IP weren't reliable ways for it to reach Portainer, container networking doesn't automatically see the outside world the same way the host does. Fixed it two ways: added `extra_hosts: host.docker.internal:host-gateway` to Uptime Kuma's docker-compose.yml so it could resolve the host machine by name, and separately found Portainer's actual container IP on the Docker bridge network (172.17.0.3) through Portainer's own container list and pointed the monitor straight at that instead. Also had to turn on "Ignore TLS/SSL errors" in the monitor settings since Portainer uses a self-signed cert, and bumped the retry count up so one slow handshake didn't get flagged as a full outage.

**Port 53 was already taken.** Setting up Bind9 for DNS, the container wouldn't bind to port 53. Turned out Ubuntu runs its own local DNS resolver (systemd-resolved) on that port by default, so Bind9 was trying to grab a port that was already in use. Had to sort that out before Bind9 would actually start. Also just generally fighting nano's syntax while editing the config files, awkward to get right compared to writing in a proper editor.

**cAdvisor kept crashing on startup.** The docker-compose.yml looked fine (valid YAML, all the right mounts), but the container kept dying right after starting with a Go panic (nil pointer dereference) somewhere in its Docker container-handling code. Docker itself registered fine in the logs, it just crashed straight after. Common issue with cAdvisor on newer Docker versions when it's pulling `:latest` instead of a pinned version.

**Homepage dashboard icons not showing.** A few tiles on the Homepage dashboard (Samba, Ubuntu) had missing icons even though the filenames looked reasonable. Turned out the icon pack (dashboardicons.com) uses more specific names than the plain service name, `samba-server.png` instead of `samba.png`, and `ubuntu-linux.png` instead of `ubuntu.png`. Worth checking the actual site for the exact filename rather than guessing.

## Running it

```bash
# full system report
python3 scripts/Monitor.py

# manual backup
./scripts/Backup.sh

# set up automatic backups on boot
sudo cp systemd/backup.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now backup.service

# system update
./scripts/System_update.sh

# create a new user (needs root)
sudo ./scripts/create_user.sh
```

## Notes

- The IPs in here are private LAN/VirtualBox addresses, nothing public-facing.
- Backup.sh and backup.service have my actual home directory path (/home/jacob) hardcoded. Change that if you're reusing this on a different machine.