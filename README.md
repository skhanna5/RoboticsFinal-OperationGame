# RoboticsFinal-OperationGame

computermain.py: handles all image processing. uses mqtthandler.py (which uses paho.mqtt) to help with communication with main.py

main.py: pico code to use image processing data to control motors. uses simple.py for mqtt processes with computermain.py

simple.py and mqtthandler.py: support libraries. simple does MQTT for PICO while mqtthandler does MQTT stuff for the computer

