import serial
from serial import tools
from serial.tools import list_ports
from email.mime.text import MIMEText
import sys
import time
import csv
import datetime
import os
import re
import pickle
import mysql.connector 
import smtplib
import setting as s

def open_serial_connection(serial_port=str):
    """
    configure and open the serial connection.
    """
    global ser
    try:   
        ser = serial.Serial(
        serial_port, baudrate=SENSOR_DATA["baudrate"],
        parity=SENSOR_DATA["parity"],
        stopbits=SENSOR_DATA["stopbits"],
        bytesize=SENSOR_DATA["bytesize"],
        writeTimeout=SENSOR_DATA["writeTimeout"],
        timeout=SENSOR_DATA["timeout"]) 
        s.printInfoMsg("The serial connection is now open")
    except(Exception):
        ser = False
        s.printErrorMsg("The serial connection has failed")


def find_available_serial_ports():
    try:
        portList = serial.tools.list_ports.comports()
        for port in portList:
            if USER_DATA["sensor serial name"] in port[1]:
                 return port[0]
        raise Execption()
    except(Exception):
        s.printErrorMsg("No serial port available")
        portname = []
        return portname


def request_data():
    """
    calls write_data and then read a line from the serial port.
    strip the data from \r\n and split it by the ","
    :return: datatocsv - the value as a list

    """
    try:
        write_data()
        time.sleep(s.SERIAL_CONNECT_PERIOD)
        line = ser.readline()
        strline = str(line)
        strline.strip("\r\n")
        s.printInfoMsg("The data is: " + strline)
        datatocsv = strline.split(",")  # only for dylos, check for other sensors
        if len(datatocsv) > 1:
            datatocsv[1] = datatocsv[1].strip("\r\n")
        return datatocsv

    except(Exception):
        datatocsv = []
        return datatocsv

def write_data():
    """
    write \r\n to serial port
    """
    try:
        if ser.isOpen():
            s.printInfoMsg("Serial is open")
            ser.write("\r\n")
    except():
        s.printErrorMsg("Serial is not open")


def create_file(folder,date):
    """
    create a file named "DylosId_Date" in the backup folder (default - /home/pi/Dylos/BackUpFiles).
    if the folder does not exist, create one.
    After opening the file assign the headers: Dylos ID,Date,Pm 0.5-2.5,Pm > 2.5
    If the file already exists, doesn't create a new one.
    :return: file name
    """

    ''' checks if the folder exists. if not, create one'''
    if not os.path.exists(folder):
        s.printWarningMsg("the folder doesnt exists")
        os.makedirs(folder)
    os.chdir(folder)
    ''' create a new csv file and append column header'''
    filename = str(USER_DATA["ID"]) + "_" + str(date) + ".csv"
    if os.path.isfile(filename):  # the file already exists, only print "append new data"
        s.printInfoMsg("Trying to create new file, file already exists")
    else:  # there is no file that name, create one, and write the columns headers
        f = open(filename, 'w')
        s.printInfoMsg("Create a new file and write column headers")
        f.write(SENSOR_DATA["sensor_values"] + "\r\n")
        f.close()
    
    s.printInfoMsg('Created file named ' + str(filename))
    return filename


def write_data_to_csv(filename, dylos_data):
    """
    get the csv file name and serial data from Dylos and write it to the file.
    Add to every line the ID and time.
    if there is no serial connection write "error" instead of data.
    if there is a serial connection, but the dylos is turned off/disconnected/some other problem,
    write "none" instead of data.
    """
    f = open(filename, 'a')
    s.printInfoMsg("open the file")
    timestamp = datetime.datetime.now()
    timestamp = "'" + timestamp.strftime('%Y-%m-%d %H:%M:%S') + "'"
    if len(dylos_data) >= 2 and dylos_data[0].isdigit() and dylos_data[1].isdigit() :  # the data is fine, write the dylos data
        newdata = [USER_DATA["ID"], timestamp, dylos_data[0], dylos_data[1]]        
    elif dylos_data == ['']:  # the connection was establish but there is no data reading. print none.
        newdata = [USER_DATA["ID"], timestamp, "none", "none"]
        s.printErrorMsg("the data was null!, Dylos is disconnected or off")
    else:  # there is no connection / other problem. print error.
        newdata = [USER_DATA["ID"],timestamp, "error", "error"]
        s.printErrorMsg("there was an error!, maybe the cable is unplugged")
    a = csv.writer(f)
    a.writerows([newdata])
    f.close()
    s.printInfoMsg("Wrote a row to csv")
    return newdata


def import_configuration(file_name):
    """
    import configuration from file using pickle.
    file default location is '/home/pi/Dylos/'
    if the file is empty exit the program
    :return: conf data
    """
    conf_location = '/home/pi/Dylos/' + str(file_name) + ".txt"

    if os.path.isfile(conf_location):  # check if the file exists
        with open(conf_location, 'rb') as handle:
            conf_data = pickle.loads(handle.read())  # unpickle the data from the file.
    else:
        s.printCriticalMsg("missing configuration file " + conf_location)
        sys.exit()

    return conf_data


