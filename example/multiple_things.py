from action import Action
from event import Event
from property import Property
from thing import Thing
from value import Value
from server import MultipleThings, WebThingServer
import logging
import random
import time
import uuid

log = logging.getLogger(__name__)


class OverheatedEvent(Event):

    def __init__(self, thing, data):
        Event.__init__(self, thing, 'overheated', data=data)


class FadeAction(Action):

    def __init__(self, thing, input_):
        Action.__init__(self, uuid.uuid4().hex, thing, 'fade', input_=input_)

    def perform_action(self):
        time.sleep(self.input['duration'] / 1000)
        self.thing.set_property('brightness', self.input['brightness'])
        self.thing.add_event(OverheatedEvent(self.thing, 102))


class ExampleDimmableLight(Thing):
    """A dimmable light that logs received commands to stdout."""

    def __init__(self):
        Thing.__init__(self,
                       'My Lamp',
                       ['OnOffSwitch', 'Light'],
                       'A web connected lamp')

        self.add_property(
            Property(self,
                     'on',
                     Value(True, lambda v: print('On-State is now', v)),
                     metadata={
                         '@type': 'OnOffProperty',
                         'label': 'On/Off',
                         'type': 'boolean',
                         'description': 'Whether the lamp is turned on',
                     }))

        self.add_property(
            Property(self,
                     'brightness',
                     Value(50, lambda v: print('Brightness is now', v)),
                     metadata={
                         '@type': 'BrightnessProperty',
                         'label': 'Brightness',
                         'type': 'integer',
                         'description': 'The level of light from 0-100',
                         'minimum': 0,
                         'maximum': 100,
                         'unit': 'percent',
                     }))

        self.add_available_action(
            'fade',
            {
                'label': 'Fade',
                'description': 'Fade the lamp to a given level',
                'input': {
                    'type': 'object',
                    'required': [
                        'brightness',
                        'duration',
                    ],
                    'properties': {
                        'brightness': {
                            'type': 'integer',
                            'minimum': 0,
                            'maximum': 100,
                            'unit': 'percent',
                        },
                        'duration': {
                            'type': 'integer',
                            'minimum': 1,
                            'unit': 'milliseconds',
                        },
                    },
                },
            },
            FadeAction)

        self.add_available_event(
            'overheated',
            {
                'description':
                'The lamp has exceeded its safe operating temperature',
                'type': 'number',
                'unit': 'degree celsius',
            })


class FakeGpioHumiditySensor(Thing):
    """A humidity sensor which updates its measurement every few seconds."""

    def __init__(self):
        Thing.__init__(self,
                       'My Humidity Sensor',
                       ['MultiLevelSensor'],
                       'A web connected humidity sensor')

        self.level = Value(0.0)
        self.add_property(
            Property(self,
                     'level',
                     self.level,
                     metadata={
                         '@type': 'LevelProperty',
                         'label': 'Humidity',
                         'type': 'number',
                         'description': 'The current humidity in %',
                         'minimum': 0,
                         'maximum': 100,
                         'unit': 'percent',
                         'readOnly': True,
                     }))

        log.debug('starting the sensor update looping task')

    @staticmethod
    def read_from_gpio():
        """Mimic an actual sensor updating its reading every couple seconds."""
        return abs(70.0 * random.random() * (-0.5 + random.random()))


def run_server():
    log.info('run_server')

    # Create a thing that represents a dimmable light
    light = ExampleDimmableLight()

    # Create a thing that represents a humidity sensor
    sensor = FakeGpioHumiditySensor()

    # If adding more than one thing, use MultipleThings() with a name.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(MultipleThings([light, sensor],
                                           'LightAndTempDevice'),
                            port=80)
    try:
        log.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        log.info('stopping the server')
        server.stop()
        log.info('done')


if __name__ == '__main__':
    log.basicConfig(
        level=10,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )
    run_server()
