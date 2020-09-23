# webthing-upy

This is a MicroPython version of webthing-python.

This has been tested on an ESP-WROVER-KIT and a SparkFun ESP32 Thing using the
loboris version of ESP32 MicroPython.
The loboris port has a forked copy of https://github.com/jczic/MicroWebSrv and
this requires some further changes which can be found here:

https://github.com/dhylands/MicroPython_ESP32_psRAM_LoBo/tree/rest-improvements

# Building and Flashing MicroPython

Using https://github.com/dhylands/MicroPython_ESP32_psRAM_LoBo/tree/rest-improvements follow
the directions in the [README.md](https://github.com/dhylands/MicroPython_ESP32_psRAM_LoBo/tree/rest-improvements/README.md) file

# Installing webthing-upy

I used version 0.0.12 of [rshell](https://github.com/dhylands/rshell) to copy the webthing-upy files to the board. The
ESP-WROVER-KIT board advertises 2 serial ports. Use the second port (typically /dev/ttyUSB1). The SparkFun ESP32 Thing only advertises a single serial port.

Edit the config.py with an appropriate SSID and password. Edit main.py to be appropriate for the board you're using.

Sample main.py for the SparkFun ESP32 Thing:
```
import start
start.thing()
```
Sample main.py for the ESP-WROVER-KIT:
```
import start
start.rgb()
```
For debugging, remove main.py and enter commands at the REPL manually.

```
$ cd webthing-upy
$ rshell -a --buffer-size=30 --port=/dev/ttyUSB1
webthing-upy> rsync -v . /flash
webthing-upy> repl
>>> Control-D
```
Pressing Control-D will cause the board to soft reboot which will start executing main.py.

# Adding to Gateway

To add your web thing to the WebThings Gateway, install the "Web Thing" add-on and follow the instructions [here](https://github.com/WebThingsIO/thing-url-adapter#readme).
