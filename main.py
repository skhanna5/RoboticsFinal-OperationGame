import network
from simple import MQTTClient
import shivsecrets
from time import sleep
import machine
from machine import Pin, PWM
import utime

# thanks for these classes Liam
class StepperMotor:
    def __init__(self, step_pin, dir_pin, delay=0.001):
        self.step_pin = machine.Pin(step_pin, machine.Pin.OUT)
        self.dir_pin = machine.Pin(dir_pin, machine.Pin.OUT)
        self.delay = delay
        self.last_coordinates = (0, 0)  # Initialize last_coordinates as a tuple (0, 0)

    def step(self, direction=1):
        self.dir_pin.value(direction)
        self.step_pin.on()
        utime.sleep_us(2)  # Ensure a minimum pulse width of 2 microseconds
        self.step_pin.off()
        utime.sleep(self.delay)

    def move_steps(self, steps, direction=1):
        for _ in range(steps):
            self.step(direction)

    def move_degrees(self, degrees, steps_per_rev, direction=1):
        steps = int(degrees / 360 * steps_per_rev)
        self.move_steps(steps, direction)

    def move(self, num_steps, direction=1):
        self.move_steps(num_steps, direction)

class ContinuousServo:
    def __init__(self, pin_number, freq=50, duty_us=1500):
        pin = Pin(pin_number)
        pwm = PWM(pin)
        pwm.freq(freq)
        self.pwm = pwm
        self.duty_us = duty_us

    def set_speed(self, speed):
        if speed < -100:
            speed = -100
        elif speed > 100:
            speed = 100

        duty_us = self.duty_us + speed * 5
        self.pwm.duty_ns(duty_us * 1000)

    def stop(self):
        self.pwm.duty_ns(self.duty_us * 1000)

    def deinit(self):
        self.pwm.deinit()

# Define WiFi credentials and MQTT broker details
ssid = shivsecrets.tufts_wifi
password = shivsecrets.tuft_wifi_password
broker = shivsecrets.secure_broker
topicsub = shivsecrets.mqtt_topic

# Define stepper and servo motors and gear ratio (steps/inch)
stepper = StepperMotor(step_pin=13, dir_pin=7)
stepperratio = 120 #169.49 #169.49 steps/inch
servo = ContinuousServo(pin_number=12)

def move_to_position(x):
    steps_to_move = int(x * stepperratio)

    # Move to the specified position
    stepper.move_steps(steps_to_move, direction=-1)
    print(f"Moved {steps_to_move} steps to position {x} inches")

    servo.set_speed(80)  # 100 means full speed forward
    sleep(1)
    # Move backward for 2 seconds
    servo.set_speed(-50)  # -100 means full speed backward
    sleep(1.7)
    # Stop the servo
    servo.stop()

    # Move back to the home position (same number of steps in the opposite direction)
    stepper.move_steps(steps_to_move, direction=0)
    print(f"Moved {steps_to_move} steps back to home")

# Connect to WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)
while wifi.isconnected() == False:
    print('Waiting for connection...')
    sleep(2)
print('Connected to WiFi')
sleep(1)

last_coordinates = None  # Global variable to store the last coordinates before "locked"

def whenCalled(topic, msg):
    global last_coordinates
    try:
        # If the message is "locked", handle it accordingly
        if msg.decode() == "locked":
            print("Target lock. Handling accordingly.")
            if last_coordinates is not None:
                x, y = last_coordinates
                move_to_position(x)
        else:
            # Decode message and extract coordinates
            coordinates = msg.decode().split(',')
            x = float(coordinates[0])
            y = float(coordinates[1])
            print(x, y)
            last_coordinates = (x, y)
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# Connect to MQTT broker
client = 'Shiv'
mqtt = MQTTClient(client, broker)
mqtt.set_callback(whenCalled)
print("Connecting to MQTT...")
mqtt.connect()
sleep(1)
print("MQTT Connection Successful!")
mqtt.subscribe(topicsub)

# Main
try:
    while True:
        mqtt.check_msg()
except KeyboardInterrupt:
    print('Interrupted')
    mqtt.disconnect()
