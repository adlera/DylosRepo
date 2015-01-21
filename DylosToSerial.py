__author__ = 'fassler'

import serial
from serial import tools
from serial.tools import list_ports
import time
import csv
import datetime
import os
import pickle
import mysql.connector 


def open_serial_connection(serial_port=str):
    """
    configure and open the serial connection.
    :param serial_port: hardcoded by default to ttyUSB0.
    :return:none
    """
    global ser
    try:
        ser = serial.Serial(
        serial_port, baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_TWO,
        bytesize=serial.EIGHTBITS,
        writeTimeout=0,
        timeout=10)

        ''' test
         ser = serial.Serial(SENSOR_DATA[serial_connection])
         '''
        print("The serial connection is now open")
    except(Exception):
        ser = False
        print("The serial connection has failed")


def find_available_serial_ports():
    try:
        portname = serial.tools.list_ports.comports()
        #print("the port name is: " + portname)
        return portname[0][0]
    except(Exception):
        print("no serial port available")
        portname = []
        return portname


def request_data():
    """
    calls write_data and then read a line from the serial port.
    strip the data from \r\n and split it by the ","
    :return: datatocsv - the value as a list

    """
    if mode == "test":  # test
        timestamp = datetime.datetime.now()
        timestamp = "'" + timestamp.strftime('%Y-%m-%d %H:%M:%S') + "'"
        datatocsv = [3,timestamp,7,7]
        return datatocsv
    else:  # test
        try:
            write_data()
            time.sleep(10)
            line = ser.readline()
            strline = str(line)
            strline.strip("\r\n")
            print("the data is: " + strline)
            datatocsv = strline.split(",")  # only for dylos, check for other sensors
            if len(datatocsv) > 1:
                datatocsv[1] = datatocsv[1].strip("\r\n")
            #ser.close()
            return datatocsv

        except(Exception):
            datatocsv = []
            print(Exception)
            return datatocsv

def write_data():
    """
    write \r\n to serial port

    """
    try:
        if ser.isOpen():
            print("serial is open")
            ser.write("\r\n")
    except():
        print ("serial is not open")


def create_file(folder):
    """
    create a file named "DylosId+Date" in the configured folder (default - /home/pi/Dylosdata/).
    if the folder does not exist, create one.
    After opening the file asian the headers: Dylos ID,Location,Date,Pm 0.5-2.5,Pm > 2.5
    If the file already exists, doesn't create a new one.
    :return: file name
    """

    day = datetime.datetime.now()
    date = day.date()
    ''' checks if the folder exists. if not, create one'''
    if not os.path.exists(folder):
        print"the folder doesnt exists"
        os.makedirs(folder)
    os.chdir(folder)
    ''' create a new csv file and append column header'''
    filename = str(USER_DATA["ID"]) + "_" + str(date) + ".csv"

    if os.path.isfile(filename):  # the file already exists, only print "append new data"
        f = open(filename, 'a')
        print("opened the file and append new data")
    else:  # there is no file that name, create one, and write the columns headers
        f = open(filename, 'w')
        print("create a new file, and write column headers")
        f.write(SENSOR_DATA["sensor_values"] + "\r\n")
    f.close()
    
    print('created file named ' + str(filename))
    return filename


def write_data_to_csv(filename, dylos_data):
    """
    get the csv file name and serial data from Dylos and write it to the file.
    Add to every line the ID, location and time.
    if there is no serial connection write "error" instead of data.
    if there is a serial connection, but the dylos is turned off/disconnected/some other problem,
    write "none" instead of data.
    """
    os.chdir(USER_DATA["folder"])
    f = open(filename, 'a')
    print("open the file")
    timestamp = datetime.datetime.now()
    timestamp = "'" + timestamp.strftime('%Y-%m-%d %H:%M:%S') + "'"
    if len(dylos_data) >= 2:  # the data is fine, write the dylos data
        newdata = [2, timestamp, dylos_data[0], dylos_data[1]]
	#newdata = [USER_DATA["ID"],timestamp , dylos_data[0], dylos_data[1]]
        a = csv.writer(f)
        a.writerows([newdata])
        f.close()
    elif dylos_data == ['']:  # the connection was establish but there is no data reading. print none.
        newdata = [2, timestamp, 0, 0]
	#newdata = [USER_DATA["ID"], timestamp, "none", "none"]
        a = csv.writer(f)
        a.writerows([newdata])
        print("the data was null!, Dylos is disconnected or off")
        f.close()
    else:  # there is no connection / other problem. print error.
        newdata = [2, timestamp, -1, -1]
        #newdata = [USER_DATA["ID"],timestamp, "error", "error"]
        a = csv.writer(f)
        a.writerows([newdata])
        print("there was an error!, maybe the cable is unplugged")
        f.close()
    print("Wrote a row to csv")
    return newdata


