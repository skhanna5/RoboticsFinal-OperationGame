# RoboticsFinal-OperationGame

computermain.py: handles all image processing. uses mqtthandler.py (which uses paho.mqtt) to communicate with main.py

main.py: pico code to use image processing data to control motors. uses simple.py for mqtt processes with computermain.py

simple.py and mqtthandler.py: support libraries

