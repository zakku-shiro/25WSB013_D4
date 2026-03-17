import enum
import serial
import time

class Signals(enum.IntEnum):
    ZERO = 0
    ERROR = 1
    ACKNOWLEDGE = 2
    SOUND_DATA = 3
    LED_COMMAND = 4
    MOVE_COMMAND = 5

SYNC = b'\xBE\xEF'
MAX_PACKET_SIZE = 32

def send_packet(msg_type, payload = b''):
    length = len(payload)
    crc = msg_type ^ length

    for b in payload:
        crc ^= b

    packet = SYNC + bytes([msg_type, length]) + payload + bytes([crc])
    ser.write(packet)

def read_exact(size):
    data = ser.read(size)
    if len(data) != size:
        raise TimeoutError("Serial timeout")
    return data

def read_packet():
    while True:
        if ser.read(1) != SYNC[:1]:
            continue
        if ser.read(1) != SYNC[1:2]:
            continue

        header = read_exact(2)
        msg_type = header[0]
        length = header[1]

        if length > MAX_PACKET_SIZE:
            continue

        payload = read_exact(length)
        crc = read_exact(1)[0]

        check = msg_type ^ length
        for b in payload:
            check ^= b

        if check == crc:
            return msg_type, payload


# Serial Initialization
ser = serial.Serial("COM6", 500000, timeout=1)
# Reset Arduino cleanly
ser.setDTR(False)
time.sleep(1)
ser.reset_input_buffer()
ser.setDTR(True)
time.sleep(2)

while True:
    print("Start blinking")
    send_packet(Signals.LED_COMMAND, bytes([1]))

    while True:
        msg_type, _ = read_packet()
        if msg_type == Signals.ACKNOWLEDGE:
            print("Arduino ACK")
            break

    time.sleep(2)

    print("Stop blinking")
    send_packet(Signals.LED_COMMAND, bytes([0]))

    while True:
        msg_type, _ = read_packet()
        if msg_type == Signals.ACKNOWLEDGE:
            print("Arduino ACK")
            break

    time.sleep(2)