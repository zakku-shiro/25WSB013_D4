import os
import queue
import time

import librosa as lb
import numpy as np
import scipy.signal as sg
from scipy.ndimage import gaussian_filter1d
from config.settings import *
from sound.sound_states import SoundStates


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

def sound_process(sound_in_q, sound_out_q):
    # Precalc
    mic_data = np.zeros((NUM_MICS, MIC_BUFFER_SIZE), dtype=np.uint16)
    mic_data_index = 0

    crazy_frog1, sr = lb.load(os.path.join(os.getcwd(), "sound/music.mp3"), sr=SAMPLE_RATE, duration=0.125, offset=24)
    _, _, crazy_stft = sg.stft(crazy_frog1, fs=SAMPLE_RATE, nperseg=512, noverlap=256)

    max_stft_ref = np.max(np.abs(crazy_stft)[40:220, :], axis=1)

    stft_ref_gauss = gaussian_filter1d(max_stft_ref, sigma=1.5)
    stft_ref_minmean = stft_ref_gauss - np.mean(stft_ref_gauss)
    stft_ref_max = np.maximum(stft_ref_minmean, 0)
    ref_norm = np.linalg.norm(stft_ref_max)

    start_time = time.perf_counter()

    # Main loop
    while True:
        try:
            (m1,m2,m3) = sound_in_q.get(timeout=0.1)
        except queue.Empty:
            continue

        mic_data[0, mic_data_index] = m1
        mic_data[1, mic_data_index] = m2
        mic_data[2, mic_data_index] = m3
        mic_data_index += 1

        if mic_data_index >= MIC_BUFFER_SIZE:
            sample_rate = MIC_BUFFER_SIZE // (time.perf_counter() - start_time)
            print("Sample rate:", sample_rate)

            start_time = time.perf_counter()
            mic_data_index = 0

            scores = make_spectra(mic_data, stft_ref_gauss, ref_norm)
            best_mic_index = np.argmax(scores)
            confidence = scores[best_mic_index] - np.mean([s for i, s in enumerate(scores) if i != best_mic_index])

            output_state = SoundStates((best_mic_index + 1) if confidence > MIC_CONFIDENCE_THRESHOLD else 0)
            sound_out_q.put(output_state)

            print(f"Output state: {output_state}, confidence: {confidence}")