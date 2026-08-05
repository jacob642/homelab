# Homelab

My Ubuntu homelab, running as a VM. It's got custom scripts for system monitoring, automated backups, file sharing over Samba, and basic user management. I built this to get real hands-on practice with Linux system administration, networking, and shell/Python scripting. It's the kind of stuff that doesn't really click until you break something and have to fix it yourself.

## Why I built this

I wanted practical experience with day-to-day sysadmin work that you don't really get in a classroom. Writing scripts that actually work against a real filesystem and network, debugging shell quoting issues, setting up services like systemd and Samba properly instead of just reading about them.

## Setup

- Host: Windows 11
- Guest: Ubuntu Server, running in VirtualBox
- Networking: two adapters, NAT (10.0.2.15, for internet access) and Host-Only (192.168.56.101, so the Windows host can talk directly to the VM)
- File sharing: Samba, bound to the Host-Only interface
- Web server: nginx, serving a static homepage
- Reverse proxy: Traefik, routing to the various services below
- Containers: Docker, managed through Portainer, running at `https://192.168.56.101:9443`
- Monitoring: Uptime Kuma, watching nginx, Portainer, the VM itself, and SSH
- Metrics: Prometheus scraping Node-Exporter (host metrics) and cAdvisor (per-container metrics), visualized in Grafana
- Dashboard: Homepage, a single page with tiles for everything running (containers, services, infrastructure, security)
- Logs: Dozzle, a lightweight log viewer for Docker containers, plus Loki and Promtail for centralized log aggregation
- Container updates: Watchtower, keeps images up to date automatically
- DNS: Bind9
- Intrusion prevention: Fail2Ban (SSH) and CrowdSec (SSH, nginx, and Docker container logs), enforced at the firewall level via the CrowdSec nftables bouncer
- SIEM / XDR: Wazuh, run on-demand rather than continuously (see Security Stack below)
- SIEM (secondary): Splunk, installed on the Windows host, pending license renewal before use
- Other VMs on the network: a Windows host, and a Kali box (from an earlier course, added to the same network so it's easy to reach from Ubuntu)

## What's in here

| Path | What it does |
|---|---|
| `scripts/Monitor.py` | Main system report: CPU, memory, disk, IP, running services/processes, and an nmap scan |
| `scripts/network_scan.py` | The individual functions Monitor.py pulls from: IP detection, OS info, memory, CPU, disk usage, nmap |
| `scripts/service_check.py` | Lists running systemd services and processes in a readable table |
| `scripts/Backup.sh` | Backs up the home directory to a dated .tgz archive, skips the backup folder itself so it doesn't back up its own backups |
| `scripts/System_update.sh` | Runs apt update/upgrade/cleanup and a snap refresh |
| `scripts/create_user.sh` (aka `AddUser.sh`) | Creates a new Linux user, validates the username, locks the account until a password is set |
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
| `docker/grafana/` | Grafana dashboards for the collected metrics |
| `docker/loki/` & `docker/promtail/` | Centralized log aggregation — Promtail ships logs, Loki stores/indexes them |
| `docker/crowdsec/` | CrowdSec config — collections, acquisition sources (SSH, nginx, Docker logs) |
| `docker/wazuh/` | Wazuh single-node stack (indexer, manager, dashboard) — see Security Stack |
| `diagrams/` | Architecture/network diagrams |
| `screenshots/` | Screenshots referenced from this README |
| `docs/` | Supporting documentation and notes |

## Problems I ran into

**Bash quoting is unforgiving.** I spent way too long chasing an "unexpected EOF" error in Backup.sh. Turned out to be a missing quote near the end of a long line, easy to miss just by reading it. Learned to use `bash -n script.sh` to check syntax without running it, and `cat -A` or `od -c` to look at the raw bytes when I couldn't trust what the terminal was showing me.

**Paths are case-sensitive on Linux.** My systemd service kept failing with `status=203/EXEC` and I couldn't figure out why, until I noticed the ExecStart path was `/Home/Jacob/...` instead of `/home/jacob/...`. Old Windows habit, doesn't work here.

**Samba binds to every interface by default.** I've got three network interfaces on this VM (NAT, Host-Only, and Docker's bridge), so I had to tell Samba explicitly which one to use with `interfaces` and `bind interfaces only` in smb.conf, otherwise it's ambiguous which IP you're supposed to connect to from Windows.

**Splitting one big script into smaller pieces.** Monitor.py used to be one long file doing everything. Now it just imports functions from network_scan.py and service_check.py, so I can test or change one piece without touching the rest.

