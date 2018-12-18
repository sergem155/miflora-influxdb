#!/usr/bin/python3
from btlewrap.base import BluetoothInterface, BluetoothBackendException
from btlewrap.bluepy import BluepyBackend
import datetime
from influxdb import InfluxDBClient
from struct import unpack
from config import *
from pprint import pprint
import sys

dbclient = InfluxDBClient(*influx_args)
json_body = []
interface = BluetoothInterface(BluepyBackend, 'hci0')

if len(sys.argv)>1:
	to_scan = sys.argv[1:]

for hostname in to_scan:
	mac = devices[hostname]
	print("connecting: %s @ %s" %(hostname,mac))
	try:
		with interface.connect(mac) as connection:
			try:
				# enable notifications on handle 35 (seems to help)
				connection.write_handle(0x36, bytes([0x01, 0x00])) 
				# product-specific enable code  
				connection.write_handle(0x1b, bytes([0x90, 0xca, 0x85, 0xde]))   
				# get FW version and battery
				data = connection.read_handle(0x38)
				battery = data[0]
				# get one-time reading
				connection.write_handle(0x33,  bytes([0xA0, 0x1F]))   
				current = connection.read_handle(0x35)
				# prepare data
				ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
				temp, light, moisture, conductivity = unpack('<hxIBhxxxxxx', current)
				temp = temp/10.0
				ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
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
				print('current reading - OK') 
				# write to inluxdb
				dbclient.write_points(json_body)
				json_body = []
				# get monitor's current timer value
				now = datetime.utcnow().timestamp()
				timer = connection.read_handle(0x41)
				starttimer = unpack('<L', timer)[0]
				# get counter of stored hourly readings
				connection.write_handle(0x3e, bytes([0xA0, 0x00, 0x00]))
				d = connection.read_handle(0x3c)
				count = d[0]
				print('getting hours')
				# iterate over stored hours counter
				print(count)
				i=0
				while i<count:
					#print(i)
					try:
						connection.write_handle(0x3e, bytes([0xA1, i, 0x00]))   
						line = connection.read_handle(0x3c)
					except:
						break
					# prepare data
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
					i=i+1
				dbclient.write_points(json_body)
				# reset hourly reading buffer
				connection.write_handle(0x3e, bytes([0xA2, 0x00, 0x00]))   
				# disable notifications
				connection.write_handle(0x36, bytes([0x00, 0x00]))   
				# ??
				connection.write_handle(0x33,  bytes([0xc0, 0x1F]))   
				print('past readings - OK') 
			except:
				print("hourly readings retrieval failed")
	except:
		print("connection and query failed - unable to connect?")
