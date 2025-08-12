#!/usr/bin/env python3
"""
GPIO Monitoring Script for Raspberry Pi Garden Controller
Run this alongside your main application to monitor GPIO health
"""

import time
import signal
import sys
from RaspberryPi import RaspberryPi


class GPIOMonitor:
    def __init__(self):
        self.rp = RaspberryPi()
        self.running = True
        self.monitor_interval = 30  # Check every 30 seconds
        self.last_activity = time.time()

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        print("\nReceived shutdown signal, cleaning up...")
        self.running = False
        self.rp.cleanup()
        sys.exit(0)

    def check_gpio_health(self):
        """Check the health of all GPIO pins"""
        try:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking GPIO health...")

            # Get current pin status
            status = self.rp.get_pin_status()

            # Check for any error states
            errors = []
            for pin, state in status.items():
                if "ERROR" in str(state):
                    errors.append(f"{pin}: {state}")

            if errors:
                print(f"  ⚠️  GPIO errors detected: {errors}")
                print("  🔄 Attempting GPIO reset...")
                self.rp._reset_gpio()

                # Check status after reset
                time.sleep(1)
                new_status = self.rp.get_pin_status()
                print(f"  📊 Status after reset: {new_status}")
            else:
                print(f"  ✅ All GPIO pins healthy: {status}")

            # Check if we need a preventive reset
            current_time = time.time()
            time_since_activity = current_time - self.last_activity

            if time_since_activity > 600:  # 10 minutes
                print(
                    "  ⏰ No activity for 10+ minutes, performing preventive reset..."
                )
                self.rp._reset_gpio()
                self.last_activity = current_time

        except Exception as e:
            print(f"  ❌ Error during health check: {e}")
            try:
                print("  🔄 Attempting GPIO reset due to error...")
                self.rp._reset_gpio()
            except Exception as reset_error:
                print(f"  ❌ Failed to reset GPIO: {reset_error}")

    def run(self):
        """Main monitoring loop"""
        print("GPIO Monitor started. Press Ctrl+C to stop.")
        print(f"Monitoring interval: {self.monitor_interval} seconds")

        while self.running:
            try:
                self.check_gpio_health()
                time.sleep(self.monitor_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Unexpected error in monitor loop: {e}")
                time.sleep(5)  # Wait a bit before retrying

        print("GPIO Monitor stopped.")


if __name__ == "__main__":
    monitor = GPIOMonitor()
    monitor.run()
