
import logging
logging.basicConfig(level= logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level= logging.WARNING,format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level= logging.ERROR,format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level= logging.CRITICAL,format='%(asctime)s - %(levelname)s - %(message)s')


def printInfoMsg(msg):
    logging.info(msg)

def printWarningMsg(msg):
    logging.warning(msg)

def printErrorMsg(msg):
    logging.error(msg)

def printCriticalMsg(msg):
    logging.critical(msg)



global SERIAL_CONNECT_PERIOED
global SLEEP_BETWEEN_READS
global MINUTE

FIRST_ERROR_ID = 1
FIRST_ERROR_MSG = "NO_AVAILABLE_DATA"
SECOND_ERROR_ID = 2
SECOND_ERROR_MSG = "INVALID_DATA"
ERROR_TABLE = "DYLOS_FAILURE"
MAIN_TABLE = "DYLOS_READING"
SERIAL_CONNECT_PERIOD = 10
SLEEP_BETWEEN_READS = 40
MINUTE = 60
DAY = 24
FIRST_REBOOT_TIME = 3
SEND_MAIL_PERIOD = 13
CONNECTION_TIMEOUT = 5
RESTORE_FILE = '/home/pi/Dylos/restore.txt'
REBOOT_FLAG = '/home/pi/Dylos/rebootFlag'
