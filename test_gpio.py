#!/usr/bin/env python3
"""
GPIO Test Script for Raspberry Pi Garden Controller
Use this script to test GPIO functionality and debug issues
"""

import time
import sys
from RaspberryPi import RaspberryPi


def test_gpio_basic():
    """Test basic GPIO functionality"""
    print("=== Testing Basic GPIO Functionality ===")
    rp = RaspberryPi()

    # Test pin status
    print("Current pin status:")
    status = rp.get_pin_status()
    for pin, state in status.items():
        print(f"  {pin}: {state}")

    # Test turning all off
    print("\nTesting turn_all_off...")
    rp.turn_all_off()
    time.sleep(1)

    # Test individual zones
    for zone in range(1, 8):
        print(f"\nTesting zone {zone}...")

        # Turn on
        print(f"  Turning ON zone {zone}")
        success = rp.turn_on_relay(zone)
        print(f"  Result: {'SUCCESS' if success else 'FAILED'}")
        time.sleep(2)

        # Turn off
        print(f"  Turning OFF zone {zone}")
        success = rp.turn_off_relay(zone)
        print(f"  Result: {'SUCCESS' if success else 'FAILED'}")
        time.sleep(1)

    # Test set_relays method
    print("\n=== Testing set_relays method ===")
    for zone in range(1, 8):
        print(f"Testing zone {zone} with set_relays...")

        # Turn on
        success = rp.set_relays(zone, 1)
        print(f"  ON: {'SUCCESS' if success else 'FAILED'}")
        time.sleep(1)

        # Turn off
        success = rp.set_relays(zone, 0)
        print(f"  OFF: {'SUCCESS' if success else 'FAILED'}")
        time.sleep(1)

    # Final status
    print("\nFinal pin status:")
    status = rp.get_pin_status()
    for pin, state in status.items():
        print(f"  {pin}: {state}")

    rp.cleanup()
    print("\nTest completed!")


def test_gpio_stress():
    """Test GPIO under stress conditions"""
    print("=== Testing GPIO Under Stress ===")
    rp = RaspberryPi()

    try:
        for cycle in range(10):
            print(f"Stress test cycle {cycle + 1}/10")

            # Rapidly switch zones
            for zone in range(1, 8):
                rp.set_relays(zone, 1)
                time.sleep(0.1)
                rp.set_relays(zone, 0)
                time.sleep(0.1)

            # Check status every few cycles
            if (cycle + 1) % 3 == 0:
                status = rp.get_pin_status()
                print(f"  Status after cycle {cycle + 1}: {status}")

        print("Stress test completed!")

    except Exception as e:
        print(f"Error during stress test: {e}")
        rp._reset_gpio()

    rp.cleanup()


def test_gpio_reset():
    """Test GPIO reset functionality"""
    print("=== Testing GPIO Reset Functionality ===")
    rp = RaspberryPi()

    # Turn on a few zones
    print("Turning on zones 1, 3, 5...")
    rp.set_relays(1, 1)
    rp.set_relays(3, 1)
    rp.set_relays(5, 1)
    time.sleep(1)

    print("Status before reset:")
    status = rp.get_pin_status()
    for pin, state in status.items():
        print(f"  {pin}: {state}")

    # Test reset
    print("\nTesting GPIO reset...")
    rp._reset_gpio()

    print("Status after reset:")
    status = rp.get_pin_status()
    for pin, state in status.items():
        print(f"  {pin}: {state}")

    rp.cleanup()
    print("Reset test completed!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "stress":
            test_gpio_stress()
        elif test_type == "reset":
            test_gpio_reset()
        else:
            print("Unknown test type. Use: basic, stress, or reset")
    else:
        test_gpio_basic()
