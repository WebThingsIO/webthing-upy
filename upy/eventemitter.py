'''A super simple EventEmitter implementation.

   Modified slightly from: https://github.com/axetroy/pyee
'''


class EventEmitter:

    def __init__(self):
        self._events = {}

    def on(self, event, handler):
        events = self._events
        if event not in events:
            events[event] = []
        events[event].append(handler)

    def emit(self, event, *data):
        events = self._events
        if event not in events:
            return
        handlers = events[event]
        for handler in handlers:
            handler(data)