#AS remove file that is older than daysAgo
def removeOldFiles(backupFolder,daysAgo):
    os.system("find " + backupFolder + " -mtime +" + daysAgo + " -exec sudo rm {} \;")    
    s.printInfoMsg("Remove old csv files")
    
def restoreData():
    if os.path.exists(s.RESTORE_FILE):
        with open(s.RESTORE_FILE,'r') as f:
            restore = [line.rstrip('\n') for line in f]
            print restore
        f.close()
        os.system('sudo rm ' + s.RESTORE_FILE)
    else:
        restore = []
    return restore    

def storeData(list):
    with open(s.RESTORE_FILE,'w') as f:
        for element in list:
            elementStr = ',' .join(map(str,element))
            print elementStr
            f.write(elementStr + '\n')
    f.close()
       

def createAndSendQuery(tmpList):
    global CNX
    cursor = CNX.cursor()
    #init lists
    backupData = [] #backup the data in case of failure to send it 
    readerData = [] #contains the valid data
    failureData = [] #contains the invalid data
    #every query will contains "UPDATE_TIME" data lines or the current size of the data list
    size = min(len(tmpList),USER_DATA["update period"])
    for x in range(0,size):
        tmpData = tmpList.pop(0)
        sendData = tmpData[:]
        backupData.append(tmpData)
        #mark that's this data line is a valid line
        if sendData[len(sendData)-1].isdigit() :
            table = s.MAIN_TABLE
        #mark that's this data line is empty - meaning no available data
        elif sendData[len(sendData)-1] == "none" :
            sendData[2] = s.FIRST_ERROR_ID
            sendData[3] = "'" + s.FIRST_ERROR_MSG +  "'"
            table = "DYLOS_FAILURE"
        #mark that's this data line is an invalid line
        else: #AS tmpData[len(sendData)-1] == "error"
            sendData[2] = s.SECOND_ERROR_ID
            sendData[3] = "'" + s.SECOND_ERROR_MSG + "'"
            table = s.ERROR_TABLE
        dataString = "(" + ',' .join(map(str,sendData)) + ")"
        #insert the data line to the appropriate list
        if table == s.MAIN_TABLE :
            readerData.append(dataString)
        else:  
            failureData.append(dataString)
    #creates the query and sends it
    try:
        if len(readerData) > 0 :
            insertReader = "INSERT INTO " + s.MAIN_TABLE + " VALUES " + ',' .join(map(str,readerData))
            cursor.execute(insertReader)
        if len(failureData) > 0 :
            insertFailure = "INSERT INTO " + s.ERROR_TABLE + " VALUES " + ',' .join(map(str,failureData))
            cursor.execute(insertFailure)
        CNX.commit()
    except (Exception):
        # if INSERT failed - return data to tmpList and try again
        s.printErrorMsg("Failed to send a qeury")
        tmpList = backupData + tmpList
    return datetime.datetime.now()

def handleNoConnection(tmpList):
    global DISCONNECT_TIME,SEND_MAIL
    res = os.system("ping google.com -c 1")
    if res != 0:
        SEND_MAIL = None
        if DISCONNECT_TIME is None:
            DISCONNECT_TIME = datetime.datetime.now()
        else:
           ALREADY_DISCONNECT = (datetime.datetime.now().hour - DISCONNECT_TIME.hour) % s.DAY
           if ALREADY_DISCONNECT == 0 and os.path.exists(s.REBOOT_FLAG):
               storeData(tmpList)     
               os.system('sudo reboot')
           elif ALREADY_DISCONNECT >= s.FIRST_REBOOT_TIME: #first reboot ,due to long disconnect, after 3 hours. the next reboot will be every 24 hours
               open(s.REBOOT_FLAG,'w') #will be removed only when the configuration will be changed
               storeData(tmpList)
               os.system('sudo reboot')
        s.printWarningMsg("No Internet connection")
        connectToInternet()
    else:
        DISCONNECT_TIME = None #There is an internet connection
        if SEND_MAIL is None: #send mail for the first time
            SEND_MAIL = datetime.datetime.now().hour
        ALREADY_SENT = (datetime.datetime.now().hour - SEND_MAIL) % s.SEND_MAIL_PERIOD #the next mail will be send every 12 hours
        if ALREADY_SENT == 0:
            sendMail()
            s.printWarningMsg("Mail sent to admin - SQL server doesn't responding")
            SEND_MAIL = SEND_MAIL + 1 #in order to avoid sending mail every minute in this hour.
    return res


def connectToServer(config,tmpList):
    global CNX, DISCONNECT_TIME,SEND_MAIL
    res = "Connect"
    try:
        CNX = mysql.connector.connect(**config)
        if not CNX.is_connected():
            res = handleNoConnection(tmpList)    
        else:
            SEND_MAIL = None
            DISCONNECT_TIME = None
    except mysql.connector.Error as err:
        res = handleNoConnection(tmpList)    
    return res

