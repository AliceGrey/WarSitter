#!/usr/bin/env python3

import os
import csv
import time
import sqlite3
import requests
import gmplot
from mac_vendor_lookup import MacLookup

MacLookup().update_vendors()
WIGLE_API_KEY = open("wigle.api").read().strip()
GOOGLE_API_KEY = open("google.api").read().strip()

db = sqlite3.connect('signals_1.db')
cur = db.cursor()

results = cur.execute("SELECT DISTINCT SSID FROM SIGNALS_CLEAN")
ssid_list = [ result[0] for result in results ]

LAT = 42.3020275
LON = -83.712292

geo_by_ssid = {}

if os.path.exists('geo-ssid-cache.csv'):
    with open('geo-ssid-cache.csv', 'rt') as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row['lat'] == '':
                row['lat'] = None
            else:
                row['lat'] = float(row['lat'])
            if row['lon'] == '':
                row['lon'] = None
            else:
                row['lon'] = float(row['lon'])
            geo_by_ssid[row['ssid']] = row

for ssid in ssid_list:
    if ssid in geo_by_ssid:
        print(f'Skipping {ssid}')
        continue

    url = f"https://api.wigle.net/api/v2/network/search?onlymine=false&closestLat={LAT}&closestLong={LON}&freenet=false&paynet=false&ssid={ssid}"
    print(f'GET {url}')

    result = requests.get(
        url,
        headers={
            'Accept': 'application/json',
            'Authorization': f'Basic {WIGLE_API_KEY}',
        }
    )

    if not result.headers['content-type'].startswith('application/json'):
        print(result.content)
        continue

    result = result.json()

    try:

        if result['resultCount'] == 0:
            geo_by_ssid[ssid] = {
                'ssid': ssid,
                'lat': None,
                'lon': None,
                'city': None,
                'region': None,
                'country': None,
                'last_updated': None,
            }
            continue

        first_result = result['results'][0]

        geo_by_ssid[ssid] = {
            'ssid': ssid,
            'lat': first_result['trilat'],
            'lon': first_result['trilong'],
            'city': first_result['city'],
            'region': first_result['region'],
            'country': first_result['country'],
            'last_updated': first_result['lastupdt'],
        }

    except KeyError:
        print(result)

        geo_by_ssid[ssid] = {
            'ssid': ssid,
            'lat': None,
            'lon': None,
            'city': None,
            'region': None,
            'country': None,
            'last_updated': None,
        }
        break

    time.sleep(1)

with open('geo-ssid-cache.csv', 'wt') as file:
    
    first_ssid = next(iter(geo_by_ssid.keys()))
    headings = geo_by_ssid[first_ssid].keys()
    writer = csv.DictWriter(file, headings)

    writer.writeheader()
    for row in geo_by_ssid.values():
        writer.writerow(row)

print(geo_by_ssid.keys())

colors=[
    "red",
    "orange",
    "yellow",
    "green",
    "cornflowerblue",
    "violet",
]

gmap = gmplot.GoogleMapPlotter(LAT, LON, 14, apikey=GOOGLE_API_KEY)

for i, loc in enumerate(geo_by_ssid.values()):
    if loc['lat'] is None:
        continue
    results = cur.execute("SELECT DISTINCT MAC FROM SIGNALS_CLEAN WHERE SSID = ?", (loc['ssid'],))
    mac_list = [ result[0] for result in results ]
    html= '<h3>' + loc['ssid'] + '</h3>'
    for mac in mac_list:
        vendor = 'randomized mac'
        try:
            vendor = MacLookup().lookup(mac)
        except:
            pass
        html+= mac + ' (' + vendor +')<br>'  
    gmap.marker(loc['lat'],loc['lon'],color=colors[i%len(colors)], info_window=html, label=loc['ssid'][0], title=loc['ssid'])

# Draw the map to an HTML file:
gmap.draw('map.html')