**Monitoring a container from another container.** Set up Uptime Kuma to watch Portainer, and it kept showing 0% up with a timeout error, even though Portainer was clearly running fine. Since Uptime Kuma runs in its own Docker container, `127.0.0.1` and even the VM's real IP weren't reliable ways for it to reach Portainer, container networking doesn't automatically see the outside world the same way the host does. Fixed it two ways: added `extra_hosts: host.docker.internal:host-gateway` to Uptime Kuma's docker-compose.yml so it could resolve the host machine by name, and separately found Portainer's actual container IP on the Docker bridge network (172.17.0.3) through Portainer's own container list and pointed the monitor straight at that instead. Also had to turn on "Ignore TLS/SSL errors" in the monitor settings since Portainer uses a self-signed cert, and bumped the retry count up so one slow handshake didn't get flagged as a full outage.

**Port 53 was already taken.** Setting up Bind9 for DNS, the container wouldn't bind to port 53. Turned out Ubuntu runs its own local DNS resolver (systemd-resolved) on that port by default, so Bind9 was trying to grab a port that was already in use. Had to sort that out before Bind9 would actually start. Also just generally fighting nano's syntax while editing the config files, awkward to get right compared to writing in a proper editor.

**cAdvisor kept crashing on startup.** The docker-compose.yml looked fine (valid YAML, all the right mounts), but the container kept dying right after starting with a Go panic (nil pointer dereference) somewhere in its Docker container-handling code. Docker itself registered fine in the logs, it just crashed straight after. Common issue with cAdvisor on newer Docker versions when it's pulling `:latest` instead of a pinned version.

**Homepage dashboard icons not showing.** A few tiles on the Homepage dashboard (Samba, Ubuntu) had missing icons even though the filenames looked reasonable. Turned out the icon pack (dashboardicons.com) uses more specific names than the plain service name, `samba-server.png` instead of `samba.png`, and `ubuntu-linux.png` instead of `ubuntu.png`. Worth checking the actual site for the exact filename rather than guessing.

**An imported Grafana dashboard showed "No data" everywhere.** Prometheus confirmed both cAdvisor and Node-Exporter targets were up and scraping fine, so the data existed, Grafana just wasn't showing it. First problem was the dashboard's data source variable (`${DS_PROMETHEUS}`) pointing at nothing, from importing without properly mapping it to the actual Prometheus data source. Re-importing and setting that mapping fixed the "datasource not found" error, but the panels still showed no data after that. Traced it down to the dashboard's queries depending on `$host`/`$container` template variables that weren't resolving against my actual label values, likely an older dashboard built around a different cAdvisor label convention. Rather than fight that one dashboard's variables, switched to a different community dashboard that worked out of the box.

## Security Stack

The homelab runs a layered security setup: Fail2Ban and CrowdSec for active intrusion prevention, and Wazuh (plus, eventually, Splunk) for detection and log analysis. Here's how each piece came together.

### CrowdSec

Deployed as a Docker container, joined to the existing `homelab` network alongside Traefik, Portainer, and the rest of the stack rather than running isolated. It watches SSH (`/var/log/auth.log`), nginx access/error logs, and selected Docker container logs, using the `sshd`, `nginx`, and `linux` collections.

Remediation is handled by the native `crowdsec-firewall-bouncer` (nftables), installed directly on the host rather than in a container, since it needs to manipulate the host's firewall rules. The bouncer talks to CrowdSec's Local API over a fixed port.

**Port conflict:** the Local API's default port (8080) was already taken by an existing `docker-proxy` process, and the next couple of fallback ports (8081, 8082) were too. Checked with:
```bash
sudo ss -tulpn | grep -E '8080|8081|8082|8083'
```
Landed on **8083**, confirmed free, and set it consistently in both the CrowdSec `docker-compose.yml` port mapping and the bouncer's `api_url` in `/etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml`. These two configs have to agree, or the bouncer can't reach CrowdSec at all.

**Fail2Ban overlap:** currently both Fail2Ban and CrowdSec watch SSH. Left as-is for now as defense-in-depth — worth revisiting later whether to consolidate onto one.

**Status:** live and running.

### Splunk

Installed on the Windows 11 host, intended to receive forwarded logs from the Ubuntu VM as a second SIEM alongside Wazuh. Currently blocked on a license renewal — not yet forwarding anything.

**Status:** installed, not yet operational.

### Wazuh

Deployed as a single-node stack (indexer, manager, dashboard) to add proper SIEM/XDR capability on top of Fail2Ban and CrowdSec's prevention layer — log analysis, file integrity monitoring, and threat detection.

The deployment went through a genuine multi-layer debugging process, redeployed from scratch after an earlier instance stopped feeding its dashboard and proved hard to debug live:

**Bug 1 — wrong branch, unpublished image.** The original setup was cloned from the `main` branch of the `wazuh-docker` repo, which was ahead of the actually published Docker images. `docker compose up -d` failed trying to pull `wazuh/wazuh-dashboard:5.1.0`, a tag that didn't exist on Docker Hub. Fixed by cloning a proper tagged release instead of `main`:
```bash
git clone https://github.com/wazuh/wazuh-docker.git -b v4.14.6 --depth=1
```

