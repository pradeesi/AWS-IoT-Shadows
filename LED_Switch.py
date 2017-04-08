# ------------------------------------------
# --- Author: Pradeep Singh
# --- Date: 29th March 2017
# --- Version: 1.0
# --- Description: This python script will update AWS Thing Shadow for a Device/Thing
# ------------------------------------------

# Import package
import paho.mqtt.client as mqtt
import ssl, time, sys

# =======================================================
# Set Following Variables
# AWS IoT Endpoint
MQTT_HOST = ""
# CA Root Certificate File Path
CA_ROOT_CERT_FILE = ""
# AWS IoT Thing Name
THING_NAME = ""
# AWS IoT Thing Certificate File Path
THING_CERT_FILE = ""
# AWS IoT Thing Private Key File Path
THING_PRIVATE_KEY_FILE = ""
# =======================================================


# =======================================================
# No need to change following variables
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
SHADOW_UPDATE_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update"
SHADOW_UPDATE_ACCEPTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/accepted"
SHADOW_UPDATE_REJECTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/rejected"
SHADOW_STATE_DOC_LED_ON = """{"state" : {"desired" : {"LED" : "ON"}}}"""
SHADOW_STATE_DOC_LED_OFF = """{"state" : {"desired" : {"LED" : "OFF"}}}"""
RESPONSE_RECEIVED = False
# =======================================================



# Initiate MQTT Client
mqttc = mqtt.Client("client1")

# Define on connect event function
# We shall subscribe to Shadow Accepted and Rejected Topics in this function
def on_connect(mosq, obj, rc):
    mqttc.subscribe(SHADOW_UPDATE_ACCEPTED_TOPIC, 1)
    mqttc.subscribe(SHADOW_UPDATE_REJECTED_TOPIC, 1)

# Define on_message event function. 
# This function will be invoked every time,
# a new message arrives for the subscribed topic 
def on_message(mosq, obj, msg):
	if str(msg.topic) == SHADOW_UPDATE_ACCEPTED_TOPIC:
		print "\n---SUCCESS---\nShadow State Doc Accepted by AWS IoT."
		print "Response JSON:\n" + str(msg.payload)
	elif str(msg.topic) == SHADOW_UPDATE_REJECTED_TOPIC:
		print "\n---FAILED---\nShadow State Doc Rejected by AWS IoT."
		print "Error Response JSON:\n" + str(msg.payload)
	else:
		print "AWS Response Topic: " + str(msg.topic)
		print "QoS: " + str(msg.qos)
		print "Payload: " + str(msg.payload)
	# Disconnect from MQTT_Broker
	mqttc.disconnect()
	global RESPONSE_RECEIVED
	RESPONSE_RECEIVED = True



# Register callback functions
mqttc.on_message = on_message
mqttc.on_connect = on_connect

# Configure TLS Set
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY_FILE, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)		
mqttc.loop_start()


print "Enter 1 to Turn On the LED"
print "Enter 2 to Turn OFF the LED"
print "Enter 3 to exit"
data = raw_input("Select an option:")
if data == "1":
	mqttc.publish(SHADOW_UPDATE_TOPIC,SHADOW_STATE_DOC_LED_ON,qos=1)
elif data == "2":
	mqttc.publish(SHADOW_UPDATE_TOPIC,SHADOW_STATE_DOC_LED_OFF,qos=1)
elif data == "3":
	sys.exit() 
else:
	print("Invalid input try again...")
	sys.exit() 


# Wait for Response
Counter = 1
while True:
	time.sleep(1)
	if Counter == 10:
		print "No response from AWS IoT. Check your Settings."
		break
	elif RESPONSE_RECEIVED == True:
		break
	Counter = Counter + 1