def import_configuration(file_name):
    """
    import configuration from file using pickle.
    file default location is 'y/home/pi/Desktop/DlosConf.txt' /"SensorBasicConf.txt"
    if the file is empty, assign default values to user data
    you need to specify the file name you want to import from
    :rtype : dict
    :return: user data
    """
    if mode == 'test':
        conf_location = '/Users/fassler/PycharmProjects/Dylos_Via_RaspberryPi_connction/' + str(file_name) + ".txt"
    else:
        conf_location = '/home/pi/Dylos/' + str(file_name) + ".txt"

    if os.path.isfile(conf_location):  # check if the file exists
        with open(conf_location, 'rb') as handle:
            user_data = pickle.loads(handle.read())  # unpickle the data from the file.
    else:
        user_data = []

    return user_data


#AS remove file that is older than daysAgo
def removeOldFile(daysAgo,today):
    oldDate = today - datetime.timedelta(daysAgo)
    oldDateFilePath = USER_DATA["folder"] + "/" + str(USER_DATA["ID"]) + "_" + str(oldDate) + ".csv"
    if os.path.isfile(str(oldDateFilePath)):    
        print "Remove old csv file from date : " + str(oldDate)
        os.remove(str(oldDateFilePath))
    


#AS function that send data from temporary list to SQL server
def sendData(tmpList,config):
    startTime = datetime.datetime.now()
    startTime = startTime.second
    midTime = datetime.datetime.now()
    while len(tmpList) != 0 and ((midTime.second - startTime) % 60) < 35 :
        try:
           cnx = mysql.connector.connect(**config)
        except mysql.connector.Error as err:
            print(err)
            midTime = datetime.datetime.now()
            continue
        else:
            cursor = cnx.cursor()
            tmpData = tmpList.pop(0)
            dataString = ',' .join(map(str,tmpData))
            insert = "INSERT INTO try VALUES(" + dataString + ")"
            print insert
            try:
                cursor.execute(insert)
                cnx.commit()
            except (Exception):
                print tmpList
                tmpList.insert(0,tmpData)
                print tmpList
                print "Shir gonna Crazy"
            # if INSERT failed - return data to tmpList and try again
            midTime = datetime.datetime.now()
        cnx.close()
    timeToSleep = 40 - ((midTime.second - startTime) % 60)
    timeToSleep = float(timeToSleep)
    time.sleep(timeToSleep) 

'''
now - the main function!
'''
try:
    config = {
      'user': 'sql364564',
      'password': 'aL8%gU2!',
      'host': 'sql3.freemysqlhosting.net',
      'database': 'sql364564',
      'raise_on_warnings': True,
    }
    mode = "else"  # if "test", run without sensor (dylos)
    global USER_DATA, SENSOR_DATA

    serialPortName = "/dev/ttyUSB0"  # RaspberryPi default serial connection name
    print("try to find serial port")
    serialPortName =find_available_serial_ports()
    ser = False
    USER_DATA = import_configuration("DylosConf")
    SENSOR_DATA = import_configuration("SensorBasicConf")
    updatePeriodTime = 1

    if mode != "test":  # if not test
        if serialPortName != []:
            print("start: try to open serial connection for the first time")
            open_serial_connection(serialPortName)

            '''if there is no serial connection, sleep and then try again to open connection.'''
        while ser is False:
            i = 10
            print("didn't worked: will try to open the serial connection again in " + str(i) + " sec")
            time.sleep(i)
            i += 10
            if i > 60:
                i = 10
            serialPortName = find_available_serial_ports()
            open_serial_connection(serialPortName)


    # create a csv file
    today = datetime.datetime.now()
    file_date = today.day

    print("file date " + str(file_date))
    print(USER_DATA["folder"])
    FileName = create_file(USER_DATA["folder"])
    tmpList = [] #AS tmp list for saving data until send to SQL server
    # the main loop: request data and assign it to the file, then sleep for 40 sec (total 50 sec in every cycle)
    # if something went wrong the app will crash
    while True:  # create a new file every day
        today = datetime.datetime.now()
        todayDate = today.date()
        removeOldFile(7,todayDate)
        if file_date != today.today().day : 
            FileName = create_file(USER_DATA["folder"])
            file_date = today.day
            removeOldFile(7,today.date())
        if serialPortName != find_available_serial_ports():
            serialPortName = find_available_serial_ports()
            open_serial_connection(serialPortName)
        data = request_data()
        print ("the data is ", data)
        serverData = write_data_to_csv(FileName,data)
        tmpList.append(serverData) #AS write each data to line on the tmpFile
        if len(tmpList) >= updatePeriodTime: #AS after Constant (15) number of data reads, start to send to the SQL server
            sendData(tmpList,config) #AS send the data on the tmpFile to the SQL server
        else:
            time.sleep(40)

except (Exception):
        print(Exception)
