# Garden Controller

Raspberry Pi Zero 2W MQTT subscriber that listens for irrigation instructions and controls relay-driven solenoid valves via GPIO.

---

## Hardware

- Raspberry Pi Zero 2W
- 7-zone relay board (5V coil, switches 12V)
- 7 x 12V solenoid valves
- 12V power supply (5A minimum, 12A battery recommended)
- 12V → 5V buck converter (3A) for Pi + relay board
- Solar panel (30W) + MPPT charge controller for off-grid use

### GPIO Pin Mapping

| Zone | GPIO (BCM) |
|------|-----------|
| 1    | 2         |
| 2    | 3         |
| 3    | 4         |
| 4    | 22        |
| 5    | 27        |
| 6    | 18        |
| 7    | 10        |

Relays are active LOW — GPIO HIGH = relay off, GPIO LOW = relay on.

---

## Software

Python 3.9, runs inside Docker via `docker-compose`.

### Dependencies

```
paho-mqtt
python-dotenv
RPi.GPIO
```

### Environment Variables (`.env`)

```
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_BROKER=
MQTT_PORT=
DEVICE_NAME=
ZONE=
ENVIRONMENT=raspberry_pi
```

### Run

```bash
docker compose up -d
```

---

## MQTT Topics

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `healthcheck/request` | Subscribe | Triggers a health check response |
| `irrigation/currentState` | Subscribe | Sets relay states for all zones |
| `healthcheck/response` | Publish | Responds with device name |

---

## Fresh Pi Setup — Do This First

### 1. Disable WiFi Power Management via NetworkManager

**This is the most important step.** The Pi Zero 2W's WiFi chip aggressively enters power-save mode when idle. This causes:
- WiFi dropouts every ~10 minutes
- Slow SSH response
- Missed MQTT messages / health checks not responding

The fix must go through NetworkManager (not just `iwconfig`) otherwise it gets overridden on reconnect.

```bash
sudo nano /etc/NetworkManager/conf.d/wifi-power.conf
```

Add:
```ini
[connection]
wifi.powersave = 2
```

Restart NetworkManager:
```bash
sudo systemctl restart NetworkManager
```

Verify:
```bash
iwconfig wlan0 | grep "Power Management"
# Must show: Power Management:off
```

### 2. Keepalive Ping (belt and braces)

Some routers prune idle WiFi clients from their ARP table. Add a cron job to generate periodic traffic:

```bash
crontab -e
```

Add:
```
*/3 * * * * ping -c 1 $(ip route | grep default | awk '{print $3}') > /dev/null 2>&1
```

### 3. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker pi
```

Log out and back in, then verify:
```bash
docker run hello-world
```

### 4. Clone and configure

```bash
git clone <repo-url>
cd garden-controller
cp .env.example .env
nano .env  # fill in your values
```

### 5. Start the service

```bash
docker compose up -d
docker compose logs -f
```

---

## Power Setup (Off-Grid Battery)

- **12V 12Ah battery** topped up by **30W solar panel** via MPPT charge controller
- Daily consumption: ~7–8Ah (Pi + relays running 24/7)
- 30W panel generates ~10–12Ah/day — comfortable margin on sunny days, ~1.5 days reserve on no sun
- Use MPPT controller, not PWM — meaningfully more harvest from a 30W panel
- Charging voltage reaches 13.6–14.4V — verify your 5V converter handles this input range

---

## Troubleshooting

### WiFi drops every ~10 minutes
NetworkManager is re-enabling WiFi power save. See **Step 1** above.

### SSH is slow / laggy
Same cause — WiFi power save mode. Fix with NetworkManager config above.

### Health checks not always responding
1. First fix WiFi power management (above)
2. Check MQTT broker logs to see if client is disconnecting
3. Verify Docker container is running: `docker compose ps`

### Checking WiFi power management state
```bash
iwconfig wlan0 | grep "Power Management"
```

### Checking NetworkManager logs live
```bash
journalctl -fu NetworkManager
```

### Checking DHCP lease
```bash
ip addr show wlan0
# Look for valid_lft — should be hours, not minutes
```
