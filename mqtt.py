import json
import uuid

import paho.mqtt.client as mqtt
from RaspberryPi import RaspberryPi

from config import config

TOPIC_SUB_HEALTH_CHECK_REQUEST = "healthcheck/request"
TOPIC_SUB_CURRENT_STATE = "irrigation/currentState"

TOPIC_PUB_HEALTH_CHECK_RESPONSE = "healthcheck/response"  # Topic to publish to


sub_topics = [TOPIC_SUB_HEALTH_CHECK_REQUEST, TOPIC_SUB_CURRENT_STATE]
rp = RaspberryPi()
total_zones = 7


# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to broker!")
        for topic in sub_topics:
            client.subscribe(topic)  # Subscribe to a topic after connecting
    else:
        print(f"Connection failed with code {rc}")


def health_check_response(client):
    payload = {"device": config.DEVICE_NAME}
    client.publish(TOPIC_PUB_HEALTH_CHECK_RESPONSE, json.dumps(payload))


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

            for id in missing_ids:
                rp.set_relays(id, 0)

            for subzone in subzones:
                rp.set_relays(subzone["id"], subzone["state"])
    except json.JSONDecodeError:
        print(f"Received non-JSON message: {msg.payload.decode()} on topic {msg.topic}")


def create_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    return client


def run_mqtt():
    try:
        client = create_mqtt_client()
        print(f"Connecting to broker {config.MQTT_BROKER} on port {config.MQTT_PORT}")
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        client.loop_forever()
        return client

    finally:
        pass
