![CI](https://github.com/Buie-Dev/controllers.garden/actions/workflows/ci.yml/badge.svg?branch=dev)

# controllers.garden

Raspberry Pi Zero 2W service that subscribes to MQTT irrigation commands and controls relay-driven solenoid valves via GPIO.

## Why I built it

The irrigation-controller decides which zones to run and publishes relay states over MQTT. This service receives those states and physically opens and closes the solenoid valves. The mobile app and web app trigger irrigation runs, and this controller is the last link in the chain that makes water flow.

## How it fits

This runs on a dedicated Raspberry Pi Zero 2W wired to a 7-zone relay board. It subscribes to the same Mosquitto MQTT broker that all other services use.

- [home-server.infra](https://github.com/Buie-Dev/home-server.infra) runs the Mosquitto MQTT broker this controller subscribes to
- [irrigation-controller](https://github.com/Buie-Dev/irrigation-controller) publishes `irrigation/currentState` with zone relay states
- [devices.flow-sensor](https://github.com/Buie-Dev/devices.flow-sensor) publishes flow sensor pulse data to MQTT
- [home-server.api](https://github.com/Buie-Dev/home-server.api) is the Flask REST API
- [home-server.web](https://github.com/Buie-Dev/home-server.web) and [home-server.mobile](https://github.com/Buie-Dev/home-server.mobile) display zone states and trigger irrigation

## Stack

- Python 3.9 on Raspberry Pi Zero 2W
- RPi.GPIO for relay control (active LOW)
- paho-mqtt for MQTT subscription
- Docker Compose (privileged mode, host network)

## Running it

### Prerequisites

- Raspberry Pi Zero 2W with Docker installed
- 7-zone relay board wired to GPIO (see wiring table below)
- Network access to the MQTT broker

### First time setup

1. Clone the repo

```bash
git clone https://github.com/Buie-Dev/controllers.garden.git
cd controllers.garden
```

2. Create `.env` from the example and fill in your MQTT credentials

```bash
cp .env.example .env
```

3. Start the service

```bash
docker compose up -d
```

## Configuration

| Variable | Purpose |
|---|---|
| `MQTT_USERNAME` | MQTT broker username |
| `MQTT_PASSWORD` | MQTT broker password |
| `MQTT_BROKER` | MQTT broker IP address |
| `MQTT_PORT` | MQTT broker port (1883) |
| `DEVICE_NAME` | Device name used in health check responses |
| `ZONE` | Zone group ID this controller manages |
| `ENVIRONMENT` | Set to `raspberry_pi` for real GPIO, anything else for mock |

## Tests

There are no automated tests. This is a hardware project that controls GPIO relays. CI runs flake8 to lint the Python code.

To test GPIO manually on the Pi:

```bash
python3 test_gpio.py
```

To monitor GPIO state in real time:

```bash
python3 monitor_gpio.py
```

## Wiring

### GPIO Pin Mapping (BCM)

| Zone | GPIO |
|------|------|
| 1    | 2    |
| 2    | 3    |
| 3    | 4    |
| 4    | 22   |
| 5    | 27   |
| 6    | 18   |
| 7    | 10   |

Relays are **active LOW** — GPIO LOW = relay on, GPIO HIGH = relay off.

### Hardware

- 7-zone relay board (5V coil, switches 12V)
- 7 x 12V solenoid valves
- 12V power supply (5A minimum, 12A battery recommended)
- 12V to 5V buck converter (3A) for Pi and relay board

## MQTT topics

| Direction | Topic | Payload |
|---|---|---|
| Subscribe | `irrigation/currentState` | Zone array with id + state per subzone |
| Subscribe | `healthcheck/request` | Any message triggers a health response |
| Publish | `healthcheck/response` | `{ device: "<device_name>" }` |

## Fresh Pi setup

### 1. Disable WiFi power management

**This is the most important step.** The Pi Zero 2W's WiFi chip aggressively enters power-save mode, causing WiFi dropouts, slow SSH, and missed MQTT messages.

```bash
sudo nano /etc/NetworkManager/conf.d/wifi-power.conf
```

Add:

```ini
[connection]
wifi.powersave = 2
```

Restart and verify:

```bash
sudo systemctl restart NetworkManager
iwconfig wlan0 | grep "Power Management"
# Must show: Power Management:off
```

### 2. Keepalive ping

Some routers prune idle WiFi clients. Add a cron job:

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

## Power setup (off-grid battery)

- 12V 12Ah battery topped up by 30W solar panel via MPPT charge controller
- Daily consumption: ~7-8Ah (Pi + relays running 24/7)
- 30W panel generates ~10-12Ah/day — comfortable margin on sunny days, ~1.5 days reserve without sun
- Use MPPT controller, not PWM — meaningfully more harvest from a 30W panel
- Charging voltage reaches 13.6-14.4V — verify your 5V converter handles this input range

## Troubleshooting

**WiFi drops every ~10 minutes** — NetworkManager is re-enabling WiFi power save. See step 1 above.

**SSH is slow or laggy** — Same cause. Fix with the NetworkManager config above.

**Health checks not responding** — Fix WiFi power management first. Then check MQTT broker logs for disconnects and verify the container is running with `docker compose ps`.

**Relays not switching** — Confirm wiring matches the GPIO table above. Check that the service is running and receiving MQTT messages with `docker compose logs -f`.

## How I work on it

Changes start as specs in `docs/specs/`. Claude Code implements them on a branch and I review and merge every pull request.
