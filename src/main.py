
import network
import time
import json
import secrets
from machine import Pin
from utime import sleep
from umqtt.simple import MQTTClient
devicenumber = 1
prefix = f"pico/{devicenumber}/"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWD)
while not wlan.isconnected() and wlan.status() >= 0:
	print("Waiting to connect to SSID...")
	time.sleep(1)
print("Connected to %s" % wlan.config('essid'))

def callback(topic, msg):
    t = topic.decode("utf-8").lstrip(prefix)
    if t[:4] == 'set/':
        p = int(t[4:])
        data = int(msg)
        print(f"Write status of GPIO pin:{p} with the value of {data}")
        led = Pin(p, Pin.OUT)
        led.value(data)
        client.publish(prefix+'status/'+str(p),str(data))

def heartbeat(first):
    global lastping
    if first:
        client.ping()
        lastping = time.ticks_ms()
    if time.ticks_diff(time.ticks_ms(), lastping) >= 300000:
        client.ping()
        lastping = time.ticks_ms()
    return

def create_mqtt_switch(device,gpiopin):
    obj = {
        "device": {
            "identifiers": [
                f"pico_{device}"
            ],
            "manufacturer": "Raspberry",
            "model": "Pico W",
            "name": "Lego controller"
        },
        "unique_id": f"pico_{device}_{gpiopin}",
        "command_topic": f"{prefix}set/{gpiopin}",
        "name": f"GPIO {gpiopin}",
        "payload_off": "0",
        "payload_on": "1",
        "state_topic": f"{prefix}status/{gpiopin}",
        "state_on": "1",
        "state:off": "0",
        "platform": "mqtt"
    }
    formatted = json.dumps(obj)
    return formatted

client = MQTTClient(prefix+"picow", secrets.MQTT_BROKER,user=None, password=None, keepalive=300, ssl=False, ssl_params={})
client.connect()

for i in range(0, 29): 
    if i not in range(23, 26): # 23-26 are used for the wifi module
        client.publish(f'homeassistant/switch/pico_{devicenumber}/GPIO{i}/config', create_mqtt_switch(devicenumber, i))
        #print("Published switch configuration: %s" % i)
        sleep(0.2)


print("Waiting for messages...")
heartbeat(True)
client.set_callback(callback)
client.subscribe(prefix+"set/#")
while True:
    client.check_msg()
    heartbeat(False)