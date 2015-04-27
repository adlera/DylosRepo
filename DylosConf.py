__author__ = 'fassler'

import pickle
import os
import sys
import subprocess
import serial

print("hello, welcome to the Dylos configuration")
conf_location = "/home/pi/Dylos/DylosConf.txt"
sensor_basic_conf = "/home/pi/Dylos/SensorBasicConf.txt"
dylos_reader = "/home/pi/Dylos/DylosToSerial.py"
server_conf = "/home/pi/Dylos/ServerConf.txt"
reboot_flag = "/home/pi/Dylos/rebootFlag"

'''remove reboot flag that created in previous run'''
if os.path.isfile(reboot_flag):
    os.system('rm ' + reboot_flag)

'''open the configuration file. if the file is empty append defulte data.
if not, unpickle the user data from the file'''


if os.path.isfile(conf_location):
    f = open(conf_location, 'rb')
    USER_DATA = f.readline()
else:
    f = open(conf_location, 'wb')
    USER_DATA = ""

if os.path.isfile(server_conf):
    f = open(server_conf, 'rb')
    SERVER_CONF = f.readline()
else:
    f = open(server_conf, 'wb')
    SERVER_CONF = ""


if USER_DATA=="":
    USER_DATA = {"ID": "default","network": "default","modem": "other","mail": "default","update period": 15,"save period": 30,
                 "backup folder": "/home/pi/Dylos/BackUpFiles", "sensor type": "dylos", "sensor serial name": "Prolific"}
    if not os.path.isfile('./DylosDesc.txt'):
        desc_f = open('DylosDesc.txt','w')
        desc_f.write("ID: the sensor's id\n")
        desc_f.write("network: the name of the GSM network(Orange,Cellcom,Pelephone,Hot,Golan,012)\n")
        desc_f.write("modem: the name of the modem(should be same as the prefix of the modem config file : <name>.config)\n")
        desc_f.write("mail: the mail adress which the alert messages will sent to\n")
        desc_f.write("update period: integer which is the number of reads from the sensor before updating the database\n")
        desc_f.write("save period: integer which is the number of days for saving the backup files\n")
        desc_f.write("backup folder: the full path to the folder that the backup files will save in\n")
        desc_f.write("sensor type: the type of the sensor(e.g. dylos)\n")
        desc_f.write("sensor serial name: giving from the 'lsusb' command, the name of the sensor serial connection\n")
        desc_f.close()
else:
    with open(conf_location, 'rb') as handle:
      USER_DATA = pickle.loads(handle.read())

if SERVER_CONF == "":
    SERVER_CONF = {"user": "APMoD", "password": "AirPol2015", "host": "132.68.226.244", "database": "APMoD"}
else:
    with open(server_conf, 'rb') as handle:
      SERVER_CONF = pickle.loads(handle.read())



print("the current server configuration is: " + str(SERVER_CONF.items()))
print("Do you want to change the server configuration? y/n.")
while True:
    read = (str(raw_input())).upper()
    if read == "N":         
         break
    elif read == "Y":
        print("Please insert the server details")
        SERVER_CONF["user"] = str(raw_input("user: "))
        SERVER_CONF["password"] = str(raw_input("password: "))
        SERVER_CONF["host"] = str(raw_input("host: "))
        SERVER_CONF["database"] = str(raw_input("database: "))
        break
    else:
        print("incorrect answer, please type y/n")
        continue


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
                         sensor_values="Dylos ID,Date,Pm 0.5-2.5,Pm > 2.5",
                         baudrate=9600, parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_TWO,bytesize=serial.EIGHTBITS,writeTimeout=0,timeout=10)

# to add other sensor configuration, change the lines below/add more else if (elif..)
'''elif USER_DATA["sensor type"] == "other sensor":
    sensor_values = "some other values" '''

print("the current data is: " + str(USER_DATA.items()))

print("the current server configuration is: " + str(SERVER_CONF.items()))


print("Do you want to execute the main reader script in startup? y/n.")
while True:
    read = (str(raw_input())).upper()
    if read == "N":
         removeStartupExec = "sudo sed -i 's/python \/home\/pi\/Dylos\/DylosToSerial.py \&//' /etc/rc.local"
         os.system(removeStartupExec)
         break
    elif read == "Y":
        res = os.system('grep python /etc/rc.local > /dev/null')
        if res !=  0:
            makeStartupExec = "sudo sed -i 's/^exit 0/python \/home\/pi\/Dylos\/DylosToSerial.py \&\\nexit 0/' /etc/rc.local"
            os.system(makeStartupExec)
        break
    else:
        print("incorrect answer, please type y/n")
        continue


with open(conf_location, 'wb') as handle:
      pickle.dump(USER_DATA,handle)

with open(sensor_basic_conf, 'wb') as handle:
      pickle.dump(sensor_values,handle)

with open(server_conf, 'wb') as handle:
      pickle.dump(SERVER_CONF,handle)



