__author__ = 'fassler'

import pickle
import os
import sys
import subprocess

mode = "else"
print("hello, welcome to the Dylos configuration")
if mode != "test":
    conf_location = "/home/pi/Dylos/DylosConf.txt"
    sensor_basic_conf = "/home/pi/Dylos/SensorBasicConf.txt"
    dylos_reader = "/home/pi/Dylos/DylosToSerial.py"

else:
    conf_location = '/Users/fassler/PycharmProjects/Dylos_Via_RaspberryPi_connction/DylosConf.txt'
    sensor_basic_conf = '/Users/fassler/PycharmProjects/Dylos_Via_RaspberryPi_connction/SensorBasicConf.txt'
    dylos_reader = "/Users/fassler/PycharmProjects/Dylos_Via_RaspberryPi_connction/DylosToSerial.py"

'''open the configuration file. if the file is empty append defulte data.
if not, unpickle the user data from the file'''

if os.path.isfile(conf_location):
    f = open(conf_location, 'rb')
    USER_DATA = f.readline()
else:
    f = open(conf_location, 'wb')
    USER_DATA = ""

if USER_DATA=="":
    USER_DATA = {"ID": "default","network": "default","modem": "other",
                 "folder": "/home/pi/Dylos", "sensor type": "dylos"}
else:
    with open(conf_location, 'rb') as handle:
      USER_DATA = pickle.loads(handle.read())
''' go over each key and ask the user if he want to change it'''

for key in USER_DATA:
    if USER_DATA[key] == "default":
        print("please enter the %s value" % key)
        r = str(raw_input("value: "))
        USER_DATA[key] = r
    else:
        print("the current data is: " + str(USER_DATA.items()))
        print("Do you want to change the " + key + " value? y/n.")
        while True:
	    read = (str(raw_input())).upper()
            if read == "N":
                break
            elif read == "Y":
                print("please enter the %s value" % key)
                r = str(raw_input("The new value is: "))
                USER_DATA[key] = r
                break
	    else:
	        print("incorrect answer, please type y/n")
	        continue

APN = {"Orange": "uinternet", "Cellcom": "internetg", "Pelephone": "internet.pelephone.net.il", "Hot": "net.hotm", "Golan": "internet.golantelecom.net.il", "012": "uwap.orange.co.il"}
updateInternetStr = "sudo sed -i 's/\"IP\".*/\"IP\",\"" + APN[USER_DATA["network"]] + "\"/' /etc/wvdial.conf"
os.system(updateInternetStr)

 
if USER_DATA["modem"] != "other":
    modemConfPath = "/home/pi/Dylos/" + USER_DATA["modem"] + ".conf"
    if os.path.isfile(modemConfPath):
        os.system("sudo cp " + modemConfPath + " /etc/usb_modeswitch.conf")
    else: 
        print("missing modem configuration file, please supply a configuration file and try again.Abort")
        exit(1)

if USER_DATA["sensor type"] == "dylos":
    sensor_values = dict(sensor_type="dylos",
                         sensor_values="Dylos ID,Location,Date,Pm 0.5-2.5,Pm > 2.5",
                         serial_connection="serial_port, baudrate=9600, parity=serial.PARITY_NONE, "
                                           "stopbits=serial.STOPBITS_TWO, "
                                           "bytesize=serial.EIGHTBITS, writeTimeout=0, timeout=10")

# to add other sensor configuration, change the lines below/add more else if (elif..)
'''elif USER_DATA["sensor type"] == "other sensor":
    sensor_values = "some other values" '''

print("the current data is: " + str(USER_DATA.items()))

with open(conf_location, 'wb') as handle:
      pickle.dump(USER_DATA,handle)

with open(sensor_basic_conf, 'wb') as handle:
      pickle.dump(sensor_values,handle)

#the configuration is now finished, execute the main program:
run_dylos = subprocess.Popen([sys.executable,dylos_reader])
run_dylos.communicate()
