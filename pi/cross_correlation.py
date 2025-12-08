import serial
import numpy as np
import librosa as lb
import scipy


SERIAL_PORT = 'COM6'  #may have to change for the pi
BAUD_RATE = 500000
FRAME_SIZE = 6
DATA_BYTES = 4
NUM_MICS = 3
SAMPLE_RATE = 7800  # estimated sample rate


BUFFER_SIZE = 2048

mic_buffers = [[] for _ in range(NUM_MICS)]

buffer_ready = False

last_5_mic_values = [0,0,0,0,0]


crazy_frog,sr = lb.load("C:/Users/bruno/PyCharmMiscProject/Crazy Frog - Axel F.mp3",sr=SAMPLE_RATE)
#need to change file path for the pi

# --- Serial Port Setup ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()


def cross_correlate(buffers, crazy_frog):

    print("--- Cross Correlation Time ---")

    np_buffers = [np.array(b) for b in buffers]

    dc_fixed_buffers = [np.subtract(mic_buffers[0], np.mean(mic_buffers[0])),
                        np.subtract(mic_buffers[1], np.mean(mic_buffers[1])),
                        np.subtract(mic_buffers[2], np.mean(mic_buffers[2]))]

    normalised_buffers = [dc_fixed_buffers[0] / np.max(np.abs(dc_fixed_buffers[0])),
                          dc_fixed_buffers[1] / np.max(np.abs(dc_fixed_buffers[1])),
                          dc_fixed_buffers[2] / np.max(np.abs(dc_fixed_buffers[2]))]

    mic_max = [np.max(normalised_buffers[0]), np.max(normalised_buffers[1]), np.max(normalised_buffers[2])]
    mic_scores = np.zeros(3)

    mic_scores[0] = np.max(np.abs(scipy.signal.correlate(crazy_frog, normalised_buffers[0], mode='valid')))
    mic_scores[1] = np.max(np.abs(scipy.signal.correlate(crazy_frog, normalised_buffers[1], mode='valid')))
    mic_scores[2] = np.max(np.abs(scipy.signal.correlate(crazy_frog, normalised_buffers[2], mode='valid')))

    print(f"Mic values: {mic_max}")
    print(f"Correlation max values: {mic_scores}")
    print(f"Mic {np.argmax(mic_scores) + 1} is the craziest frog.")
    print("-" * 40)

    for b in buffers:
        b.clear()

    return np.argmax(mic_scores)+1 #returns mic with the loudest crazy frog
# --- Main Loop ---

#global buffer_ready

while True:
    try:
        #check if there is data on the serial monitor
        if ser.in_waiting > 0:
            first_byte = ser.read_until(b'<', size=100)  # Read up to 100 bytes until marker
            if not first_byte.endswith(b'<'):
                continue  # Didn't find start marker, keep trying

            packed_data = ser.read(DATA_BYTES)
            if len(packed_data) < DATA_BYTES:
                # Not enough data, discard this frame and continue
                continue

            end_byte = ser.read(1)
            if end_byte != b'>':
                # End marker missing, synchronization lost! Discard and resync.
                print("Sync lost! Resyncing...")
                continue

            m1 = packed_data[0] << 2 | (packed_data[1] & 0xF0) >> 6
            m2 = (packed_data[1] & 0x3F) << 4 | (packed_data[2] & 0xF0) >> 4
            m3 = (packed_data[2] & 0x0F) << 6 | (packed_data[3] & 0x3F)

            if m1 != 0 and m2 != 0 and m3 != 0:
                mic_buffers[0].append(m1)
                mic_buffers[1].append(m2)
                mic_buffers[2].append(m3)

            # 6. Check if buffers are full
            if len(mic_buffers[0]) >= BUFFER_SIZE:


                current_mic_value = cross_correlate(mic_buffers, crazy_frog)

                last_5_mic_values.pop(0)
                last_5_mic_values.append(int(current_mic_value))

                count = np.array([0,0,0])

                for i in last_5_mic_values:
                    match i:
                        case 1:
                            count[0] += 1
                        case 2:
                            count[1] += 1
                        case 3:
                            count[2] += 1
                        case _:
                            print("something went wrong")

                loudest_mic = np.argmax(count) + 1 #remove 0 indexing

                #print("The loudest mic is: ", loudest_mic)


    except serial.SerialTimeoutException:
        pass  # Keep trying
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        ser.close()
        break

