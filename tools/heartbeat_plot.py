
# heartbeat_plot.py
# real-time serial plotter for heartbeat samples
#
# expects stm32 to print one line per sample over uart in the following format:
# "adc_value/r/n"
#
# uses pyserial and matplotlib

# This file was originally used to plot accelerometer data which is why everything is generalized to number of channels


import serial
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from filters import filter_sample, fs
import numpy as np
from scipy.signal import find_peaks

PORT = "/dev/ttyACM0"
BAUDRATE = 115200
WINDOW_WIDTH = 1000 # number of samples on screen at a time
NUM_CHANNELS = 1 # number of things we are plotting

# returns heartrate in beats per minute
def get_heartrate(data):
    data = np.array(data)
    distance = (int)(0.3 * fs) # minumum  horizontal distance between neighboring peaks
    height = np.mean(data) + np.std(data) # required minimum height of peaks
    peaks, _ = find_peaks(data, height=height, distance=distance)
    if len(peaks) < 2:
        return None
    sample_period = 1/fs
    avg_gap_samples = np.mean(np.diff(peaks)) # gap between peaks in units of samples
    avg_gap_seconds = avg_gap_samples * sample_period
    bpm = 60/avg_gap_seconds 
    return bpm

ser = serial.Serial(PORT, BAUDRATE, timeout=1)
ser.reset_input_buffer()

channels = []
values = []
for i in range (NUM_CHANNELS):
    channels.append(deque([0] * WINDOW_WIDTH, maxlen=WINDOW_WIDTH))

def update(frame):
    while ser.in_waiting:
        raw_data = ser.readline()
        try:
            decoded_data = raw_data.decode("ascii").strip().split(",")
            if len(decoded_data) != NUM_CHANNELS:
                continue
            sample = [int(p) for p in decoded_data]
        except (UnicodeDecodeError, ValueError):
            continue
        for i in range(NUM_CHANNELS):
            channels[i].append(filter_sample(sample[i]))
    return []

fig, ax = plt.subplots(1, 1, sharex=True)

labels = ["filtered_adc_data (heartbeat: unknown for now)"]
lines = []
for i in range(NUM_CHANNELS):
    lines.append(ax.plot(range(WINDOW_WIDTH), channels[i], label=labels[i])[0])

ax.set_title("AD8232 ADC Output After Filtering")
ax.legend(loc="upper right")

def update_plot(frame):
    update(frame)
    for i in range(NUM_CHANNELS):
        lines[i].set_ydata(channels[i])
        data = np.array(channels[i])
        ax.set_ylim(data.min() - 50, data.max() + 200)
        # ax.relim();
        # ax.autoscale_view(scalex=False)
    bpm = get_heartrate(channels[0])
    if bpm is not None:
        lines[0].set_label("filtered adc data (heartbeat: " + str(round(bpm)) + " BPM)")
        ax.legend(loc="upper right")
    return lines


try:
    anim = FuncAnimation(fig, update_plot, interval=50, cache_frame_data=False)
    plt.show()

except KeyboardInterrupt:
    print("keyboard interrupt detected")

finally:
    if ser.is_open:
        ser.close()
        print("serial port closed")