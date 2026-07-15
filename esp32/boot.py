import time

import machine
import network

WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

wlan = network.WLAN(network.STA_IF)
network.WLAN(network.AP_IF).active(False)

for attempt in range(3):
    wlan.active(False)
    time.sleep_ms(200)
    wlan.active(True)
    wlan.config(reconnects=3)

    if attempt == 0:
        try:
            networks = sorted(wlan.scan(), key=lambda row: row[3], reverse=True)
            print("Nearby WiFi networks:")
            for ssid, _, channel, rssi, _, _ in networks[:10]:
                print(" ", ssid.decode("utf-8", "replace"), "channel:", channel, "RSSI:", rssi)
        except OSError as exc:
            print("WiFi scan error:", exc)

    try:
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    except OSError as exc:
        print("WiFi connect error:", exc)
        continue

    for _ in range(30):
        if wlan.isconnected():
            break
        time.sleep_ms(500)
    if wlan.isconnected():
        break
    print("WiFi attempt failed:", attempt + 1, "status:", wlan.status())

if wlan.isconnected():
    print("WiFi connected:", wlan.ifconfig())
else:
    print("WiFi failed, rebooting...")
    time.sleep(3)
    machine.reset()
