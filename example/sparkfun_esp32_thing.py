from property import Property
from thing import Thing
from value import Value
from server import MultipleThings, WebThingServer
import logging
import time
import machine

log = logging.getLogger(__name__)


class Led(Thing):

    def __init__(self, ledPin):
        Thing.__init__(self,
                       'Blue LED',
                       ['OnOffSwitch', 'Light'],
                       'Blue LED on SparkFun ESP32 Thing')
        self.pinLed = machine.Pin(ledPin, machine.Pin.OUT)
        self.pwmLed = machine.PWM(self.pinLed)
        self.ledBrightness = 50
        self.on = False
        self.updateLed()

        self.add_property(
            Property(self,
                     'on',
                     Value(self.on, self.setOnOff),
                     metadata={
                         '@type': 'OnOffProperty',
                         'label': 'On/Off',
                         'type': 'boolean',
                         'description': 'Whether the LED is turned on',
                     }))
        self.add_property(
            Property(self,
                     'brightness',
                     Value(self.ledBrightness, self.setBrightness),
                     metadata={
                         '@type': 'BrightnessProperty',
                         'label': 'Brightness',
                         'type': 'number',
                         'minimum': 0,
                         'maximum': 100,
                         'unit': 'percent',
                         'description': 'The brightness of the LED',
                     }))

    def setOnOff(self, onOff):
        log.info('setOnOff: onOff = ' + str(onOff))
        self.on = onOff
        self.updateLed()

    def setBrightness(self, brightness):
        log.info('setBrightness: brightness = ' + str(brightness))
        self.ledBrightness = brightness
        self.updateLed()

    def updateLed(self):
        log.debug('updateLed: on = ' + str(self.on) +
                  ' brightness = ' + str(self.ledBrightness))
        if self.on:
            self.pwmLed.duty(self.ledBrightness)
        else:
            self.pwmLed.duty(0)


class Button(Thing):

    def __init__(self, pin):
        Thing.__init__(self,
                       'Button 0',
                       'binarySensor',
                       'Button 0 on SparkFun ESP32 Thing')
        self.pin = machine.Pin(pin, machine.Pin.IN)

        self.button = Value(False)
        self.add_property(
            Property(self,
                     'on',
                     self.button,
                     metadata={
                         'type': 'boolean',
                         'description': 'Button 0 pressed'
                     }))
        self.prev_pressed = self.is_pressed()

    def is_pressed(self):
        return self.pin.value() == 0

    def process(self):
        pressed = self.is_pressed()
        if pressed != self.prev_pressed:
            self.prev_pressed = pressed
            log.debug('pressed = ' + str(pressed))
            self.button.notify_of_external_update(pressed)


def run_server():
    log.info('run_server')

    led = Led(5)
    button = Button(0)

    # If adding more than one thing here, be sure to set the `name`
    # parameter to some string, which will be broadcast via mDNS.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(MultipleThings([led, button],
                                           'SparkFun-ESP32-Thing'),
                            port=80)
    try:
        log.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        log.info('stopping the server')
        server.stop()
        log.info('done')

    while True:
        time.sleep(0.1)
        button.process()
