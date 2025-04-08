# File Name:         cu_main_UITest.py
# Contributors:      David Kunz
#                    Chris Sparano
# Last Contribution: 21:26; 4/7/25
# Purpose:           Fresh Air Senior Design Project
# Project Name:      Particulate Matter Detection and Alert System for 
#                    Citadel Civil Engineering Concrete and Asphalt Lab
#
# NOTES:
# Data from sensors via the ESP32 devices comes in the following format:
# {"SensorID":%s,"PM2.5 ug/m^3":%.1f,"PM10 ug/m^3":%.1f,"IAQI_PM2.5":%d,"IAQI_PM10":%d,"Overall_IAQI":%d}
#
# Values between ":" and "," characters will change
# depending on real time data

# Initialize libraries
import time
import paho.mqtt.client as paho
import sys
import RPi.GPIO as GPIO
from paho import mqtt
import json
import subprocess
import threading
import pygame
pygame.init()
import os
import threading

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

sensor_data_file = '/home/freshair/sensor_data.txt'
# Initialize variables
toggle = False
toggle_switch = 0
connection_status = False
new_data = False
user_input = False
sensor_id = ""
received = False
vent = False
data = {}
IAQ = 0 #UI Variable
IAQ_PM2 = 0
IAQ_PM10 = 0
IAQ_ovr = 0
prev_1 = ""
prev_2 = ""
prev_3 = ""
prev_4 = ""
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# Visual Alarm GPIO ports
GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)

# Sensor GPIO ports
GPIO.setup(8, GPIO.OUT)
GPIO.setup(10, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(29, GPIO.OUT)
GPIO.setup(31, GPIO.OUT)
GPIO.setup(33, GPIO.OUT)

toggle_switch = 0
sensor_1 = 0
sensor_2 = 0
sensor_3 = 0
sensor_4 = 0
sensor_list = [1, 1, 1, 1]
Moderate_Alarm = pygame.mixer.Sound('/home/freshair/Downloads/ModerateAlarm.wav')
Dangerous_Alarm = pygame.mixer.Sound('/home/freshair/Downloads/DangerousAlarm.wav')
# GPIO.setup(16,GPIO.OUT, initial = False)                  
# GPIO.setup(18,GPIO.OUT, initial = False)
GPIO.setup(37, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Need a new variable for sensor id


# Raw data from sensors comes in the following format:
# {"iaqi_pm2.5":12,"iaqi_pm10":2,"overall_iaqi":12}
# NOTE: Numeric values between ":" and "," characters will change
# depending on real time data
def alarm(IAQ, sensor_list):
    global toggle_switch
    print(toggle_switch)
    if (3 in sensor_list and toggle_switch == 0):
        GPIO.output(18, False)
        GPIO.output(16, True)
        Dangerous_Alarm.play()
    elif (2 in sensor_list and 3 not in sensor_list and toggle_switch == 0):
        GPIO.output(16, False)
        GPIO.output(18, True)
        Moderate_Alarm.play()
    elif (1 in sensor_list and 2 not in sensor_list and 3 not in sensor_list and toggle_switch == 0):
        GPIO.output(16, False)
        GPIO.output(18, False)
    elif toggle_switch == 1:
        GPIO.output(16, False)
        GPIO.output(18, False)
        
def sensor_designation(IAQ, sensor_id):
    sensor_id = int(sensor_id)
    IAQ = int(IAQ)
    global sensor_list
    if IAQ == 3:
        if sensor_id == 1:
            sensor_list[0] = IAQ
            GPIO.output(8, False)
            GPIO.output(10, False)
            GPIO.output(12, True)
        elif sensor_id == 2:
            sensor_list[1] = IAQ
            GPIO.output(11, False)
            GPIO.output(13, False)
            GPIO.output(15, True)
        elif sensor_id == 3:
            sensor_list[2] = IAQ
            GPIO.output(19, False)
            GPIO.output(21, False)
            GPIO.output(23, True)
        else:
            sensor_list[3] = IAQ
            GPIO.output(29, False)
            GPIO.output(31, False)
            GPIO.output(33, True)

    elif IAQ == 2:
        if sensor_id == 1:
            sensor_list[0] = IAQ
            GPIO.output(8, False)
            GPIO.output(10, True)
            GPIO.output(12, False)
        elif sensor_id == 2:
            sensor_list[1] = IAQ
            GPIO.output(11, False)
            GPIO.output(13, True)
            GPIO.output(15, False)
        elif sensor_id == 3:
            sensor_list[2] = IAQ
            GPIO.output(19, False)
            GPIO.output(21, True)
            GPIO.output(23, False)
        else:
            sensor_list[3] = IAQ
            GPIO.output(29, False)
            GPIO.output(31, True)
            GPIO.output(33, False)

            
    elif IAQ == 1:
        if sensor_id == 1:
            sensor_list[0] = IAQ
            GPIO.output(8, True)
            GPIO.output(10, False)
            GPIO.output(12, False)
        elif sensor_id == 2:
            sensor_list[1] = IAQ
            GPIO.output(11, True)
            GPIO.output(13, False)
            GPIO.output(15, False)
        elif sensor_id == 3:
            sensor_list[2] = IAQ
            GPIO.output(19, True)
            GPIO.output(21, False)
            GPIO.output(23, False)
        else:
            sensor_list[3] = IAQ
            GPIO.output(29, True)
            GPIO.output(31, False)
            GPIO.output(33, False)

def reset_toggle_switch():
    global toggle_switch
    toggle_switch = 0
    
def button_callback(channel):
    global toggle_switch
    print("toggle switch has been pressed")
    toggle_switch = 1
    print(toggle_switch)
    GPIO.output(18,False)
    GPIO.output(16, False)
    threading.Timer(60, reset_toggle_switch).start()
    
GPIO.remove_event_detect(37)
GPIO.add_event_detect(37,GPIO.FALLING,callback=button_callback, bouncetime=500) 
# Upon connection, print connection status and set global variable
def on_connect(client, userdata, flags, rc, properties=None):
    # THE FOLLOWING EXCERPT IS ADAPTED FROM AN AI GENERATED EXAMPLE:
    global connection_status
    if rc == 0:
        print("Successfully connected to the broker")
        connection_status = True
    else:
        print("Failed to connect, code %d" %rc)
        connection_status = False
    # END OF AI GENERATED CODE
    
# Upon published message, print confirmation
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))
    
