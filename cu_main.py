# Initialize libraries
import time
import paho.mqtt.client as paho
import sys
import RPi.GPIO as GPIO
from paho import mqtt
import json
import subprocess

# Initialize variables
toggle = False
connection_status = False
new_data = False
user_input = False
sensor = 0
Sensor_1 = False
Sensor_2 = False
Sensor_3 = False
received = False
vent = False
data = {}
IAQ = 0 #UI Variable
IAQ_PM2 = 0
IAQ_PM10 = 0
IAQ_ovr = 0
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(16,GPIO.OUT, initial = False)                  
GPIO.setup(18,GPIO.OUT, initial = False)
# Need a new variable for sensor id
UI_command = ["alarms","/home/freshair/Documents/PM_Device/Alarms.py",IAQ,sensor]

# Raw data from sensors comes in the following format:
# {"iaqi_pm2.5":12,"iaqi_pm10":2,"overall_iaqi":12}
# NOTE: Numeric values between ":" and "," characters will change
# depending on real time data

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
    global Sensor_1
    global Sensor_2
    global Sensor_3
    
    # If message from Toggle, button was pressed, set to true
    if "Toggle" in msg.topic:
        toggle = True
        
    # If message from Ventilation, set equal to message value
    if "Vent" in msg.topic:
        vent_payload = msg.payload.decode("utf-8").strip().lower()
    
        if vent_payload in ['true', '1', b'true', b'1']:
            vent = True
        elif vent_payload in ['false', '0', b'false', b'0']:
            vent = False
        else:
            vent = False
        
        received = True
        
    # If message is from sensor, parse data 
    if "Sensor" in msg.topic:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        print("Received message: ", data)
        received = True
        
    # Determine sensor ID
    if "Sensor1" in msg.topic:
        Sensor_1 = True
    if "Sensor2" in msg.topic:
        Sensor_2 = True
    if "Sensor3" in msg.topic:
        Sensor_3 = True
     
# MQTT Initialization
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set("freshair", "Freshair1")
client.connect("307235db588f42bda5a2c31d242ef05c.s1.eu.hivemq.cloud", 8883)
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
    while toggle == True:
        GPIO.output(18, False)
        time.sleep(0.5)
        GPIO.output(16, False)
        time.sleep(0.5)
        print("Siren Status: OFF")
        toggle = False
            
    # If data received
    while received == True:
        if Sensor_1 == True or Sensor_2 == True or Sensor_3 == True:
            # Parse sensor data
            IAQ_PM2 = data.get("iaqi_pm2.5", 0)
            IAQ_PM10 = data.get("iaqi_10", 0)
            IAQ_ovr = data.get("overall_iaqi", 0)
            new_data = True
            received = False
        
        # Handle ventilation status
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
        if IAQ_PM2 >= 55 or IAQ_PM10 >= 255 or IAQ_ovr >=255:
            client.publish("cu/pm_status", payload="Dangerous", qos=0)
            time.sleep(0.5)
            IAQ = 3
            client.publish("cu/vent", payload=True, qos=0)
            print("Ventilation Status: ON")
            time.sleep(0.5)
            process = subprocess.run(UI_command, capture_output=True, text=true)
            time.sleep(5)
            new_data = False
            
        # If under "Dangerous" threshold and over/equal to conditions below, "Unhealthy" PM condition met (via OSHA 1910.1000)
        elif IAQ_PM2 >= 35 or IAQ_PM10 >= 155 or IAQ_ovr >=155:
            client.publish("cu/pm_status", payload="Unhealthy", qos=0)
            print("Siren Status: YELLOW")
            IAQ = 2
            time.sleep(0.5)
            process = subprocess.run(UI_command, capture_output=True, text=true)
            time.sleep(5)
            new_data = False
            
        # If below both conditions, "Healthy" PM condition met (via OSHA 1910.1000)
        else:
            client.publish("cu/pm_status", payload="Healthy", qos=0)
            client.publish("cu/vent", payload=False, qos=0)
            IAQ = 1
            time.sleep(0.5)
            process = subprocess.run(UI_command, capture_output=True, text=true)
            time.sleep(5)
            print("Ventilation Status: OFF")
            print("Siren Status: OFF")
            toggle = True
            new_data = False
            
            
        # Publish sensor ID of the data to the broker    
        if Sensor_1 == True:
            client.publish("cu/sensor_id", payload="Sensor 1", qos=0)
            print("Data received from Sensor 1")
            # Save as previous status of Sensor 1, 2, 3, etc.
        if Sensor_2 == True:
            client.publish("cu/sensor_id", payload="Sensor 2", qos=0)
            print("Data received from Sensor 2")
        if Sensor_3 == True:
            client.publish("cu/sensor_id", payload="Sensor 3", qos=0)
            print("Data received from Sensor 3")           
            
GPIO.cleanup()
client.loop_stop()
sys.exit()
