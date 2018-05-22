from property import Property
from thing import Thing
from value import Value
from server import SingleThing, WebThingServer
import logging
import machine

log = logging.getLogger(__name__)


class RGBLed(Thing):

  def __init__(self, rPin, gPin, bPin):
    Thing.__init__(self,
                   'ESP32-RGB-LED',
                   'dimmableColorLight',
                   'RGB LED on ESP-Wrover-Kit')
    self.red = machine.Pin(rPin, machine.Pin.OUT)
    self.green = machine.Pin(gPin, machine.Pin.OUT)
    self.blue = machine.Pin(bPin, machine.Pin.OUT)

    self.add_property(
      Property(self,
               'on',
               Value(True, self.setOnOff),
               metadata={
                'type': 'boolean',
                'description': 'Whether the LED is turned on',
               }))
    self.add_property(
        Property(self,
                 'level',
                 Value(50, self.setRGBLevel),
                 metadata={
                     'type': 'number',
                     'description': 'The level of light from 0-100',
                     'minimum': 0,
                     'maximum': 100,
                 }))

    self.add_property(
        Property(self,
                 'color',
                 Value('#808080', self.setRGBColor),
                 metadata={
                     'type': 'string',
                     'description': 'The color of the LED',
                 }))

  def setOnOff(self, onOff):
      print('setOnOff: onOff =', onOff)

  def setRGBLevel(self, level):
      print('setsetRGBColorOnOff: level =', level)

  def setRGBColor(self, color):
      print('setRGBColor: color =', color)


def run_server():
    log.info('run_server')

    rgb = RGBLed(0, 4, 2)

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
