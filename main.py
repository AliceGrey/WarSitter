#!/usr/bin/env python3
import sys
import subprocess
import time
import signal
import atexit
import sqlite3
from pprint import pprint
from scapy.layers.dot11 import *

db = None
cur = None
def initdb():
    global db, cur
    db = sqlite3.connect("signals.db")
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS "SIGNALS" (
        "TIME"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        "SSID"	TEXT,
        "MAC"	TEXT,
        "BSSID" TEXT,
        "SIGNAL"	INTEGER,
        "RSSI"	INTEGER,
        "FREQ"	INTEGER,
        "CH"	INTEGER
    );""")

def cleanup(card):
    print("cleanup")
    subprocess.run(["sudo", "ip", "link", "set", card, "down"])
    subprocess.run(["sudo", "iw", "dev", card, "set", "type", "managed"])
    subprocess.run(["sudo", "ip", "link", "set", card, "up"])


def signal_handler(sig, frame):
    exit(0)


def lerp(x1: float, x2: float, y1: float, y2: float, d: float):
    return ((y2 - y1) * d + x2 * y1 - x1 * y2) / (x2 - x1)

def getChannel(frequency):
    base = 2407              # 2.4Ghz
    if frequency//1000 == 5: 
        base = 5000          # 5Ghz
    # 2.4 and 5Ghz channels increment by 5
    return (frequency-base)//5

def monitor_mode(card):
    try:
        mode = None
        while mode != "monitor":
            iw = subprocess.run(["iw", card, "info"], capture_output=True, text=True).stdout
            mode = iw.split("type ", 1)[1].split("\n", 1)[0]
            print("Wifi card is in", mode, "mode")
            if mode == "managed":
                print("Setting up monitor mode")
                subprocess.run(["sudo", "airmon-ng", "check", "kill"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                subprocess.run(["sudo", "ip", "link", "set", card, "down"])
                subprocess.run(["sudo", "iw", "dev", card, "set", "type", "monitor"])
                subprocess.run(["sudo", "ip", "link", "set", card, "up"])
        return True
    except:
        print("DANGER WILL ROBINSON")
        return False


def packet_handler(p):
    global db
    if p.haslayer(Dot11ProbeReq):
        # Extract SSID from the packet
        if p[Dot11ProbeReq].info:
            print("Probe Request")
            print("==============================")
            # Extract SSID from the packet
            try:
                ssid = p[Dot11ProbeReq].info.decode()
            except UnicodeDecodeError:
                return

            # Extract MAC address of the client sending the probe request
            client_mac = p.addr2

            # Extract MAC address of the access point (BSSID)
            bssid = p.addr3

            # Extract signal strength percentage
            # Mapping the range of -100 to -50 to the range of 0-100%
            signal_strength = lerp(-100, -50, 0, 100, p[RadioTap].dBm_AntSignal)
            signal_strength = min(signal_strength, 100)

            # Extract RSSI (dBm)
            rssi = p[RadioTap].dBm_AntSignal

            # Get timestamp
            timestamp = int(time.time())

            # Extract frequency (MHz)
            frequency = p[RadioTap].ChannelFrequency

            # Extract channel
            channel = getChannel(frequency)

            # Display the extracted information
            print(f"SSID: {ssid}")
            print(f"Client MAC: {client_mac}")
            print(f"BSSID: {bssid}")
            print(f"Signal Strength: {signal_strength}%")
            print(f"RSSI: {rssi}")
            print(f"Timestamp: {timestamp}")
            print(f"Frequency: {frequency} MHz")
            print(f"Channel: {channel}")
            print("==============================\n")
            cur.execute(
                """INSERT INTO "main"."SIGNALS" ("SSID", "MAC", "BSSID", "SIGNAL", "RSSI", "FREQ", "CH") VALUES (?, ?, ?, ?, ?, ?, ?);""",
                (
                    ssid,
                    client_mac,
                    bssid,
                    signal_strength,
                    rssi,
                    frequency,
                    channel
                )
            )
            db.commit()


def capture_probes(card):
    sniff(
        iface=card,
        prn=packet_handler,
        store=0
    )


def main():
    # TODO: Better arg parsing
    card = sys.argv[1]
    if not monitor_mode(card):
        print("No Monitor mode")
    atexit.register(cleanup, card)
    signal.signal(signal.SIGINT, signal_handler)
    initdb()
    while True:
        capture_probes(card)


if __name__ == '__main__':
    main()

