import signal
import sys

from mqtt import run_mqtt, rp


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print("\nReceived shutdown signal, cleaning up...")
    try:
        rp.cleanup()
    except Exception as e:
        print(f"Error during cleanup: {e}")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Running --------")
    try:
        mqtt_client = run_mqtt()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        rp.cleanup()
    except Exception as e:
        print(f"Unexpected error: {e}")
        rp.cleanup()
        sys.exit(1)
