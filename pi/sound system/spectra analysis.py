import scipy.signal as sg
import serial
import numpy as np
import librosa as lb
import traceback
import scipy
#from scipy import signal
import matplotlib.pyplot as plt

import time
start_time = None

SERIAL_PORT = 'COM6'  #may have to change for the pi
BAUD_RATE = 500000
FRAME_SIZE = 6
DATA_BYTES = 4
NUM_MICS = 3
SAMPLE_RATE = 8400  # estimated sample rate

BUFFER_SIZE = 1024

mic_data = np.zeros((NUM_MICS, BUFFER_SIZE), dtype=np.uint16)
data_ptr = 0

last_5_mic_values = [0,0,0,0,0]

crazy_frog1,sr = lb.load("C:/Users/bruno/PyCharmMiscProject/Crazy Frog - Axel F.mp3",sr=SAMPLE_RATE,duration=1.5,offset=30)

#need to change file path for the pi
f, s, crazy_stft = sg.stft(crazy_frog1, fs=SAMPLE_RATE, nperseg=512, noverlap=0)
crazy_stft1 = crazy_stft[40:400, :]

median_stft_ref = np.median(np.abs(crazy_stft1), axis=1)
stft_ref_minmean = median_stft_ref - np.mean(median_stft_ref)
stft_ref_squ = stft_ref_minmean ** 2
ref_norm = np.linalg.norm(stft_ref_squ)

# fig, ax = plt.subplots()
# img = lb.display.specshow(lb.amplitude_to_db(crazy_stft,ref=np.max),y_axis='log', x_axis='time', ax=ax)
# ax.set_title('Reference Spectrogram')
# fig.colorbar(img, ax=ax, format="%+2.0f dB")
# plt.show()

# --- Serial Port Setup ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()


def make_spectra(buffers, stft_ref_squ, ref_norm):
    #print("--- Spectra time ---")

    #removing dc offset
    dc_fixed = buffers - np.mean(buffers, axis=1, keepdims=True)

    #finding rms volume to eliminate noise
    if np.max(np.sqrt(np.mean(dc_fixed**2,axis=1))) < 4.5:
        return [0.0, 0.0, 0.0]

    #stft on samples
    f, s, Zxx = sg.stft(dc_fixed, fs=SAMPLE_RATE, nperseg=512, noverlap=0)

    # Get median across the time frames (axis 2)
    live_medians = np.median(np.abs(Zxx), axis=2)
    # Slice to match your 40:400 reference
    live_clipped = live_medians[:, 40:400]

    #mean square to ignore people noise
    live_min_mean = live_clipped - np.mean(live_clipped, axis=1, keepdims=True)
    live_sq = live_min_mean ** 2

    # Dot product for all 3 mics
    scores = np.dot(live_sq, stft_ref_squ) / (np.linalg.norm(live_sq, axis=1) * ref_norm + 1e-9)

    return scores.tolist()

# --- Main Loop ---

while True:
    try:
        if ser.in_waiting >= FRAME_SIZE:
            # 1. Read everything currently in the buffer
            chunk = ser.read(ser.in_waiting)
            last_data_time = time.perf_counter()  # Reset the "Stuck" timer

            # 2. SLIDING WINDOW SEARCH - doesnt get stuck if it is misaligned and not reading the start of a packet

            i = 0
            while i <= len(chunk) - FRAME_SIZE:
                if chunk[i] == 60 and chunk[i + 5] == 62:
                    # Valid frame found! Unpack it
                    frame = chunk[i: i + 6]

                    if data_ptr == 0:
                        #timer for sample rate
                        start_time = time.perf_counter()

                    #unpacking
                    m1 = (frame[1] << 2) | ((frame[2] & 0xF0) >> 6)
                    m2 = ((frame[2] & 0x3F) << 4) | ((frame[3] & 0xF0) >> 4)
                    m3 = ((frame[3] & 0x0F) << 6) | (frame[4] & 0x3F)

                    mic_data[0, data_ptr] = m1
                    mic_data[1, data_ptr] = m2
                    mic_data[2, data_ptr] = m3
                    data_ptr += 1

                    # Jump ahead by a full frame
                    i += 6
                else:
                    # Not a start marker? Just skip 1 byte and keep looking
                    i += 1

                #running correlation when buffer full
                if data_ptr >= BUFFER_SIZE:
                    duration = time.perf_counter() - start_time
                    print(f"SR: {BUFFER_SIZE / duration:.0f}Hz", end=" | ")

                    scores = make_spectra(mic_data, stft_ref_squ, ref_norm)
                    print(f"Scores: {[round(s, 2) for s in scores]}")

                    data_ptr = 0
                    ser.reset_input_buffer()  # Clear the "math lag"
                    start_time = time.perf_counter()
                    break  # Exit the 'while i' loop to start fresh

        # HEARTBEAT: If no data for 2 seconds, the Arduino or Port is likely frozen
        # if time.perf_counter() - last_data_time > 2.0:
        #     print("Warning: No serial data detected. Is the Arduino still on?")
        #     last_data_time = time.perf_counter()

    except Exception as e:
        traceback.print_exc()
        break