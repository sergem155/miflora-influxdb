from btlewrap.base import BluetoothInterface, BluetoothBackendException
from btlewrap.bluepy import BluepyBackend
from hosts import hosts

VALID_DEVICE_NAMES = ['flower mate','flower care']
DEVICE_PREFIX = 'C4:7C:8D:'

for (mac, name) in BluepyBackend.scan_for_devices(10):
	if (name is not None and name.lower() in VALID_DEVICE_NAMES) or \
			mac is not None and mac.upper().startswith(DEVICE_PREFIX):
		hostname="none"
		for (temphostname,hostmac) in hosts.items():
			if(hostmac.lower()==mac.lower()):
				hostname=temphostname
		print("%s: %s" %(mac.upper(),hostname))
		interface = BluetoothInterface(BluepyBackend, 'hci0')
		with interface.connect(mac) as connection:
			data = connection.read_handle(0x38)
			battery = data[0]
			fw = data[2:]
			print(" - fw: %s, battery %d" %(fw,battery))
