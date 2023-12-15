import shivsecrets
import time
from time import sleep
import paho.mqtt.client as mqtt
import subprocess

# Import keys
mqtt_broker = shivsecrets.secure_broker
mqtt_topic = shivsecrets.mqtt_topic
mqtt_port = shivsecrets.mqtt_port
mqtt_client = mqtt.Client()

# Callback function when connecting to the MQTT broker
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    if str(rc) == '0':
        print('Success!')
    else:
        print('Error!')

def initializemqtt():
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)
    mqtt_client.loop_start()  # Start the MQTT client loop in the background

def startmqtt():
    command = '/opt/homebrew/opt/mosquitto/sbin/mosquitto -c /opt/homebrew/etc/mosquitto/mosquitto.conf'
    subprocess.Popen(command, shell=True)

def stopmqtt():
    command = 'pkill mosquitto'
    subprocess.run(command, shell=True)

# # Global variable to store the last published centroid
# last_centroid = None

# # Function to publish coordinates to MQTT only if significantly different
# def publish(cx, cy):
#     global last_centroid
#     # Set a threshold for significant difference
#     threshold = 30
#     # Run conversion
#     IN_TO_PIXEL = 37/1280
#     cx2 = round(cx*IN_TO_PIXEL, 2)
#     cy2 = round(cy*IN_TO_PIXEL, 2)
#     # Post
#     if last_centroid is None or abs(cx - last_centroid[0]) > threshold or abs(cy - last_centroid[1]) > threshold:
#         payload = f"{cx2},{cy2}"
#         mqtt_client.publish(mqtt_topic, payload)
#         last_centroid = (cx, cy)


# # Global variable to store the last published centroid and timestamp
# last_centroid = None
# last_publish_time = None

# # Function to publish coordinates to MQTT only if significantly different
# def publish(cx, cy):
#     global last_centroid, last_publish_time
#     # Set a threshold for significant difference
#     threshold = 30
#     # Set the time threshold for "locked" state (in seconds)
#     time_threshold = 5

#     # Run conversion
#     IN_TO_PIXEL = 37/1280
#     cx2 = round(cx*IN_TO_PIXEL, 2)
#     cy2 = round(cy*IN_TO_PIXEL, 2)

#     # Check if the centroid has moved significantly
#     if last_centroid is None or abs(cx - last_centroid[0]) > threshold or abs(cy - last_centroid[1]) > threshold:
#         payload = f"{cx2},{cy2}"
#         mqtt_client.publish(mqtt_topic, payload)
#         last_centroid = (cx, cy)
#         last_publish_time = time.time()
#     else:
#         # Check if the time threshold for "locked" state has been reached
#         if last_publish_time is not None and time.time() - last_publish_time >= time_threshold:
#             mqtt_client.publish(mqtt_topic, "locked")

# Global variable to store the last published centroid and timestamp
last_distance = None
last_publish_time = None
locked_published = False  # Flag to track if "locked" has been published

# # Function to publish distance between centroids to MQTT only if significantly different
# def publish(distance_x, distance_y):
#     global last_distance, last_publish_time, locked_published
#     # Set a threshold for significant difference
#     threshold = 10
#     # Set the time threshold for "locked" state (in seconds)
#     time_threshold = 5

#     # Run conversion if needed
#     # Example conversion factor (adjust according to your requirements)
#     PIXEL_TO_IN = 1280 / 18.125
#     distance_x_inches = round(distance_x / PIXEL_TO_IN, 2)
#     distance_y_inches = round(distance_y / PIXEL_TO_IN, 2)

#     # Check if the distance has changed significantly
#     if last_distance is None or abs(distance_x - last_distance[0]) > threshold or abs(distance_y - last_distance[1]) > threshold:
#         payload = f"{distance_x_inches},{distance_y_inches}"
#         mqtt_client.publish(mqtt_topic, payload)
#         last_distance = (distance_x, distance_y)
#         last_publish_time = time.time()
#         locked_published = False  # Reset the flag when significant movement occurs
#     else:
#         # Check if the time threshold for "locked" state has been reached
#         if last_publish_time is not None and time.time() - last_publish_time >= time_threshold and not locked_published:
#             mqtt_client.publish(mqtt_topic, "locked")
#             locked_published = True  # Set the flag to True after "locked" is published

# Global variable to store the last published centroid and timestamp
last_distance = None
last_publish_time = None
locked_published = False  # Flag to track if "locked" has been published

# Function to publish distance between centroids to MQTT only if significantly different
def publish(distance_x, distance_y):
    global last_distance, last_publish_time, locked_published
    # Set a threshold for significant difference
    threshold = 10
    # Set the time threshold for "locked" state (in seconds)
    time_threshold = 5

    # Run conversion if needed
    # Example conversion factor (adjust according to your requirements)
    PIXEL_TO_IN = 1280 / 18.125
    distance_x_inches = round(distance_x / PIXEL_TO_IN, 2)
    distance_y_inches = round(distance_y / PIXEL_TO_IN, 2)

    # Check if "locked" has been published
    if locked_published:
        return

    # Check if the distance has changed significantly
    if last_distance is None or abs(distance_x - last_distance[0]) > threshold or abs(distance_y - last_distance[1]) > threshold:
        payload = f"{distance_x_inches},{distance_y_inches}"
        mqtt_client.publish(mqtt_topic, payload)
        last_distance = (distance_x, distance_y)
        last_publish_time = time.time()
        locked_published = False  # Reset the flag when significant movement occurs
    else:
        # Check if the time threshold for "locked" state has been reached
        if last_publish_time is not None and time.time() - last_publish_time >= time_threshold and not locked_published:
            mqtt_client.publish(mqtt_topic, "locked")
            locked_published = True  # Set the flag to True after "locked" is published

