# filters.py

from scipy.signal import butter, iirnotch, tf2sos, sosfilt, sosfilt_zi

# sampling rate in hz
fs = 250

# design 3rd order butterworth high pass filter with 0.5 hz fcutoff 
hp_sos = butter(4, 0.5, btype="high", fs=fs, output="sos")
# 3rd order buttersworth low pass filter with 40 hz cutof
lp_sos = butter(4, 40, btype="low", fs=fs, output="sos")
# 2nd order iir notch filter with 60 Hz target freq and 30 quality factor (2 hz width)
bn, an = iirnotch(60, 30, fs=fs)
notch_sos = tf2sos(bn, an)

# initialize filter states
hp_zi = lp_zi = notch_zi = None

def filter_sample(x):
    global hp_zi, lp_zi, notch_zi
    if hp_zi is None:
        hp_zi = sosfilt_zi(hp_sos) * x
        lp_zi = sosfilt_zi(lp_sos) * x
        notch_zi = sosfilt_zi(notch_sos) * x
    y, hp_zi = sosfilt(hp_sos, [x], zi=hp_zi)
    y, notch_zi = sosfilt(notch_sos, [y[0]], zi=notch_zi)
    y, lp_zi = sosfilt(lp_sos, [y[0]], zi=lp_zi)
    return float(y[0])