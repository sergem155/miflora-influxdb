# miflora-influxdb
query Xiaomi Mi Flora plant monitors, extract hourly historical data and push into influxdb. Requires python3

Bluetooth access is influenced by [miflora module](https://github.com/open-homeautomation/miflora)

Rename config-example.py to config.py. It's OK to have an empty device array intially. 

Scan for plant monitors (make sure to turn them one by one and mark them with a marker once identified):
```sh
$ sudo python3 scan.py
```

Poll for data:
```sh
$ ./poll-insert.py
$ ./poll-insert.py device1 device2 device3
```

Dependencies: InfluxDB, btlewrap, bluepy
```sh
$ sudo apt install python3-pip
$ sudo pip3 install influxdb
$ sudo pip3 install btlewrap
$ sudo pip3 install bluepy
```

