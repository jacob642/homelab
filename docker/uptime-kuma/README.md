# Uptime Kuma

Monitoring dashboard, running in Docker at `http://192.168.56.101:3001`. Watches nginx, Portainer, the VM itself, and SSH.

## docker-compose.yml

```yaml
version: "3"
services:
  uptime-kuma:
    container_name: uptime-kuma
    image: louislam/uptime-kuma
    restart: always
    ports:
      - "3001:3001"
    volumes:
      - ./data:/app/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

The `extra_hosts` line lets Uptime Kuma resolve the host machine by name from inside its own container, needed because container networking doesn't automatically see the host the same way the host sees itself. See the main README's "Problems I ran into" section for the full story on debugging this.