# Upon subscription, print confirmation
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# Print message if data is received from sensor
def on_message(client, userdata, msg):
    global data
    global received
    global toggle
    global vent
    global sensor_id

            
    # If message from Ventilation, set equal to message value
    if "Status" in msg.topic:
        vent_payload = msg.payload.decode("utf-8").strip().lower()
    
        if vent_payload in ['true', '1', b'true', b'1','on','ON']:
            vent = True
        elif vent_payload in ['false', '0', b'false', b'0','off','OFF']:
            vent = False
        else:
            vent = False
        
        received = True
        
    # If message is from sensor, parse data 
    if "air_quality" in msg.topic:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        print("Received message: ", data)
        received = True
     
# MQTT Initialization
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
#client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS) # No need for TLS in the full product, only for testing in HIVEMQ
client.username_pw_set("freshair", "freshair")
client.connect("localhost", 1883)
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish
client.subscribe("ESP32/#", qos=0)
client.loop_start()

# Wait on broker connection
while connection_status == False:
    print("Waiting for connection...")
    time.sleep(1)

# Broker successfully connected
while connection_status == True:
    time.sleep(0.5)
    # If acknowledged, turn off sirens
#     while toggle == True:
#         GPIO.output(18, False)
#         time.sleep(0.5)
#         GPIO.output(16, False)
#         time.sleep(0.5)
#         print("Siren Status: OFF")
#         toggle = False

    # If data received
    while received == True:
        # Parse sensor data
        #GPIO.remove_event_detect(37)
        #GPIO.add_event_detect(37,GPIO.RISING,callback=button_callback, bouncetime=500) 
        sensor_id = data.get("SensorID", "0")  # Default to 'Unknown' if SensorID is missing
        #pm2_5 = data.get("PM2.5 ug/m^3", 0.0)  # Default to 0.0 if PM2.5 value is missing
        #pm10 = data.get("PM10 ug/m^3", 0.0)  # Default to 0.0 if PM10 value is missing
        IAQ_PM2 = data.get("IAQI_PM2.5", 0)  # Default to 0 if IAQI_PM2.5 is missing
        IAQ_PM10 = data.get("IAQI_PM10", 0)  # Default to 0 if IAQI_PM10 is missing
        IAQ_ovr = data.get("Overall_IAQI", 0)  # Default to 0 if Overall_IAQI is missing
