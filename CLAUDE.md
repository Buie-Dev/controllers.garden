# CLAUDE.md

## What this repo is

Python service for a Raspberry Pi Zero 2W that subscribes to MQTT irrigation commands and controls 7 relay-driven solenoid valves via GPIO. The irrigation-controller publishes zone states; this service sets the physical relays accordingly. Responds to MQTT health checks so the mobile and web apps can confirm the device is online.

## Related repos

- [home-server.infra](https://github.com/Buie-Dev/home-server.infra) — Docker Compose infrastructure, runs the Mosquitto MQTT broker this controller subscribes to
- [irrigation-controller](https://github.com/Buie-Dev/irrigation-controller) — Raspberry Pi service that publishes `irrigation/currentState` with zone relay states
- [devices.flow-sensor](https://github.com/Buie-Dev/devices.flow-sensor) — ESP32 flow sensor that publishes pulse counts to MQTT
- [home-server.api](https://github.com/Buie-Dev/home-server.api) — Flask REST API
- [home-server.web](https://github.com/Buie-Dev/home-server.web) — React web app
- [home-server.mobile](https://github.com/Buie-Dev/home-server.mobile) — React Native mobile app

## Stack

- Python 3.9 on Raspberry Pi Zero 2W
- RPi.GPIO for relay control (active LOW)
- paho-mqtt for MQTT subscription
- Docker Compose (privileged mode, host network)

## Commands

```bash
docker compose up -d       # Start the service
docker compose logs -f     # Tail logs
docker compose down        # Stop the service
```

## File layout

```
index.py              # Entry point — signal handlers, starts MQTT client
mqtt.py               # MQTT subscriber — handles currentState and healthcheck topics
RaspberryPi.py        # GPIO control class — relay on/off, reset, health monitoring
config.py             # Config class reading from environment variables
docker-compose.yaml   # Single service, privileged, host network, .env file
Dockerfile            # Python 3.9 base, installs requirements
monitor_gpio.py       # Standalone GPIO monitoring script
test_gpio.py          # Manual GPIO test script (basic, stress, reset tests)
requirements.txt      # paho-mqtt, python-dotenv, uuid, certifi
requirements_pi.txt   # RPi.GPIO
.env                  # Credentials and config (gitignored)
.env.example          # Template for .env
```

## GPIO pin mapping (BCM)

| Zone | GPIO |
|------|------|
| 1    | 2    |
| 2    | 3    |
| 3    | 4    |
| 4    | 22   |
| 5    | 27   |
| 6    | 18   |
| 7    | 10   |

Relays are active LOW — GPIO LOW = relay on, GPIO HIGH = relay off.

## MQTT topics

| Direction | Topic | Payload |
|---|---|---|
| Subscribe | `irrigation/currentState` | Zone array with id + state per subzone |
| Subscribe | `healthcheck/request` | Any message triggers a health response |
| Publish | `healthcheck/response` | `{ device: DEVICE_NAME }` |

## Standards

- Two long-lived branches: `main` (stable) and `dev` (ongoing work)
- Spec branches named `spec/NNN-short-name`, branched from `dev`, merged back to `dev`
- Commit messages: imperative, sentence case, no AI attribution
- `.gitignore` covers `.env`, `config.py`, `__pycache__/`
- `.env.example` lists every variable with placeholder values
- No license file

## Boundaries

- Never push. Give commands and wait for confirmation.
- Never change app behavior unless a spec says to.
- Never commit `.env`, real IPs, or credentials.
- Never merge a pull request. I review and merge.
- Only write things that are true in the code.

## Workflow

Changes start as specs in `docs/specs/`. Claude Code implements them on a spec branch, and I review and merge every pull request.
