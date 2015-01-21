#!/bin/python
__author__ = 'fassler'
import os
import sys
import subprocess
import time
mode = "else"
if mode != "test":
    conf_exe = "/home/pi/Dylos/DylosConf.py"
    conf_location = "/home/pi/Dylos/DylosConf.txt"
    dylos_reader = "/home/pi/Dylos/DylosToSerial.py"
else:
    conf_exe = "/Users/fassler/PycharmProjects/Dylos_Via_RaspberryPi_connction/DylosConf.py"
    conf_location = "/Users/fassler/PycharmProjects/Dylos_Via_RaspberryPi_connction/DylosConf.txt"
    dylos_reader = "/Users/fassler/PycharmProjects/Dylos_Via_RaspberryPi_connction//DylosToSerial.py"

'''open the configuration file. if there is no file/the file is empty run DylosConf and wait a minute.
    if not, skip to Dylos reader file'''
if not os.path.isfile(conf_location):
    os.system(conf_exe)
elif os.path.isfile(conf_location):
    f = open(conf_location, 'rb')
    USER_DATA = f.readline()
    if USER_DATA == "":
        run_conf = subprocess.Popen([sys.executable,conf_exe], shell="true")
        run_conf.communicate()
    else:
        run_dylos = subprocess.Popen([sys.executable,dylos_reader])
        run_dylos.communicate()
