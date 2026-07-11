import time

import network

WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(30):
        if wlan.isconnected():
            break
        time.sleep(0.5)

if wlan.isconnected():
    print("WiFi connected:", wlan.ifconfig())
else:
    print("WiFi failed, rebooting...")
    import machine

    machine.reset()
