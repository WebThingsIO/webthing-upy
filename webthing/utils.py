"""Utility functions."""

import time
import network


def timestamp():
    """
    Get the current time.

    Returns the current time in the form YYYY-mm-ddTHH:MM:SS+00:00
    """
    now = time.localtime()
    return '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}+00:00'.format(*now[:6])


def get_ip():
    """
    Get the default local IP address.
    """
    station = network.WLAN(network.STA_IF)
    if station.isconnected():
        ip = station.ifconfig()[0]
    else:
        ip = '127.0.0.1'

    return ip
