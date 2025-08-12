from typing import Optional
import time
from config import config

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    print(config.IS_RASPBERRYPI)
    print("Running on non-Raspberry Pi hardware. Using mock GPIO library.")


class RaspberryPi:
    pin_numbers = [2, 3, 4, 17, 27, 18, 10]

    def __init__(self):
        if config.IS_RASPBERRYPI:
            try:
                GPIO.setmode(GPIO.BCM)  # Use BCM numbering
                GPIO.setwarnings(False)  # Disable warnings to reduce noise
                for pin in self.pin_numbers:
                    GPIO.setup(pin, GPIO.OUT)  # Set all as output
                    GPIO.output(pin, GPIO.HIGH)
                print("GPIO initialized successfully")
            except Exception as e:
                print(f"Error initializing GPIO: {e}")
                self._reset_gpio()

    def _reset_gpio(self):
        """Reset GPIO to a known good state"""
        if config.IS_RASPBERRYPI:
            try:
                GPIO.cleanup()
                time.sleep(0.1)  # Small delay to ensure cleanup
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                for pin in self.pin_numbers:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.HIGH)
                print("GPIO reset completed")
            except Exception as e:
                print(f"Error resetting GPIO: {e}")

    def _safe_gpio_output(self, pin, state):
        """Safely set GPIO output with error handling"""
        if not config.IS_RASPBERRYPI:
            return True

        try:
            GPIO.output(pin, state)
            # Verify the pin was set correctly
            time.sleep(0.002)
            actual_state = GPIO.input(pin)
            if actual_state != state:
                print(
                    f"Warning: Pin {pin} state mismatch. Expected: {state}, Got: {actual_state}"
                )
                return False
            return True
        except Exception as e:
            print(f"Error setting GPIO pin {pin} to {state}: {e}")
            return False

    def turn_all_off(self):
        self.active_zone = None
        print("TURNING OFF ALL RELAY")
        success = True
        for pin in self.pin_numbers:
            if config.IS_RASPBERRYPI:
                if not self._safe_gpio_output(pin, GPIO.HIGH):
                    success = False
            else:
                print(f"TURNING OFF PIN {pin}")

        if not success and config.IS_RASPBERRYPI:
            print("Some pins failed to turn off, attempting GPIO reset...")
            self._reset_gpio()

    def turn_on_relay(self, zone: int):
        if zone < 1 or zone > 7:
            print(f"Invalid zone: {zone}")
            return False

        self.turn_all_off()
        pin_number = self.pin_numbers[zone - 1]

        if config.IS_RASPBERRYPI:
            success = self._safe_gpio_output(pin_number, GPIO.LOW)
            if success:
                print(f"Successfully turned ON zone {zone}")
            else:
                print(f"Failed to turn ON zone {zone}, attempting GPIO reset...")
                self._reset_gpio()
                # Try one more time after reset
                success = self._safe_gpio_output(pin_number, GPIO.LOW)
            return success
        else:
            print(f"TURNING ON ZONE {zone}: GPIO {pin_number}")
            return True

    def turn_off_relay(self, zone: int):
        if zone < 1 or zone > 7:
            print(f"Invalid zone: {zone}")
            return False

        pin_number = self.pin_numbers[zone - 1]

        if config.IS_RASPBERRYPI:
            print("TURNING OFF RELAY")
            success = self._safe_gpio_output(pin_number, GPIO.HIGH)
            if not success:
                print(f"Failed to turn OFF zone {zone}, attempting GPIO reset...")
                self._reset_gpio()
                success = self._safe_gpio_output(pin_number, GPIO.HIGH)
            return success
        else:
            print(f"TURNING OFF ZONE {zone}: GPIO {pin_number}")
            return True

    def set_relays(self, zone, state):
        if zone > 7 or zone < 1:
            print("Zone Out OF Range")
            return False

        pin_number = self.pin_numbers[zone - 1]

        if config.IS_RASPBERRYPI:
            print(f"SETTING ZONE {zone}: GPIO {pin_number} TO {state}")
            gpio_state = GPIO.HIGH if state == 0 else GPIO.LOW
            success = self._safe_gpio_output(pin_number, gpio_state)

            if not success:
                print(f"Failed to set zone {zone} to {state}, attempting GPIO reset...")
                self._reset_gpio()
                # Try one more time after reset
                success = self._safe_gpio_output(pin_number, gpio_state)

            if success:
                print(f"Successfully set zone {zone} to {state}")
            else:
                print(f"Failed to set zone {zone} to {state} even after reset")

            return success
        else:
            print(f"SETTING ZONE {zone}: GPIO {pin_number} TO {state}")
            return True

    def get_pin_status(self):
        """Get the current status of all pins for debugging"""
        if not config.IS_RASPBERRYPI:
            return {}

        status = {}
        for i, pin in enumerate(self.pin_numbers):
            try:
                state = GPIO.input(pin)
                status[f"zone_{i+1}_pin_{pin}"] = "HIGH" if state else "LOW"
            except Exception as e:
                status[f"zone_{i+1}_pin_{pin}"] = f"ERROR: {e}"
        return status

    def cleanup(self):
        """Clean up GPIO on shutdown"""
        if config.IS_RASPBERRYPI:
            try:
                GPIO.cleanup()
                print("GPIO cleanup completed")
            except Exception as e:
                print(f"Error during GPIO cleanup: {e}")
