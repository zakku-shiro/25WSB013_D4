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


def serial_process(init_event, mode_settings, ultrasonic_q, motor_q, sound_in_q):
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

    # Wait for Arduino to send us the status of the switches to choose a mode
    while True:
        if ser.in_waiting:
            msg_type, payload = read_packet(ser)

            if msg_type == Signals.SWITCH_DATA:
                mode_settings["demo_enabled"], mode_settings["demo_type"] = bool(payload[0]), bool(payload[1])
                send_packet(ser, Signals.ACKNOWLEDGE)
                break

    cmd = {"left": 0, "right": 0}

    # Let other threads know we are ready
    init_event.set()

    while True:
        try:
            cmd = motor_q.get(timeout=0.1)
            # print(f"[SERIAL] Sent L:{cmd['left']} R:{cmd['right']}")
        except queue.Empty:
            pass

        payload = encode_motor_command(
            cmd["left"],
            cmd["right"]
        )

        send_packet(ser, Signals.MOVE_COMMAND, payload)

        while ser.in_waiting:
            msg_type, payload = read_packet(ser)

            match msg_type:
                case Signals.ACKNOWLEDGE:
                    pass
                case Signals.ERROR:
                    print(f"[Arduino ERROR]: {payload}")
                case Signals.SOUND_DATA:
                    # Unpacking
                    m1 = (payload[0] << 2) | ((payload[1] & 0xF0) >> 6)
                    m2 = ((payload[1] & 0x3F) << 4) | ((payload[2] & 0xF0) >> 4)
                    m3 = ((payload[2] & 0x0F) << 6) | (payload[3] & 0x3F)
                    sound_in_q.put((m1, m2, m3))
                case Signals.ULTRASONIC_DATA:
                    data = struct.unpack("<f", payload)[0]
                    ultrasonic_q.put(data)