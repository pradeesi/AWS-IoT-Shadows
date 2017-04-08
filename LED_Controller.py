# ------------------------------------------
# --- Author: Pradeep Singh
# --- Date: 29th March 2017
# --- Version: 1.0
# --- Description: This python script will leverage AWS IoT Shadow to control LED
# ------------------------------------------

# Import package
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import ssl, time, sys, json

# =======================================================
# Set Following Variables
# AWS IoT Endpoint
MQTT_HOST = ""
# CA Root Certificate File Path
CA_ROOT_CERT_FILE = ""
# AWS IoT Thing Name
THING_NAME = ""
# AWS IoT Thing Certificate File Path
THING_CERT_FILE = "42f2bc1d29-certificate.pem.crt"
# AWS IoT Thing Private Key File Path
THING_PRIVATE_KEY_FILE = "42f2bc1d29-private.pem.key"
# =======================================================


# =======================================================
# No need to change following variables
LED_PIN = 14
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
SHADOW_UPDATE_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update"
SHADOW_UPDATE_ACCEPTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/accepted"
SHADOW_UPDATE_REJECTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/rejected"
SHADOW_UPDATE_DELTA_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/delta"
SHADOW_GET_TOPIC = "$aws/things/" + THING_NAME + "/shadow/get"
SHADOW_GET_ACCEPTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/get/accepted"
SHADOW_GET_REJECTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/get/rejected"
SHADOW_STATE_DOC_LED_ON = """{"state" : {"reported" : {"LED" : "ON"}}}"""
SHADOW_STATE_DOC_LED_OFF = """{"state" : {"reported" : {"LED" : "OFF"}}}"""
# =======================================================


# Initiate GPIO for LED
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)

# Initiate MQTT Client
mqttc = mqtt.Client("client2")


# Master LED Control Function
def LED_Status_Change(Shadow_State_Doc, Type):
	# Parse LED Status from Shadow
	DESIRED_LED_STATUS = ""
	print "\nParsing Shadow Json..."
	SHADOW_State_Doc = json.loads(Shadow_State_Doc)
	if Type == "DELTA":
		DESIRED_LED_STATUS = SHADOW_State_Doc['state']['LED']
	elif Type == "GET_REQ":
		DESIRED_LED_STATUS = SHADOW_State_Doc['state']['desired']['LED']
	print "Desired LED Status: " + DESIRED_LED_STATUS

	# Control LED 
	if DESIRED_LED_STATUS == "ON":
		# Turn LED ON
		print "\nTurning ON LED..."
		GPIO.output(LED_PIN, GPIO.HIGH)
		# Report LED ON Status back to Shadow
		print "LED Turned ON. Reporting ON Status to Shadow..."
		mqttc.publish(SHADOW_UPDATE_TOPIC,SHADOW_STATE_DOC_LED_ON,qos=1)
	elif DESIRED_LED_STATUS == "OFF":
		# Turn LED OFF
		print "\nTurning OFF LED..."
		GPIO.output(LED_PIN, GPIO.LOW)
		# Report LED OFF Status back to Shadow
		print "LED Turned OFF. Reporting OFF Status to Shadow..."
		mqttc.publish(SHADOW_UPDATE_TOPIC,SHADOW_STATE_DOC_LED_OFF,qos=1)
	else:
		print "---ERROR--- Invalid LED STATUS."



# Define on connect event function
# We shall subscribe to Shadow Accepted and Rejected Topics in this function
def on_connect(mosq, obj, rc):
	print "Connected to AWS IoT..."
	# Subscribe to Delta Topic
	mqttc.subscribe(SHADOW_UPDATE_DELTA_TOPIC, 1)
	# Subscribe to Update Topic
	#mqttc.subscribe(SHADOW_UPDATE_TOPIC, 1)
	# Subscribe to Update Accepted and Rejected Topics
	mqttc.subscribe(SHADOW_UPDATE_ACCEPTED_TOPIC, 1)
	mqttc.subscribe(SHADOW_UPDATE_REJECTED_TOPIC, 1)	
	# Subscribe to Get Accepted and Rejected Topics
	mqttc.subscribe(SHADOW_GET_ACCEPTED_TOPIC, 1)
	mqttc.subscribe(SHADOW_GET_REJECTED_TOPIC, 1)


# Define on_message event function. 
# This function will be invoked every time,
# a new message arrives for the subscribed topic 
def on_message(mosq, obj, msg):
	if str(msg.topic) == SHADOW_UPDATE_DELTA_TOPIC:
		print "\nNew Delta Message Received..."
		SHADOW_STATE_DELTA = str(msg.payload)
		print SHADOW_STATE_DELTA
		LED_Status_Change(SHADOW_STATE_DELTA, "DELTA")
	elif str(msg.topic) == SHADOW_GET_ACCEPTED_TOPIC:
		print "\nReceived State Doc with Get Request..."
		SHADOW_STATE_DOC = str(msg.payload)
		print SHADOW_STATE_DOC
		LED_Status_Change(SHADOW_STATE_DOC, "GET_REQ")
	elif str(msg.topic) == SHADOW_GET_REJECTED_TOPIC:
		SHADOW_GET_ERROR = str(msg.payload)
		print "\n---ERROR--- Unable to fetch Shadow Doc...\nError Response: " + SHADOW_GET_ERROR
	elif str(msg.topic) == SHADOW_UPDATE_ACCEPTED_TOPIC:
		print "\nLED Status Change Updated SUCCESSFULLY in Shadow..."
		print "Response JSON: " + str(msg.payload)
	elif str(msg.topic) == SHADOW_UPDATE_REJECTED_TOPIC:
		SHADOW_UPDATE_ERROR = str(msg.payload)
		print "\n---ERROR--- Failed to Update the Shadow...\nError Response: " + SHADOW_UPDATE_ERROR
	else:
		print "AWS Response Topic: " + str(msg.topic)
		print "QoS: " + str(msg.qos)
		print "Payload: " + str(msg.payload)


def on_subscribe(mosq, obj, mid, granted_qos):
	#As we are subscribing to 3 Topics, wait till all 3 topics get subscribed
	#for each subscription mid will get incremented by 1 (starting with 1)
	if mid == 3:
		# Fetch current Shadow status. Useful for reconnection scenario. 
		mqttc.publish(SHADOW_GET_TOPIC,"",qos=1)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print "Diconnected from AWS IoT. Trying to auto-reconnect..."

# Register callback functions
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect

# Configure TLS Set
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY_FILE, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)		

# Continue monitoring the incoming messages for subscribed topic
mqttc.loop_forever()
