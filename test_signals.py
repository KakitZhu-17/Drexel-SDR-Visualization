import numpy as np

def signal_generator(start, end, fs=1e6, freq=200e3, sigtype="simple",duration = 2):
    if sigtype == "burst":
        total_N = int(fs * duration)
        t = np.arange(total_N) / fs

        burst = np.zeros(total_N)
        s = int(start * fs)
        e = int(end * fs)

        tone = np.sin(2*np.pi*freq*t)
        burst[s:e] = tone[s:e]

        return burst, fs

    if sigtype == "simple":
        fs = 1e6
        N = 1024 * 1000
        t = np.arange(N) / fs
        f = 50e3
        x = np.sin(2*np.pi*f*t) + 0.2*np.random.randn(len(t))
        return x, fs