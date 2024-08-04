from mac_vendor_lookup import MacLookup
import sqlite3
import csv

MacLookup().update_vendors()

db = sqlite3.connect('signals_1.db')
cur = db.cursor()

results = cur.execute("SELECT DISTINCT MAC FROM SIGNALS_CLEAN")
mac_list = [ result[0] for result in results ]

vendor_list = []
for mac in mac_list:
    vendor = ''
    try:
        vendor = MacLookup().lookup(mac)
    except:
        pass
    vendor_list.append({
        'mac': mac,
        'vendor': vendor,
    })

with open('vendor-list.csv', 'wt') as file:
    
    headings = vendor_list[0].keys()
    writer = csv.DictWriter(file, headings)

    writer.writeheader()
    for row in vendor_list:
        writer.writerow(row)
