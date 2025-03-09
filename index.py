import threading
import time

from mqtt import run_mqtt

if __name__ == "__main__":
    print("Running --------")
    mqtt_client = run_mqtt()
