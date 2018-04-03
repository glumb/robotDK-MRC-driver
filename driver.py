#!/usr/local/bin/python

import serial
import time
import sys
import datetime
import select

MRCP_END_FRAME = '\r'
MRCP_START_FRAME = ':'

MRCP_COMMAND_QUEUE_IN = 'Q'
MRCP_COMMAND_EXECUTE = 'E'
MRCP_COMMAND_WRITE = 'W'

MRCP_GET_BUFFER_SIZE = 'B'

ROBOTCOM_CONNECTION_PROBLEMS = 1
ROBOTCOM_DISCONNECTED = 2
ROBOTCOM_NOT_CONNECTED = 3
ROBOTCOM_READY = 4
ROBOTCOM_WORKING = 5
ROBOTCOM_WAITING = 6


filename = 'log.txt'
logfile = open(filename, 'w', 1)  # line buffered

print("MRC remote")
print("use CONNECT <serialport> to open a connection")


def send_instruction(instruction):
    log('sending instruction: ' + MRCP_START_FRAME + MRCP_COMMAND_EXECUTE +
        instruction + MRCP_END_FRAME)
    ser.write(MRCP_START_FRAME + MRCP_COMMAND_EXECUTE +
              instruction + MRCP_END_FRAME)
    # ser.flush()


def log(line):
    ts = time.time()
    logfile.write(datetime.datetime.fromtimestamp(
        ts).strftime('%Y-%m-%d %H:%M:%S') + ' ' + line + '\n')


log('starting')


def print_message(message):
    print(message)
    log('T: ' + message)
    sys.stdout.flush()


def update_status(status):
    if status == ROBOTCOM_CONNECTION_PROBLEMS:
        print_message("SMS:Connection problems")
    elif status == ROBOTCOM_DISCONNECTED:
        print_message("SMS:Disconnected")  # red, same as "Disconnected"
    elif status == ROBOTCOM_NOT_CONNECTED:
        # this means that the host is not reachable
        print_message("SMS:Not connected")  # red, same as "Disconnected"
        # connection_retry_schedule()
    elif status == ROBOTCOM_READY:
        print_message("SMS:Ready")  # provokes green color
    elif status == ROBOTCOM_WORKING:
        print_message("SMS:Working...")  # provokes yellow color
    elif status == ROBOTCOM_WAITING:
        print_message("SMS:Waiting...")  # provokes cyan color
    else:
        print_message("SMS:Unknown status")


def format_number(string):
    return str(round(float(string), 5))


update_status(ROBOTCOM_WORKING)
connected = False


def readline(a_serial, eol=b'\r'):
    leneol = len(eol)
    line = bytearray()
    while True:
        c = a_serial.read(1)
        if c:
            line += c
            if line[-leneol:] == eol:
                break
        else:
            break
    return bytes(line)


while 1:
    # check if input is available - dont block
    if select.select([sys.stdin, ], [], [], 0.0)[0]:
        data = sys.stdin.readline()
        log('R: ' + data)
        commands = data[0:-1].split(' ')
        commands[0] = commands[0].strip()
        if connected is False:

            if commands[0] == 'CONNECT':
                log('connecting to ' + commands[1])
                connected = True
                ser = serial.Serial(commands[1], baudrate=9600, timeout=0.5)
                ser.setRTS(False)
                update_status(ROBOTCOM_READY)
                send_instruction('Q')
            else:
                print("use CONNECT <serialport> to open a connection")

        elif commands[0] == 'MOVJ':

            update_status(ROBOTCOM_WORKING)
            # velocity is hardcoded for now
            instruction = 'M00 V10 N42 '
            for i in range(0, 6):
                instruction += 'R' + str(i) + ' ' + \
                    format_number(commands[i + 1]) + ' '
            send_instruction(instruction)

        elif commands[0] == 'MOVL':

            update_status(ROBOTCOM_WORKING)
            # velocity is hardcoded for now
            instruction = 'M01 V20 N42 '
            for i in range(0, 6):
                instruction += 'R' + str(i) + ' ' + \
                    format_number(commands[i + 1]) + ' '
            send_instruction(instruction)

        elif commands[0] == 'MOVC':

            print('MOVC not implemented on MRC')

        elif commands[0] == 'PAUSE':

            send_instruction('N42 D ' + commands[1])

        elif commands[0] == 'SPEED':

            send_instruction('V ' + commands[1])

        elif commands[0] == 'CJNT':

            update_status(ROBOTCOM_WORKING)
            send_instruction('N42 R1 R2 R3 R4 R5 R6')
            time.sleep(.1)
            number = readline(ser).decode('ascii')  # instruction number
            log('received number: ' + number)
            mrcpr = readline(ser).decode('ascii')
            log('received angles: ' + mrcpr)

            # MRC outputs R<joint><angle>
            print_message('JNTS ' + ' '.join([s[5:]
                                              for s in mrcpr[5:].split('R')]))
            update_status(ROBOTCOM_READY)

        elif commands[0] == 'SETDO':

            send_instruction('N42 O' + commands[1] + ' ' + commands[2])

        elif commands[0] == 'WAITDI':

            send_instruction('N42 I' + commands[1] + ' ' + commands[2])

        else:

            send_instruction(' '.join(commands))

    sys.stdout.flush()
    if connected:
        # read response from MRC
        mrcpr = readline(ser).decode('ascii')
        if len(mrcpr) > 0:
            log('receiving: ' + mrcpr)
            # MRC sends N1<instruction number> to signal the instruction was executed
            if len(mrcpr) >= 5 and mrcpr[1] == 'N' and mrcpr[2:5] == '142':
                update_status(ROBOTCOM_READY)
