#!/usr/bin/env python3
import sqlite3
from matplotlib import pyplot
from matplotlib import ticker
from datetime import datetime
from operator import itemgetter

db = sqlite3.connect('signals_1.db')
cur = db.cursor()

ROWS = 3
COLS = 2

def do_plot(title, results, start_time, end_time):

    # Assemble data into dictionaries/lists
    macs = set()
    strength_by_mac = {}
    times_by_mac = {}
    for mac, signal, time in results:
        macs.add(mac)

        if mac not in strength_by_mac:
            strength_by_mac[mac] = []

        if mac not in times_by_mac:
            times_by_mac[mac] = []

        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

        strength_by_mac[mac].append(signal / 100.0)
        times_by_mac[mac].append(time)

    # Sort times, filter macs with too few data points
    filtered_macs = []
    for mac in macs:

        times = []
        strengths = []

        for time, strength in sorted(zip(times_by_mac[mac], strength_by_mac[mac]), key=itemgetter(0)):
            if time not in times:
                times.append(time)
                strengths.append(strength)

        times_by_mac[mac] = times
        strength_by_mac[mac] = strengths

        if len(times_by_mac[mac]) > 2:
            filtered_macs.append(mac)

    # Sort by the number of samples, to display the longest plots
    lengths = [ len(times_by_mac[mac]) for mac in filtered_macs ]
    filtered_macs = [ mac for _, mac in sorted(zip(lengths, filtered_macs), key=itemgetter(0), reverse=True) ]

    colors = [
        "red",
        "green",
        "blue",
        "cyan",
        "orange",
        "magenta",
        "brown",
        "black",
        "purple",
        "teal",
    ]


    fig, ax = pyplot.subplots(ROWS, COLS)
    fig.suptitle(title, fontsize="x-large")
    fig.tight_layout()

    axf = ax.flatten()
    for i, mac in enumerate(filtered_macs[ : int(ROWS * COLS) ]):
        axf[i].set_title(mac)
        axf[i].plot(times_by_mac[mac], strength_by_mac[mac], label=mac, marker='|', color=colors[i % len(colors)], linewidth=2)
        axf[i].set_ylim([0, 1.1])
        axf[i].yaxis.set_major_formatter(ticker.PercentFormatter(1))
        axf[i].set_xlim([start_time, end_time])
        
        print(mac, len(times_by_mac[mac]))

    pyplot.show()


# Day1
day1_results = cur.execute("SELECT MAC, SIGNAL, TIME FROM SIGNALS_CLEAN WHERE TIME < DATE('2024-07-28')")
day1_start_time = datetime(2024, 7, 27, 12, 20)
day1_end_time = datetime(2024, 7, 27, 14, 50)

do_plot("Day 1", day1_results, day1_start_time, day1_end_time)

# Day2
day2_results = cur.execute("SELECT MAC, SIGNAL, TIME FROM SIGNALS_CLEAN WHERE TIME > DATE('2024-07-28')")
day2_start_time = datetime(2024, 8, 3, 17, 00)
day2_end_time = datetime(2024, 8, 3, 18, 20)

do_plot("Day 2", day2_results, day2_start_time, day2_end_time)
