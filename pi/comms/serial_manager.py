import queue
import struct

import serial
import time
import os
import dotenv

from comms.protocol import Signals

dotenv.load_dotenv()

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM6")
BAUD_RATE = 500000

SYNC = b'\xBE\xEF'
MAX_PACKET_SIZE = 32

def send_packet(ser, msg_type, payload=b''):
    length = len(payload)
    crc = msg_type ^ length

    for b in payload:
        crc ^= b

    packet = SYNC + bytes([msg_type, length]) + payload + bytes([crc])
    ser.write(packet)


def read_exact(ser, size):
    data = ser.read(size)
    if len(data) != size:
        raise TimeoutError("Serial timeout")
    return data


def read_packet(ser):
    while True:
        if ser.read(1) != SYNC[:1]:
            continue
        if ser.read(1) != SYNC[1:2]:
            continue

        header = read_exact(ser, 2)
        msg_type = header[0]
        length = header[1]

        if length > MAX_PACKET_SIZE:
            continue

        payload = read_exact(ser, length)
        crc = read_exact(ser, 1)[0]

        check = msg_type ^ length
        for b in payload:
            check ^= b

        if check == crc:
            return msg_type, payload

def encode_motor_command(left_speed, right_speed):
    """
    Converts signed motor speeds into:
    [dir, speed, dir, speed]

    dir:   0 = forward, 1 = reverse
    speed: 0–255
    """

    # Clamp values safely
    left_speed = max(-255, min(255, left_speed))
    right_speed = max(-255, min(255, right_speed))

    left_dir = 0 if left_speed >= 0 else 1
    right_dir = 0 if right_speed >= 0 else 1

    return bytes([
        left_dir,
        abs(left_speed),
        right_dir,
        abs(right_speed)
    ])

def serial_process(ultrasonic_q, motor_q, sound_q):
    """
    Receives motor commands from controller:
    {
        "left": int (-255 to 255),
        "right": int (-255 to 255)
    }
    """
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)

    # Reset Arduino cleanly
    ser.setDTR(False)
    time.sleep(1)
    ser.reset_input_buffer()
    ser.setDTR(True)
    time.sleep(2)

    send_interval = 0.02  # 50Hz update rate

    while True:
        try:
            cmd = motor_q.get(timeout=0.1)
        except queue.Empty:
            continue

        payload = encode_motor_command(
            cmd["left"],
            cmd["right"]
        )

        send_packet(ser, Signals.MOVE_COMMAND, payload)
        last_send_time = time.time()
        #print(f"[SERIAL] Sent L:{cmd['left']} R:{cmd['right']}")

        while ser.in_waiting:
            msg_type, payload = read_packet(ser)

            match msg_type:
                case Signals.ACKNOWLEDGE:
                    pass
                case Signals.ERROR:
                    print(f"[Arduino ERROR]: {payload}")
                case Signals.SOUND_DATA:
                    # Todo: Add sound data to queue here
                    pass
                case Signals.ULTRASONIC_DATA:
                    data = struct.unpack("<f", payload)[0]
                    ultrasonic_q.put(data)

        # Maintain consistent send rate
        elapsed = time.time() - last_send_time
        if elapsed < send_interval:
            time.sleep(send_interval - elapsed)
