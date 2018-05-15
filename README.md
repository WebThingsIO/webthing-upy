# webthing-upy

This is a MicroPython version of webthing-python.

This has been tested on an ESP-WROVER-KIT using the loboris version of ESP32 MicroPython.
The loboris port has a forked copy of https://github.com/jczic/MicroWebSrv and this requires
some further changes which can be found here:

https://github.com/dhylands/MicroPython_ESP32_psRAM_LoBo/tree/rest-improvements

# Building and Flashing MicroPython

Using https://github.com/dhylands/MicroPython_ESP32_psRAM_LoBo/tree/rest-improvements follow
the directions in the [README.md](https://github.com/dhylands/MicroPython_ESP32_psRAM_LoBo/tree/rest-improvements/README.md) file

# Installing webthing-upy

I used version 0.0.12 of [rshell](https://github.com/dhylands/rshell) to copy the webthing-upy files to the board. The
ESP-WROVER-KIT board advertises 2 serial ports. Use the second port (typically /dev/ttyUSB1)
```
$ cd webthing-upy
$ rshell -a --buffer-size=30 --port=/dev/ttyUSB1
webthing-upy> rsync -v . /flash
webthing-upy> repl
>>> import start
>>> start.rgb()
```
 