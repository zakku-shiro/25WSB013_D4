import queue
import struct
import serial
import time
import os
import dotenv

from comms.protocol import Signals

dotenv.load_dotenv()

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM6")
BAUD_RATE   = 500000

SYNC            = b'\xBE\xEF'
MAX_PACKET_SIZE = 32

# Motor command is re-sent at least this often to prevent watchdog trips
# when the controller is in a stopped state and producing commands slowly.
KEEPALIVE_INTERVAL = 0.2  # seconds

# Maximum inbound packets processed per iteration to prevent sound data
# flooding from starving the motor command send.
MAX_INCOMING_PER_ITER = 8


def send_packet(ser, msg_type, payload=b''):
    length = len(payload)
    crc    = msg_type ^ length

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

        header   = read_exact(ser, 2)
        msg_type = header[0]
        length   = header[1]

        if length > MAX_PACKET_SIZE:
            continue

        payload = read_exact(ser, length)
        crc     = read_exact(ser, 1)[0]

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
    left_speed  = max(-255, min(255, left_speed))
    right_speed = max(-255, min(255, right_speed))

    left_dir  = 0 if left_speed  >= 0 else 1
    right_dir = 0 if right_speed >= 0 else 1

    return bytes([
        left_dir,
        abs(left_speed),
        right_dir,
        abs(right_speed)
    ])


def serial_process(init_event, mode_settings, ultrasonic_q, motor_q, sound_in_q):
    ser = None
    while ser is None:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        except serial.SerialException as e:
            print(f"[SERIAL] Waiting for {SERIAL_PORT}: {e}")
            time.sleep(1.0)


    # Reset Arduino cleanly
    ser.setDTR(False)
    time.sleep(1)
    ser.reset_input_buffer()
    ser.setDTR(True)
    time.sleep(2)

    # Block until the Arduino sends switch state so mode_settings is populated
    # before init_event unblocks the other processes.
    while True:
        if ser.in_waiting:
            msg_type, payload = read_packet(ser)

            if msg_type == Signals.SWITCH_DATA:
                mode_settings["demo_enabled"] = bool(payload[0])
                mode_settings["demo_type"]    = bool(payload[1])
                send_packet(ser, Signals.ACKNOWLEDGE)
                break

    cmd            = {"left": 0, "right": 0}
    last_send_time = 0

    init_event.set()

    while True:
        # Keepalive
        try:
            cmd = motor_q.get(timeout=0.05)
        except queue.Empty:
            pass

        now = time.perf_counter()
        if now - last_send_time >= KEEPALIVE_INTERVAL:
            # Clear buffer to ensure room
            while ser.in_waiting:
                _, _ = read_packet(ser)                
            
            payload = encode_motor_command(cmd["left"], cmd["right"])
            send_packet(ser, Signals.MOVE_COMMAND, payload)
            print(f"[SERIAL:{now}] -> L,R:{cmd['left']},{cmd['right']}")
            last_send_time = now

        # Cap inbound processing
        for _ in range(MAX_INCOMING_PER_ITER):
            if not ser.in_waiting:
                break

            msg_type, payload = read_packet(ser)

            match msg_type:
                case Signals.ACKNOWLEDGE:
                    pass

                case Signals.ERROR:
                    print(f"[Arduino ERROR]: {payload}")

                case Signals.SOUND_DATA:
                    # Single frame: 3×10-bit ADC values packed into 4 bytes
                    if len(payload) >= 4:
                        d  = payload
                        m0 = ((d[0] << 2) | (d[1] >> 6))             & 0x3FF
                        m1 = (((d[1] & 0x3F) << 4) | (d[2] >> 4))   & 0x3FF
                        m2 = (((d[2] & 0x0F) << 6) | (d[3] & 0x3F)) & 0x3FF
                        sound_in_q.put((m0, m1, m2))

                case Signals.ULTRASONIC_DATA:
                    data = struct.unpack("<f", payload)[0]
                    ultrasonic_q.put(data)
