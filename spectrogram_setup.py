from scipy.signal import spectrogram
import numpy as np


def calculate_spectrogram(data,sample_rate):
    f, time_bins, Sxx = spectrogram(
        data,
        fs=sample_rate,
        nperseg=256,
        noverlap=128,
        nfft=256,
        window="hann",
        return_onesided=False
    )

    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-12)
    Sxx_db = np.fft.fftshift(Sxx_db, axes=0)
    f = np.fft.fftshift(f)

    return f,time_bins,Sxx_db