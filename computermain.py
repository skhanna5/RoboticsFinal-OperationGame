import cv2 # Library for image processing
import imutils # Library for feed resizing
from time import sleep
from mqtthandler import publish, initializemqtt, startmqtt, stopmqtt # Library to publish coordinates using MQTT
import shivsecrets # Library for my keys

# Collection of command line tools to test MQTT
def failsafe():
    nothing = 'here'
    # command line tools in case
    # /opt/homebrew/opt/mosquitto/sbin/mosquitto -c /opt/homebrew/etc/mosquitto/mosquitto.conf
    # mosquitto_sub -t 'ShivFinal' -h 10.243.51.89 -p 1883 
    # mosquitto_pub -t "ShivFinal" -h 10.0.0.109 -p 1883 -m "hi there”

# Function to find the center and highlight the largest red object in the frame 
def reddetection(frame):
    global cx2, cy2
    # Create a copy of the frame to avoid modifying the original
    frame_copy = frame.copy()

    b, g, r = cv2.split(frame_copy)
    red = cv2.subtract(r, g)
    # Blur the red channel image
    blurred = cv2.GaussianBlur(red, (5, 5), 0)
    # Threshold the blurred image
    thresh = cv2.threshold(blurred, 125, 255, cv2.THRESH_BINARY)[1]
    # Find contours in the thresholded image
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Find the largest contour (if any)
    largest_contour = max(cnts, key=cv2.contourArea, default=None)
    if largest_contour is not None:
        # Highlight the largest contour
        cv2.drawContours(frame, [largest_contour], -1, (255, 0, 0), 2)
        # Compute the center of the largest contour
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            return cx, cy
    return None

def bluedetection(frame):
    global cx2, cy2
    # Create a copy of the frame to avoid modifying the original
    frame_copy = frame.copy()

    b, g, r = cv2.split(frame_copy)
    blue = cv2.subtract(b, r)
    blurred = cv2.GaussianBlur(blue, (5, 5), 0)
    thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY)[1]
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(cnts, key=cv2.contourArea, default=None)
    if largest_contour is not None:
        cv2.drawContours(frame, [largest_contour], -1, (0, 0, 255), 2)
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            return cx, cy
    return None

def greendetection(frame):
    global cx2, cy2
    # Create a copy of the frame to avoid modifying the original
    frame_copy = frame.copy()

    b, g, r = cv2.split(frame_copy)
    green = cv2.subtract(g, r)
    blurred = cv2.GaussianBlur(green, (5, 5), 0)
    thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY)[1]
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(cnts, key=cv2.contourArea, default=None)
    if largest_contour is not None:
        cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            return cx, cy
    return None

# Main script to create live video feed and publish to MQTT
def capture(url):
    try:
        cap = cv2.VideoCapture(url)
        while True:
            ret, frame = cap.read()
            if not ret:
                print('Error reading frame from video capture.')
                break

            # Resize video
            frame = imutils.resize(frame, width=1280, height=960)
            frame = imutils.rotate(frame, angle=0)

            # Detect blue and green centroids
            green_center = greendetection(frame)
            blue_center = bluedetection(frame)

            # Draw faint grid lines
            grid_spacing = 150
            grid_color = (100, 100, 100)
            for i in range(0, frame.shape[1], grid_spacing):
                cv2.line(frame, (i, 0), (i, frame.shape[0]), grid_color, 1)
            for j in range(0, frame.shape[0], grid_spacing):
                cv2.line(frame, (0, j), (frame.shape[1], j), grid_color, 1)

            # Live data box
            cv2.rectangle(frame, (5, 5), (410, 95), (255, 0, 255), 8)
            cv2.putText(frame, 'Centroid Distance [IN.]:', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 6)

            if blue_center is not None and green_center is not None:
                blue_cx, blue_cy = blue_center
                green_cx, green_cy = green_center

                # Draw circles and text on the frame for blue object
                cv2.circle(frame, blue_center, 10, (0, 0, 255), -1)
                cv2.putText(frame, 'Blue Center', (blue_center[0] - 20, blue_center[1] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 6)
                
                # Draw circles and text on the frame for green object
                cv2.circle(frame, green_center, 10, (0, 0, 255), -1)
                cv2.putText(frame, 'Green Center', (green_center[0] - 20, green_center[1] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 6)

                # Calculate the distance between centroids
                distance_x = abs(blue_cx - green_cx)
                distance_y = abs(blue_cy - green_cy)

                # Run conversion
                PIXEL_TO_IN = 1280 / 18.125
                distance_x_inches = round(distance_x / PIXEL_TO_IN, 2)
                distance_y_inches = round(distance_y / PIXEL_TO_IN, 2)

                # Publish the distance to MQTT topic
                publish(distance_x, distance_y)

                # Add to data box
                cv2.putText(frame, f'({distance_x_inches}, {distance_y_inches})', (20, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 6)

            cv2.imshow("Shiv's iPhone Live Video", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print('-----------------------------------------------')
        print("...Stopping video capture")
        cap.release()
        cv2.destroyAllWindows()

# Run [Pass in the correct droid key of the video camera, remember to adjust MQTT broker key as well]
try:
# Output formatting 
    print("Welcome to the Final Exam by Shiv and Jackson. Let's begin!")
    sleep(1)
    print("Starting MQTT broker...")
    print('-----------------------------------------------')
    startmqtt()
    sleep(2) 
    print('-----------------------------------------------')
    print("Initializing MQTT connection...")
    print('-----------------------------------------------')
    initializemqtt()
    sleep(2)
    print('-----------------------------------------------')
    print("Starting video capture")
    capture(shivsecrets.droid_secureurl)
finally:
# Output formatting
    print('-----------------------------------------------')
    print("...Stopping MQTT")
    print('-----------------------------------------------')
    stopmqtt()  # Stop MQTT broker when closing the program
    print('Have a good day!')
