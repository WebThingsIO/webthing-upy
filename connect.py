import machine
import network
import time
import config


def start_ftp():
    print('Starting FTP...')
    network.ftp.start()


def start_ntp():
    print('Syncing to NTP...')
    rtc = machine.RTC()
    rtc.ntp_sync(server='pool.ntp.org')

    if not rtc.synced():
        print('  waiting for time sync...', end='')
        time.sleep(0.5)
        while not rtc.synced():
            print('.', end='')
            time.sleep(0.5)
        print('')
    print('Time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))


def connect_to_ap():
    station = network.WLAN(network.STA_IF)
    if not station.active():
        station.active(True)
        if not station.isconnected():
            print('Connecting....')
            station.connect(config.SSID, config.PASSWORD)
            while not station.isconnected():
                time.sleep(1)
                print('.', end='')
            print('')
    print('ifconfig =', station.ifconfig())
