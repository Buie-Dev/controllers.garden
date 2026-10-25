import json
import time
import threading

import paho.mqtt.client as mqtt
from RaspberryPi import RaspberryPi

from config import config

TOPIC_SUB_HEALTH_CHECK_REQUEST = "healthcheck/request"
TOPIC_SUB_CURRENT_STATE = "irrigation/currentState"

TOPIC_PUB_HEALTH_CHECK_RESPONSE = "healthcheck/response"  # Topic to publish to


sub_topics = [TOPIC_SUB_HEALTH_CHECK_REQUEST, TOPIC_SUB_CURRENT_STATE]
rp = RaspberryPi()
total_zones = 7

# Global variables for monitoring
last_gpio_activity = time.time()
gpio_health_check_interval = 300  # 5 minutes


# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to broker!")
        for topic in sub_topics:
            client.subscribe(topic)  # Subscribe to a topic after connecting
        # Start GPIO health monitoring
        start_gpio_monitoring()
    else:
        print(f"Connection failed with code {rc}")


def health_check_response(client):
    payload = {"device": config.DEVICE_NAME}
    client.publish(TOPIC_PUB_HEALTH_CHECK_RESPONSE, json.dumps(payload))


def start_gpio_monitoring():
    """Start a background thread to monitor GPIO health"""

    def monitor_gpio():
        while True:
            try:
                time.sleep(gpio_health_check_interval)
                check_gpio_health()
            except Exception as e:
                print(f"Error in GPIO monitoring: {e}")

    monitor_thread = threading.Thread(target=monitor_gpio, daemon=True)
    monitor_thread.start()
    print("GPIO monitoring started")


def check_gpio_health():
    """Periodically check GPIO health and reset if needed"""
    global last_gpio_activity

    current_time = time.time()
    time_since_activity = current_time - last_gpio_activity

    if time_since_activity > gpio_health_check_interval:
        print("Performing periodic GPIO health check...")
        try:
            # Get current pin status
            pin_status = rp.get_pin_status()
            print(f"Current GPIO status: {pin_status}")

            # Commented out: this was resetting all relays after 10 min of no messages
            # but main controller only sends on state change, so long timers (hours)
            # would always get killed mid-run
            # if time_since_activity > 600:  # 10 minutes
            #     print(
            #         "No GPIO activity for 10+ minutes, performing preventive reset..."
            #     )
            #     rp._reset_gpio()

        except Exception as e:
            print(f"Error during GPIO health check: {e}")


def update_gpio_activity():
    """Update the timestamp of last GPIO activity"""
    global last_gpio_activity
    last_gpio_activity = time.time()


# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    # print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    try:
        print(msg.topic, msg.payload)

        if msg.topic == TOPIC_SUB_HEALTH_CHECK_REQUEST:
            health_check_response(client)
        elif msg.topic == TOPIC_SUB_CURRENT_STATE:
            payload = json.loads(msg.payload.decode())
            zone = next((z for z in payload if z["id"] == config.ZONE), None)
            if zone is None:
                return

            subzones = zone["subzones"]
            print(subzones)

            # Turn off missing zones
            existing_ids = {zone["id"] for zone in subzones}
            missing_ids = [i for i in range(1, 8) if i not in existing_ids]

            success_count = 0
            for id in missing_ids:
                if rp.set_relays(id, 0):
                    success_count += 1
                else:
                    print(f"Failed to turn off zone {id}")

            for subzone in subzones:
                if rp.set_relays(subzone["id"], subzone["state"]):
                    success_count += 1
                    update_gpio_activity()  # Update activity timestamp
                else:
                    print(f"Failed to set zone {subzone['id']} to {subzone['state']}")

            print(
                f"Successfully processed {success_count}/{len(subzones) + len(missing_ids)} zone operations"
            )

            # If we had failures, log the current GPIO status
            if success_count < len(subzones) + len(missing_ids):
                print("Some operations failed, checking GPIO status...")
                pin_status = rp.get_pin_status()
                print(f"GPIO status after failures: {pin_status}")

    except json.JSONDecodeError:
        print(f"Received non-JSON message: {msg.payload.decode()} on topic {msg.topic}")
    except Exception as e:
        print(f"Error processing message: {e}")
        # Commented out: resetting all relays on any message error was too aggressive
        # and could kill active irrigation runs unexpectedly
        # try:
        #     print("Attempting GPIO reset due to error...")
        #     rp._reset_gpio()
        # except Exception as reset_error:
        #     print(f"Failed to reset GPIO: {reset_error}")


def create_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    return client


def run_mqtt():
    client = create_mqtt_client()
    while True:
        try:
            print(f"Connecting to broker {config.MQTT_BROKER}:{config.MQTT_PORT}...")
            client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
            break
        except Exception as e:
            print(f"MQTT connect failed: {e} — retrying in 5s")
            time.sleep(5)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        rp.cleanup()
    except Exception as e:
        print(f"Error in MQTT client: {e}")
        rp.cleanup()
