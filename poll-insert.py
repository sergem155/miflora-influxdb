#!/usr/bin/python3
import bluepy.btle
from miot_encode import *
from influxdb import InfluxDBClient
from struct import unpack
import datetime
import sys
import time
from config import *

#globals
dbclient = InfluxDBClient(*influx_args)
json_body = []
notificationsFired={}
count = 0
line = ''
device = None
battery = 0
starttimer = 0
now = 0
finish = ""

#wait for a specific notification, in 1 sec time intervals
def waitForANotification(device, cHandle, timeout):
	t = time.perf_counter()
	notificationsFired[cHandle] = False
	while(not notificationsFired[cHandle] and time.perf_counter() < t+timeout):
		device.waitForNotifications(1)
	return notificationsFired[cHandle]

#delegate class to receive notifications
class myDelegate(bluepy.btle.DefaultDelegate):
	def __init__(self):
		bluepy.btle.DefaultDelegate.__init__(self)

	def handleNotification(self, cHandle, data):
		global notificationsFired
		global count 
		global json_body
		global starttimer
		global device
		global finish
		notificationsFired[cHandle] = True
		#print("%02x" % cHandle)
		# secure handshake response received, do not check it, just send encoded session finish command
		if(cHandle == 0x12):
			device.writeCharacteristic(0x12,finish,True)
		# hourly data interface notifications		
		elif(cHandle == 0x3e):
			# hourly data count is ready in 0x3c
			if(data[0]==0xa0):
				bcount = device.readCharacteristic(0x3c)
				count = bcount[0]+bcount[1]*256
			# hourly data for specific hour is ready in 0x3c
			elif(data[0]==0xa1):
				line = device.readCharacteristic(0x3c)
				# prepare data for influx import
				timer, temp, light, moisture, conductivity = unpack('<LhxIBhxx',line)
				temp = temp/10.0
				timer -= starttimer
				ts = datetime.datetime.fromtimestamp(now+timer).strftime('%Y-%m-%dT%H:%M:%SZ')
				# append json
				json_body.append(
				{
					"measurement": "monitor_reading",
					"tags": {
						"monitor": hostname
					},
					"time": ts,
					"fields": {
						"battery": battery,
						"temperature": temp,
						"moisture": moisture,
						"light": light,
						"conductivity": conductivity
					}
				})

	# not used
	def handleDiscovery(self, scanEntry, isNewDev, isNewData):
		pass

if len(sys.argv)>1:
	to_scan = sys.argv[1:]

for hostname in to_scan:
	mac = devices[hostname]
	print("connecting: %s @ %s" %(hostname,mac))
	try:
		json_body=[]
		device = bluepy.btle.Peripheral()
		device.setDelegate(myDelegate())
		device.connect(mac, iface=0)
		print("connected")
		# start session command, possibly product-specific
		device.writeCharacteristic(0x1b, bytes([0x90, 0xca, 0x85, 0xde]),True)
		# one-time key the device will use to encode its reply
		btoken = generate_token()
		# handshake key, mac and product code-based
		# 0x98 is the miflora product code, other codes are 0x15d (flowerpot.v2) and 0x3bc (flowercare.l1)
		# if not performing this handshake, the device will hangup in the middle of recorded data retrieval 
		key = mix_a(mac,0x98)
		# encrypted one-time key
		challenge = RC4_encrypt(key,btoken)
		# one-time-key-encrypted finish command
		finish = RC4_encrypt(btoken,bytes.fromhex('92ab54fa')) # magic end session word, possibly product-specific
		# enable notification on 0x12 handle
		device.writeCharacteristic(0x13,bytes([0x01, 0x00]),True)
		# send key
		device.writeCharacteristic(0x12,challenge,True)
		# read reply and send finish in the notification handler
		waitForANotification(device,0x12,5)
		# disable notifications
		device.writeCharacteristic(0x13,bytes([0x01, 0x00]),True)
		print("handshake finished, getting hours")
		# read battery level
		battery = device.readCharacteristic(0x38)
		battery = battery[0] # 100% fits in one byte
		# enable notifications on handle 0x3e
		device.writeCharacteristic(0x3f,bytes([0x01, 0x00]),True)
		# sync clocks - note local time and read device timer 
		now = datetime.datetime.utcnow().timestamp()
		timer = device.readCharacteristic(0x41)
		starttimer = unpack('<L', timer)[0]
		# get hours count command - result is read in notification handler
		# make sure your bluetooth supervision timeout is at least 1000 msec, as the
		# device freezes here for quite a while, which makes bluez treat it as hangup otherwise
		device.writeCharacteristic(0x3e,bytes([0xA0, 0x00, 0x00]),True)
		# count comes as a notification  
		if(waitForANotification(device,0x3e,5)): 
			print("count: %d" % count)
			for i in range(count):
				print(i)
				# request hour i
				device.writeCharacteristic(0x3e,bytes([0xA1, i%256, int(i/256)]),True)
				# read reply in the notification handler
				waitForANotification(device,0x3e,5)
			dbclient.write_points(json_body)
			# disable notifications on handle 0x3e
			device.writeCharacteristic(0x3f,bytes([0x00, 0x00]),True)
			# reset hourly data storage
			device.writeCharacteristic(0x3e,bytes([0xA2, 0x00, 0x00]),True)
		else:
			print("tired waiting for a notification")
		device.disconnect()
		print('done')
	except bluepy.btle.BTLEException as e:
		print("connection and/or query failed - unable to connect?")
