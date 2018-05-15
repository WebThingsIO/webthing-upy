import machine
import network
import time


station = network.WLAN(network.STA_IF)
if not station.active():
  station.active(True)
  if not station.isconnected():
    print('Connecting....')
    station.connect('SSID', 'password')
    while not station.isconnected():
      time.sleep(1)
      print('.', end='')
  print('ifconfig =', station.ifconfig())

print('Syncing to NTP...')
rtc = machine.RTC()
rtc.ntp_sync(server='pool.ntp.org')

print('Starting mDNS...')
mdns = network.mDNS()
_ = mdns.start("esp32-upy","MicroPython with mDNS")
_ = mdns.addService('_ftp', '_tcp', 21, "MicroPython", {"board": "ESP32", "service": "mPy FTP File transfer", "passive": "True"})
_ = mdns.addService('_telnet', '_tcp', 23, "MicroPython", {"board": "ESP32", "service": "mPy Telnet REPL"})
_ = mdns.addService('_http', '_tcp', 80, "MicroPython", {"board": "ESP32", "service": "mPy Web server"})

print('Starting FTP...')
network.ftp.start()

if not rtc.synced():
  print('  waiting for time sync...', end='')
  time.sleep(0.5)
  while not rtc.synced():
    print('.', end='')
    time.sleep(0.5)
  print('')

print('Time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