#AS function that send data from temporary list to SQL server
def sendData(tmpList,config):
    global CNX
    #start counting the time of the send process
    startTime = datetime.datetime.now()  
    midTime = datetime.datetime.now()
    #get in the while loop only if there is data to send and available time
    while len(tmpList) != 0 and ((midTime.second - startTime.second) % s.MINUTE) < (s.SLEEP_BETWEEN_READS - s.CONNECTION_TIMEOUT) :
        #checking if there is a connection to the SQL server, if not try again
      	if CNX is None or not CNX.is_connected():
            if (connectToServer(config,tmpList) != "Connect"):
                break
            midTime = datetime.datetime.now()
      	    continue
        else: #there is a connection to the SQL server
      	    midTime = createAndSendQuery(tmpList)
    if not CNX is None:
        CNX.close() 
    #sleep the left time until the period time is passed
    timeToSleep = s.SLEEP_BETWEEN_READS - ((midTime.second - startTime.second) % s.MINUTE)
    timeToSleep = float(timeToSleep)
    time.sleep(timeToSleep) 



def sendMail():
    server = smtplib.SMTP("smtp.gmail.com",587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('dylosreader@gmail.com','dylosreader1')
    msg = MIMEText('Attention Please - There is a problem with the SQL server: not responding, please fix it. sent by sensor (Type): ' + USER_DATA["sensor type"] + ' (ID): ' + USER_DATA["ID"])
    msg['Subject'] = 'Sensor Warning'
    msg['From'] = 'dylosreader@gmail.com'
    msg['To'] = USER_DATA["mail"]
    server.sendmail('dylosreader@gmail.com',USER_DATA["mail"],msg.as_string())
    

def connectToInternet():
    s.printInfoMsg("Connecting To Internet")
    if USER_DATA["modem"] != "other":
        os.system("sudo usb_modeswitch -c /etc/usb_modeswitch.conf")
        time.sleep(3)
    os.system("sudo wvdial 3gconnect &")
        



#now - the main function!

try: 
    global USER_DATA, SENSOR_DATA, DISCONNECT_TIME, SEND_MAIL, CNX
    time.sleep(10)
    CNX = None
    SEND_MAIL = None
    DISCONNECT_TIME = None
    USER_DATA = import_configuration("DylosConf")
    SENSOR_DATA = import_configuration("SensorBasicConf")
    SERVER_CONF = import_configuration("ServerConf")
    s.printInfoMsg("Trying to find serial port")
    serialPortName = find_available_serial_ports()
    ser = False
    config = {
       'user': SERVER_CONF["user"],
       'password': SERVER_CONF["password"],
       'host': SERVER_CONF["host"],
       'database': SERVER_CONF["database"],
       'raise_on_warnings': True,
       'connection_timeout': s.CONNECTION_TIMEOUT
    }
    connectToInternet()
    if serialPortName != []:
        s.printInfoMsg("Start: Trying to open serial connection for the first time")
        open_serial_connection(serialPortName)
        #if there is no serial connection, sleep and then try again to open connection.
    while ser is False:
        i = s.SERIAL_CONNECT_PERIOD
        s.printWarningMsg("Didn't worked: will try to open the serial connection again in " + str(i) + " sec")
        time.sleep(i)
        i += s.SERIAL_CONNECT_PERIOD
        if i > s.MINUTE:
            i = s.SERIAL_CONNECT_PERIOD
        serialPortName = find_available_serial_ports()
        open_serial_connection(serialPortName)


    # create a csv file
    today = datetime.datetime.now()
    file_date = today.day
    todayDate = today.date()
 
    s.printInfoMsg("file date " + str(todayDate))
    s.printInfoMsg(USER_DATA["backup folder"])
    FileName = create_file(USER_DATA["backup folder"],todayDate)
    tmpList = restoreData() #AS temp list for saving data until send to it to the SQL server
    # the main loop: request data and assign it to the file, then sleep for 40 sec (total 50 sec in every cycle)
    # if something went wrong the app will crash
    while True:  # create a new file every day
        today = datetime.datetime.now()
        todayDate = today.date()
        if file_date != today.day : 
            FileName = create_file(USER_DATA["backup folder"],todayDate)
            file_date = today.day
            removeOldFiles(USER_DATA["backup folder"],USER_DATA["save period"])
        if serialPortName != find_available_serial_ports():
            serialPortName = find_available_serial_ports()
            open_serial_connection(serialPortName)
        data = request_data()
        serverData = write_data_to_csv(FileName,data)
        tmpList.append(serverData) #AS adding each data line to the temp list
        if len(tmpList) >= int(USER_DATA["update period"]): #AS after Constant (15) number of data reads, starts to send them to the SQL server
            sendData(tmpList,config) #AS sends the data lines to the SQL server
        else:
            time.sleep(s.SLEEP_BETWEEN_READS)

except (Exception):
        s.printCriticalMsg("Something went wrong - please contact the developers")
