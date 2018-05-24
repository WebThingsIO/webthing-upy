"""Utility functions."""

import time
import network


def timestamp():
    """
    Get the current time.

    Returns the current time in the form YYYY-mm-ddTHH:MM:SS+00:00
    """

    return time.strftime('%Y-%m-%dT%H:%M:%S+00:00')


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