#         print(f"Sensor ID: {sensor_id}")
#         print(f"PM2.5 (ug/m^3): {pm2_5}")
#         print(f"PM10 (ug/m^3): {pm10}")
#         print(f"IAQI PM2.5: {IAQ_PM2}")
#         print(f"IAQI PM10: {IAQ_PM10}")
#         print(f"Overall IAQI: {IAQ_ovr}")
        new_data = True
        
        # Handle ventilation status
        if IAQ_ovr >=200 and (prev_1 and prev_2 and prev_3 and prev_4) != "3":
            client.publish("ESP32/Relay", payload="ON", qos=0)
            vent = True
        elif IAQ_ovr <100 and (prev_1 and prev_2 and prev_3 and prev_4) != "1":
            client.publish("ESP32/Relay", payload="OFF", qos=0)
            vent = False
        else:
            pass
            
        if vent == True:
            client.publish("cu/vent", payload=True, qos=0)
            print("Ventilation Status: ON")
            received = False
        if vent == False:
            client.publish("cu/vent", payload=False, qos=0)
            print("Ventilation Status: OFF")
            received = False
    
    # If sensor data is parsed:   
    if new_data:
        time.sleep(0.5)
                
        # If over/equal to conditions below, "Dangerous" PM condition met (via OSHA 1910.1000)
        if IAQ_ovr >=200:
            #client.publish("ESP32/Relay", payload="ON", qos=0)
            time.sleep(0.5)
            IAQ = "3"
            sensor_designation(IAQ,sensor_id)
            #print(sensor_list)
            time.sleep(0.3)
            #IAQ += sensor_id
            #client.publish("cu/vent", payload=True, qos=0)
            print("Dangerous")
            time.sleep(0.5)
            alarm(IAQ, sensor_list)
            #subprocess.run(['python','/home/freshair/Documents/Testing_Codes/User_Interface/Testing_Plan_Main_Copy.py', IAQ, sensor_id] ,text=True, timeout=3)
            time.sleep(0.5)
            new_data = False
            
        # If under "Dangerous" threshold and over/equal to conditions below, "Unhealthy" PM condition met (via OSHA 1910.1000)
        elif IAQ_ovr >=100:
            #client.publish("cu/pm_status", payload="Unhealthy", qos=0)
            print("Unhealthy")
            time.sleep(0.3)
            IAQ = "2"
            #print(sensor_id)
            sensor_designation(IAQ,sensor_id)
            #IAQ += sensor_id
            time.sleep(0.5)
            alarm(IAQ, sensor_list)
            #subprocess.run(['python','/home/freshair/Documents/Testing_Codes/User_Interface/Testing_Plan_Main_Copy.py', IAQ, sensor_id] ,text=True, timeout=3)
            time.sleep(0.5)
            new_data = False
            
        # If below both conditions, "Healthy" PM condition met (via OSHA 1910.1000)
        else:
            #time.sleep(0.3)
            #client.publish("ESP32/Relay", "OFF", qos=0)
            time.sleep(0.3)
            IAQ = "1"
#             print(IAQ)
#             print(sensor_id)
#             print(sensor_list)
            sensor_designation(IAQ,sensor_id)
            time.sleep(0.3)
            print("Healthy")
            #IAQ += sensor_id
            time.sleep(0.5)
            alarm(IAQ, sensor_list)
            #subprocess.run(['python','/home/freshair/Documents/Testing_Codes/User_Interface/Testing_Plan_Main_Copy.py', IAQ, sensor_id] ,text=True, timeout=3)
            time.sleep(0.5)
            toggle = True
            new_data = False
    

reset_sensors()
GPIO.cleanup()
client.loop_stop()
sys.exit()
