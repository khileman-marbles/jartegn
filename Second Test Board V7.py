import board
import digitalio
import time

# --- Standby LED setup ---
standby_led = digitalio.DigitalInOut(board.D8)
standby_led.direction = digitalio.Direction.OUTPUT

# --- Standby Button (GPIO 7) ---
standby_button = digitalio.DigitalInOut(board.D7)
standby_button.direction = digitalio.Direction.INPUT
standby_button.pull = digitalio.Pull.UP

# --- Tube Control Button (GPIO 5) ---
tube_control_button = digitalio.DigitalInOut(board.D5)
tube_control_button.direction = digitalio.Direction.INPUT
tube_control_button.pull = digitalio.Pull.UP

# --- Volume Meter Control Button (GPIO 10) ---
vu_button = digitalio.DigitalInOut(board.D10)
vu_button.direction = digitalio.Direction.INPUT
vu_button.pull = digitalio.Pull.UP

# --- Tube Relays ---
tube1_relay = digitalio.DigitalInOut(board.D3)
tube1_relay.direction = digitalio.Direction.OUTPUT

tube2_relay = digitalio.DigitalInOut(board.D2)
tube2_relay.direction = digitalio.Direction.OUTPUT

# --- Tube Warm-up LEDs ---
tube1_led = digitalio.DigitalInOut(board.D4)
tube1_led.direction = digitalio.Direction.OUTPUT

tube2_led = digitalio.DigitalInOut(board.D6)
tube2_led.direction = digitalio.Direction.OUTPUT

# --- VU Meter Relay (GPIO 9) ---
vu_meter_relay = digitalio.DigitalInOut(board.D9)
vu_meter_relay.direction = digitalio.Direction.OUTPUT
vu_meter_relay_state = False
vu_meter_relay.value = False  # OFF by default

# --- Initial States ---
device_awake = False
tube_state = 0
prev_standby = True
prev_tube = True
prev_vu = True
debounce_delay = 0.2
last_input_time = 0

def blink_led(led, duration, interval=1.0):
    """ Blink the given LED on/off at interval for duration seconds """
    end_time = time.monotonic() + duration
    while time.monotonic() < end_time:
        led.value = True
        time.sleep(interval / 2)
        led.value = False
        time.sleep(interval / 2)

while True:
    now = time.monotonic()

    # --- Handle Standby Button ---
    current_standby = standby_button.value
    if prev_standby and not current_standby and (now - last_input_time > debounce_delay):
        device_awake = not device_awake
        standby_led.value = device_awake
        print("Device is now", "AWAKE" if device_awake else "STANDBY")

        if device_awake:
            # Wake: Activate both tubes & warm-up LEDs simultaneously
            tube_state = 0
            tube1_relay.value = True
            tube2_relay.value = True
            print("Waking up. Both tube relays ON. Starting simultaneous warm-up...")

            # Blink both warm-up LEDs together
            blink_start = time.monotonic()
            while time.monotonic() - blink_start < 10:
                tube1_led.value = True
                tube2_led.value = True
                time.sleep(0.5)
                tube1_led.value = False
                tube2_led.value = False
                time.sleep(0.5)

            tube1_led.value = True
            tube2_led.value = True
            print("Warm-up complete. Both tube LEDs ON.")

            # VU meter relay turns on now
            vu_meter_relay_state = True
            vu_meter_relay.value = True
            print("VU meter relay enabled after waking from standby.")

        else:
            # Standby: Turn off everything
            tube1_relay.value = False
            tube2_relay.value = False
            tube1_led.value = False
            tube2_led.value = False
            vu_meter_relay.value = False
            print("Entering standby. All relays and LEDs OFF.")

        last_input_time = now
    prev_standby = current_standby

    # --- Handle Tube Control Button ---
    current_tube = tube_control_button.value
    if prev_tube and not current_tube and device_awake and (now - last_input_time > debounce_delay):
        tube_state = (tube_state + 1) % 3

        if tube_state == 0:
            print("Tube State 0: Both tubes ON. Starting warm-up for Tube 1.")
            tube1_relay.value = True
            tube2_relay.value = True

            # Only blink Tube 1 LED, Tube 2 LED stays on
            tube2_led.value = True
            blink_led(tube1_led, 10)
            tube1_led.value = True
            print("Tube 1 warm-up complete.")

        elif tube_state == 1:
            print("Tube State 1: Tube 2 OFF.")
            tube2_relay.value = False
            tube2_led.value = False
            # Tube 1 stays ON, LED stays solid

        elif tube_state == 2:
            print("Tube State 2: Tube 1 OFF. Tube 2 ON with warm-up.")
            tube1_relay.value = False
            tube1_led.value = False
            tube2_relay.value = True
            blink_led(tube2_led, 10)
            tube2_led.value = True
            print("Tube 2 warm-up complete.")

        last_input_time = now
    prev_tube = current_tube

    # --- Handle VU Meter Button ---
    current_vu = vu_button.value
    if prev_vu and not current_vu and (now - last_input_time > debounce_delay):
        vu_meter_relay_state = not vu_meter_relay_state
        vu_meter_relay.value = vu_meter_relay_state
        print("VU Meter Relay", "ENABLED" if vu_meter_relay_state else "DISABLED")
        last_input_time = now
    prev_vu = current_vu