**Port conflicts on 443/445.** Both were already bound by other services on the VM. Edited `docker-compose.yml` to remap the dashboard's exposed ports (dashboard ended up on 4446) before bringing the stack up.

**Bug 2 — certs were directories, not files.** Once containers were up, the dashboard showed `ERROR3099 - Server not ready yet` and couldn't find a working API connection. Manager logs showed the real cause:

Filebeat — which ships alerts from the manager to the indexer — was crash-looping because several files under `config/wazuh_indexer_ssl_certs/` had somehow been created as empty **directories** instead of actual `.pem`/`.key` files. Every dashboard symptom (no API, no matching index patterns, no alerts) traced back to this one broken link in the chain. Fixed by wiping and regenerating the certs:
```bash
docker compose down
sudo rm -rf config/wazuh_indexer_ssl_certs
docker compose -f generate-indexer-certs.yml run --rm generator
```

**Bug 3 — inconsistent cert ownership.** After regenerating, all files were proper regular files, but three (`root-ca-manager.key`, `root-ca-manager.pem`, `wazuh.manager.pem`) were owned by `dnsmasq:systemd-journal` instead of `jacob:jacob` like the rest. Fixed with:
```bash
sudo find config/wazuh_indexer_ssl_certs -type f -exec chown jacob:jacob {} \;
```

**Indexer startup timing.** Even after both fixes, the manager briefly showed `connection refused` trying to reach the indexer on port 9200 — not a config problem, just the indexer (OpenSearch) still finishing its own startup. Waiting roughly a minute resolved it; logs flipped cleanly from `retrying until the connection is successful` to `initialized successfully` across every index, and filebeat confirmed `Connection to backoff(elasticsearch(https://wazuh.indexer:9200)) established`.

**Confirmed working end-to-end:** API status Online, manager v4.14.6, dashboard fully functional, and the instance had already generated real alerts (45 medium, 142 low severity in 24 hours) purely from monitoring the manager host itself, before any agents were deployed.

**Resource reality check:** running the full Wazuh stack (indexer/manager/dashboard) alongside the rest of the homelab pushed the host — 16GB RAM total, VM allocated ~10GB — to zero free memory, and separately, Wazuh's containers and volumes (the manager's container layer and the `wazuh_queue` volume in particular) consumed close to 16GB of disk space on their own. Rather than over-provision a VM sharing resources with a daily-use Windows machine, the call was made to run Wazuh **on-demand** instead of continuously, and to free the disk space once the working setup was proven and documented.

**Status:** proven working end-to-end, stack currently torn down to reclaim resources. Redeploying is a known, documented process (above) rather than a fresh debugging exercise — the next run will need certs regenerated from scratch, since volumes aren't persisted between teardowns. Revisiting with dedicated hardware once budget allows, since 16GB shared between host and VM is the real ceiling here, not a configuration problem.

## Homepage Dashboard

The Homepage dashboard (`http://192.168.56.101:3000`) ties the whole stack together on one page, grouped into four sections:

- **Containers** — Portainer, Uptime Kuma, Traefik, Dozzle, Watchtower, Node-Exporter, cAdvisor, Prometheus, Grafana
- **Services** — nginx, Samba, SSH, Docker Engine
- **Infrastructure** — Ubuntu, Windows Host, Kali
- **Security** — Hardened SSH, UFW Firewall, Automated Backups, CrowdSec, Wazuh

Live CPU, memory, and disk stats are shown at the top of the dashboard via its built-in system widget.

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

# bring Wazuh back up (from a clean/reset state — will need cert regeneration, see Security Stack above)
cd docker/wazuh/wazuh-docker/single-node
docker compose -f generate-indexer-certs.yml run --rm generator
sudo find config/wazuh_indexer_ssl_certs -type f -exec chown jacob:jacob {} \;
docker compose up -d

# stop Wazuh to free RAM/disk when not actively using it
cd docker/wazuh/wazuh-docker/single-node
docker compose stop      # keeps containers/data, releases RAM
# docker compose down -v   # full teardown, also reclaims disk space, but requires cert regen next time
```

## Current Status

- **Active:** Fail2Ban, CrowdSec, Docker stack (Portainer, Traefik, Prometheus, Grafana, Loki/Promtail, Uptime Kuma, Dozzle, Watchtower, Bind9)
- **On-demand (torn down when not in use):** Wazuh — indexer, manager, dashboard
- **Blocked:** Splunk — installed, awaiting license renewal before log forwarding can be configured

## Notes

- The IPs in here are private LAN/VirtualBox addresses, nothing public-facing.
- Backup.sh and backup.service have my actual home directory path (/home/jacob) hardcoded. Change that if you're reusing this on a different machine.
- Wazuh's data volumes are not currently persisted between teardowns — redeploying starts from a clean state and needs certs regenerated (documented above).