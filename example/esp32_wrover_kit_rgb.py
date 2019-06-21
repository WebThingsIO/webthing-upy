from property import Property
from thing import Thing
from value import Value
from server import SingleThing, WebThingServer
import logging
import machine

log = logging.getLogger(__name__)


class RGBLed(Thing):

    def __init__(self, rPin, gPin, bPin):
        Thing.__init__(
            self,
            'urn:dev:ops:esp32-rgb-led-1234',
            'ESP32-RGB-LED',
            ['OnOffSwitch', 'Light', 'ColorControl'],
            'RGB LED on ESP-Wrover-Kit'
        )
        self.pinRed = machine.Pin(rPin, machine.Pin.OUT)
        self.pinGreen = machine.Pin(gPin, machine.Pin.OUT)
        self.pinBlue = machine.Pin(bPin, machine.Pin.OUT)
        self.pwmRed = machine.PWM(self.pinRed)
        self.pwmGreen = machine.PWM(self.pinGreen)
        self.pwmBlue = machine.PWM(self.pinBlue)
        self.redLevel = 50
        self.greenLevel = 50
        self.blueLevel = 50
        self.on = False
        self.updateLeds()

        self.add_property(
            Property(self,
                     'on',
                     Value(True, self.setOnOff),
                     metadata={
                         '@type': 'OnOffProperty',
                         'title': 'On/Off',
                         'type': 'boolean',
                         'description': 'Whether the LED is turned on',
                     }))
        self.add_property(
            Property(self,
                     'color',
                     Value('#808080', self.setRGBColor),
                     metadata={
                         '@type': 'ColorProperty',
                         'title': 'Color',
                         'type': 'string',
                         'description': 'The color of the LED',
                     }))

    def setOnOff(self, onOff):
        print('setOnOff: onOff =', onOff)
        self.on = onOff
        self.updateLeds()

    def setRGBColor(self, color):
        print('setRGBColor: color =', color)
        self.redLevel = int(color[1:3], 16) / 256 * 100
        self.greenLevel = int(color[3:5], 16) / 256 * 100
        self.blueLevel = int(color[5:7], 16) / 256 * 100
        self.updateLeds()

    def updateLeds(self):
        print('updateLeds: on =', self.on, 'r', self.redLevel,
              'g', self.greenLevel, 'b', self.blueLevel)
        if self.on:
            self.pwmRed.duty(self.redLevel)
            self.pwmGreen.duty(self.greenLevel)
            self.pwmBlue.duty(self.blueLevel)
        else:
            self.pwmRed.duty(0)
            self.pwmGreen.duty(0)
            self.pwmBlue.duty(0)


def run_server():
    log.info('run_server')

    rgb = RGBLed(0, 2, 4)

    # If adding more than one thing here, be sure to set the `name`
    # parameter to some string, which will be broadcast via mDNS.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(SingleThing(rgb), port=80)
    try:
        log.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        log.info('stopping the server')
        server.stop()
        log.info('done')
