import scipy.signal as sg
import serial
import numpy as np
import librosa as lb
import traceback
from scipy.ndimage import gaussian_filter1d
import time

start_time = None

SERIAL_PORT = 'COM6'  #may have to change for the pi
BAUD_RATE = 500000
FRAME_SIZE = 6
DATA_BYTES = 4
NUM_MICS = 3
SAMPLE_RATE = 8325  # estimated sample rate

BUFFER_SIZE = 1024

mic_data = np.zeros((NUM_MICS, BUFFER_SIZE), dtype=np.uint16)
data_ptr = 0

last_5_mic_values = [0,0,0,0,0]

crazy_frog1,sr = lb.load("C:/Users/bruno/PyCharmMiscProject/Crazy Frog - Axel F.mp3",sr=SAMPLE_RATE,duration=0.125,offset=29.2)
#need to change file path for the pi

f, s, crazy_stft = sg.stft(crazy_frog1, fs=SAMPLE_RATE, nperseg=512, noverlap=256)
crazy_stft1 = np.abs(crazy_stft)[40:220, :]

#median_stft_ref = np.median(np.abs(crazy_stft1), axis=1)
max_stft_ref = np.max(crazy_stft1, axis=1)

stft_ref_gauss = gaussian_filter1d(max_stft_ref, sigma=1.5)
stft_ref_minmean = stft_ref_gauss - np.mean(stft_ref_gauss)
stft_ref_max = np.maximum(stft_ref_minmean, 0)
ref_norm = np.linalg.norm(stft_ref_max)

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
    rms = np.sqrt(np.mean(dc_fixed**2,axis=1))
    if  np.max(rms) < 4.5:
        return [0.0, 0.0, 0.0]

    #stft on samples
    f, s, Zxx = sg.stft(dc_fixed, fs=SAMPLE_RATE, nperseg=512, noverlap=256)

    # Get max value across timeframes for each buffers stft (axis 2)
    live_maxes = np.max(np.abs(Zxx), axis=2)
    # Slice to match reference target bins
    live_clipped = live_maxes[:, 40:220]
    #gaussin blur
    live_clipped = gaussian_filter1d(live_clipped, sigma=1.5, axis=1)

    #set all data below the mean to 0 to ignore background freqs
    live_min_mean = live_clipped - np.mean(live_clipped, axis=1, keepdims=True)
    live_sq = np.maximum(live_min_mean,0)

    # Dot product for all 3 mics
    scores = np.dot(live_sq, stft_ref_squ) / (np.linalg.norm(live_sq, axis=1) * ref_norm + 1e-9)

    #rms weighting
    weighted_scores = scores * (rms / (rms + 15))

    return weighted_scores.tolist()

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

                    scores = make_spectra(mic_data, stft_ref_max, ref_norm)
                    #scores are generally quite low basically always below 0.5 due to rms weighting
                    bestmic = np.argmax(scores)
                    confidence = scores[bestmic] - np.mean([s for i, s in enumerate(scores) if i != bestmic])
                    if scores == [0,0,0]:
                        print(f"Scores: {[round(s, 2) for s in scores]}, Best: n/a, Confidence: {confidence:.2f}")
                    else:
                        print(f"Scores: {[round(s, 2) for s in scores]}, Best: {bestmic+1}, Confidence: {confidence:.2f}")
                    #if confidence is > 0.15 when no other sounds, probably the song
                    #false positives are somewhat likely if it is noisy, weight mic values low
                    #probably need to run like 5 times and look across them


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