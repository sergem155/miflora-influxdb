#!/usr/bin/python3
from bluepy.btle import Scanner, DefaultDelegate, Peripheral
from config import *

dev_dict = {}
for (temphostname,hostmac) in devices.items():
	dev_dict[hostmac.lower()] = temphostname

class ScanDelegate(DefaultDelegate):
	def __init__(self):
		DefaultDelegate.__init__(self)

	def handleDiscovery(self, dev, isNewDev, isNewData):
		if dev.addr.upper().startswith('C4:7C:8D:'):
			if isNewDev:
				print("Discovered device: %s - %s" % (dev.addr,dev_dict[dev.addr.lower()]))
			elif isNewData:
				print("Received new data from: %s - %s" % (dev.addr,dev_dict[dev.addr.lower()]))

scanner = Scanner().withDelegate(ScanDelegate())
device_list = scanner.scan(10.0)

for dev in device_list:
	if dev.addr.upper().startswith('C4:7C:8D:'):
		hostname = dev_dict[dev.addr.lower()]
		print("Hostname: %s, Device %s (%s), RSSI=%d dB" % (hostname, dev.addr, dev.addrType, dev.rssi))
		for (adtype, desc, value) in dev.getScanData():
		    print("  %s = %s" % (desc, value))
		device = Peripheral()
		device.connect(dev.addr)
		data = device.readCharacteristic(0x38)
		battery = data[0]
		fw = data[2:]
		print(" - fw: %s, battery %d" %(fw, battery))
		device.disconnect()

