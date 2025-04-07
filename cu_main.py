# File Name:         cu_main.py
# Contributors:      David Kunz
#                    Chris Sparano
# Last Contribution: 15:00; 4/7/25
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
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

sensor_data_file = '/home/freshair/sensor_data.txt'

# Initialize variables and GPIO
toggle = False
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
GPIO.setup(37, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def reset_sensors():
    # Erase the sensor_id file if it exists
    if os.path.exists(sensor_data_file):
        os.remove(sensor_data_file)
        print(f"{sensor_data_file} has been erased.")

    # Initialize sensor values to 1
    global sensor_1, sensor_2, sensor_3, sensor_4
    sensor_1 = 1
    sensor_2 = 1
    sensor_3 = 1
    sensor_4 = 1
    print("All sensor values initialized to 1.")

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
        sensor_id = data.get("SensorID", "Unknown")  # Default to 'Unknown' if SensorID is missing
        #pm2_5 = data.get("PM2.5 ug/m^3", 0.0)  # Default to 0.0 if PM2.5 value is missing
        #pm10 = data.get("PM10 ug/m^3", 0.0)  # Default to 0.0 if PM10 value is missing
        IAQ_PM2 = data.get("IAQI_PM2.5", 0)  # Default to 0 if IAQI_PM2.5 is missing
        IAQ_PM10 = data.get("IAQI_PM10", 0)  # Default to 0 if IAQI_PM10 is missing
        IAQ_ovr = data.get("Overall_IAQI", 0)  # Default to 0 if Overall_IAQI is missing
        print(f"Sensor ID: {sensor_id}")
#         print(f"PM2.5 (ug/m^3): {pm2_5}")
#         print(f"PM10 (ug/m^3): {pm10}")
        print(f"IAQI PM2.5: {IAQ_PM2}")
        print(f"IAQI PM10: {IAQ_PM10}")
        print(f"Overall IAQI: {IAQ_ovr}")
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
            client.publish("ESP32/Relay", payload="ON", qos=0)
            time.sleep(0.5)
            IAQ = "3"
            time.sleep(0.3)
            #IAQ += sensor_id
            #client.publish("cu/vent", payload=True, qos=0)
            print("Dangerous")
            time.sleep(0.5)
            subprocess.run(['python','/home/freshair/Documents/Testing_Codes/User_Interface/Testing_Plan_Main_Copy.py', IAQ, sensor_id] ,text=True, timeout=3)
            time.sleep(0.5)
            new_data = False
            
        # If under "Dangerous" threshold and over/equal to conditions below, "Unhealthy" PM condition met (via OSHA 1910.1000)
        elif IAQ_ovr >=100:
            #client.publish("cu/pm_status", payload="Unhealthy", qos=0)
            print("Unhealthy")
            time.sleep(0.3)
            IAQ = "2"
            #IAQ += sensor_id
            time.sleep(0.5)
            subprocess.run(['python','/home/freshair/Documents/Testing_Codes/User_Interface/Testing_Plan_Main_Copy.py', IAQ, sensor_id] ,text=True, timeout=3)
            time.sleep(0.5)
            new_data = False
            
        # If below both conditions, "Healthy" PM condition met (via OSHA 1910.1000)
        else:
            time.sleep(0.3)
            client.publish("ESP32/Relay", "OFF", qos=0)
            time.sleep(0.3)
            IAQ = "1"
            time.sleep(0.3)
            print("Healthy")
            #IAQ += sensor_id
            time.sleep(0.5)
            subprocess.run(['python','/home/freshair/Documents/Testing_Codes/User_Interface/Testing_Plan_Main_Copy.py', IAQ, sensor_id] ,text=True, timeout=3)
            time.sleep(0.5)
            toggle = True
            new_data = False

        # Keep track of previous status of PM for each sensor
        if sensor_id == "1":
            prev_1 = IAQ
        if sensor_id == "2":
            prev_2 = IAQ
        if sensor_id == "3":
            prev_3 = IAQ
        if sensor_id == "4":
            prev_4 = IAQ
            
def button_callback(channel):
    GPIO.output(18, False)
    GPIO.output(16, False)
    
GPIO.add_event_detect(37,GPIO.RISING,callback=button_callback)
reset_sensors()
GPIO.cleanup()
client.loop_stop()
sys.exit()
GPIO.cleanup()
client.loop_stop()
sys.exit()
