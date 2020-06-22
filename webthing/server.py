"""Python Web Thing server implementation."""

from microWebSrv import MicroWebSrv
import _thread
import logging
import sys
import network

from errors import PropertyError
from utils import get_addresses

log = logging.getLogger(__name__)

# set to True to print WebSocket messages
WS_messages = True

# =================================================
# Recommended configuration:
#   - run microWebServer in thread
#   - do NOT run MicroWebSocket in thread
# =================================================
# Run microWebServer in thread
srv_run_in_thread = True
# Run microWebSocket in thread
ws_run_in_thread = False

_CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers':
        'Origin, X-Requested-With, Content-Type, Accept',
    'Access-Control-Allow-Methods': 'GET, HEAD, PUT, POST, DELETE',
}


def print_exc(func):
    """Wrap a function and print an exception, if encountered."""
    def wrapper(*args, **kwargs):
        try:
            # log.debug('Calling {}'.format(func.__name__))
            ret = func(*args, **kwargs)
            # log.debug('Back from {}'.format(func.__name__))
            return ret
        except Exception as err:
            sys.print_exception(err)
    return wrapper


class SingleThing:
    """A container for a single thing."""

    def __init__(self, thing):
        """
        Initialize the container.

        thing -- the thing to store
        """
        self.thing = thing

    def get_thing(self, _):
        """Get the thing at the given index."""
        return self.thing

    def get_things(self):
        """Get the list of things."""
        return [self.thing]

    def get_name(self):
        """Get the mDNS server name."""
        return self.thing.title


class MultipleThings:
    """A container for multiple things."""

    def __init__(self, things, name):
        """
        Initialize the container.

        things -- the things to store
        name -- the mDNS server name
        """
        self.things = things
        self.name = name

    def get_thing(self, idx):
        """
        Get the thing at the given index.

        idx -- the index
        """
        try:
            idx = int(idx)
        except ValueError:
            return None

        if idx < 0 or idx >= len(self.things):
            return None

        return self.things[idx]

    def get_things(self):
        """Get the list of things."""
        return self.things

    def get_name(self):
        """Get the mDNS server name."""
        return self.name


class WebThingServer:
    """Server to represent a Web Thing over HTTP."""

    def __init__(self, things, port=80, hostname=None, ssl_options=None,
                 additional_routes=None):
        """
        Initialize the WebThingServer.

        For documentation on the additional route format, see:
        https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/microWebSrv

        things -- list of Things managed by this server
        port -- port to listen on (defaults to 80)
        hostname -- Optional host name, i.e. mything.com
        ssl_options -- dict of SSL options to pass to the tornado server
        additional_routes -- list of additional routes to add to the server
        """
        self.ssl_suffix = '' if ssl_options is None else 's'

        self.things = things
        self.name = things.get_name()
        self.port = port
        self.hostname = hostname

        station = network.WLAN()
        mac = station.config('mac')
        self.system_hostname = 'esp32-upy-{:02x}{:02x}{:02x}'.format(
          mac[3], mac[4], mac[5])

        self.hosts = [
            'localhost',
            'localhost:{}'.format(self.port),
            '{}.local'.format(self.system_hostname),
            '{}.local:{}'.format(self.system_hostname, self.port),
        ]

        for address in get_addresses():
            self.hosts.extend([
                address,
                '{}:{}'.format(address, self.port),
            ])

        if self.hostname is not None:
            self.hostname = self.hostname.lower()
            self.hosts.extend([
                self.hostname,
                '{}:{}'.format(self.hostname, self.port),
            ])

        if isinstance(self.things, MultipleThings):
            log.info('Registering multiple things')
            for idx, thing in enumerate(self.things.get_things()):
                thing.set_href_prefix('/{}'.format(idx))

            handlers = [
                (
                    '/.*',
                    'OPTIONS',
                    self.optionsHandler
                ),
                (
                    '/',
                    'GET',
                    self.thingsGetHandler
                ),
                (
                    '/<thing_id>',
                    'GET',
                    self.thingGetHandler
                ),
                (
                    '/<thing_id>/properties',
                    'GET',
                    self.propertiesGetHandler
                ),
                (
                    '/<thing_id>/properties/<property_name>',
                    'GET',
                    self.propertyGetHandler
                ),
                (
                    '/<thing_id>/properties/<property_name>',
                    'PUT',
                    self.propertyPutHandler
                ),
            ]
        else:
            log.info('Registering a single thing')
            handlers = [
                (
                    '/.*',
                    'OPTIONS',
                    self.optionsHandler
                ),
                (
                    '/',
                    'GET',
                    self.thingGetHandler
                ),
                (
                    '/properties',
                    'GET',
                    self.propertiesGetHandler
                ),
                (
                    '/properties/<property_name>',
                    'GET',
                    self.propertyGetHandler
                ),
                (
                    '/properties/<property_name>',
                    'PUT',
                    self.propertyPutHandler
                ),
            ]

        if isinstance(additional_routes, list):
            handlers = additional_routes + handlers

        self.server = MicroWebSrv(webPath='/flash/www',
                                  routeHandlers=handlers,
                                  port=port)
        self.server.MaxWebSocketRecvLen = 256
        self.WebSocketThreaded = ws_run_in_thread
        self.server.WebSocketStackSize = 8 * 1024
        self.server.AcceptWebSocketCallback = self._acceptWebSocketCallback

    def start(self):
        """Start listening for incoming connections."""
        # If WebSocketS used and NOT running in thread, and WebServer IS
        # running in thread make shure WebServer has enough stack size to
        # handle also the WebSocket requests.
        log.info('Starting Web Server on port {}'.format(self.port))
        self.server.Start(threaded=srv_run_in_thread, stackSize=12*1024)

        mdns = network.mDNS()
        mdns.start(self.system_hostname, 'MicroPython with mDNS')
        mdns.addService('_webthing', '_tcp', 80, self.system_hostname,
                        {
                          'board': 'ESP32',
                          'path': '/',
                        })

    def stop(self):
        """Stop listening."""
        self.server.Stop()

    def getThing(self, routeArgs):
        """Get the thing ID based on the route."""
        if not routeArgs or 'thing_id' not in routeArgs:
            thing_id = None
        else:
            thing_id = routeArgs['thing_id']

        return self.things.get_thing(thing_id)

    def getProperty(self, routeArgs):
        """Get the property name based on the route."""
        thing = self.getThing(routeArgs)
        if thing:
            property_name = routeArgs['property_name']
            if thing.has_property(property_name):
                return thing, thing.find_property(property_name)
        return None, None

    def validateHost(self, headers):
        """Validate the Host header in the request."""
        host = headers.get('host', None) or headers.get('Host', None)
        if host is not None and host.lower() in self.hosts:
            return True

        return False

    @print_exc
    def optionsHandler(self, httpClient, httpResponse, routeArgs=None):
        """Handle an OPTIONS request to any path."""
        if not self.validateHost(httpClient.GetRequestHeaders()):
            httpResponse.WriteResponseError(403)
            return

        httpResponse.WriteResponse(204, _CORS_HEADERS, None, None, None)

    @print_exc
    def thingsGetHandler(self, httpClient, httpResponse):
        """Handle a request to / when the server manages multiple things."""
        if not self.validateHost(httpClient.GetRequestHeaders()):
            httpResponse.WriteResponseError(403)
            return

        base_href = 'http{}://{}'.format(
            self.ssl_suffix,
            httpClient.GetRequestHeaders().get('host', None)
            or httpClient.GetRequestHeaders().get('Host', None)
            or ''
        )
        ws_href = 'ws{}://{}'.format(
            self.ssl_suffix,
            httpClient.GetRequestHeaders().get('host', None)
            or httpClient.GetRequestHeaders().get('Host', None)
            or ''
        )

        descriptions = []
        for thing in self.things.get_things():
            description = thing.as_thing_description()
            description['links'].append({
                'rel': 'alternate',
                'href': '{}{}'.format(ws_href, thing.get_href()),
            })
            description['href'] = thing.get_href()
            description['base'] = '{}{}'.format(base_href, thing.get_href())
            description['securityDefinitions'] = {
                'nosec_sc': {
                    'scheme': 'nosec',
                },
            }
            description['security'] = 'nosec_sc'
            descriptions.append(description)

        httpResponse.WriteResponseJSONOk(
            obj=descriptions,
            headers=_CORS_HEADERS,
        )

    @print_exc
    def thingGetHandler(self, httpClient, httpResponse, routeArgs=None):
        """Handle a GET request for an individual thing."""
        if not self.validateHost(httpClient.GetRequestHeaders()):
            httpResponse.WriteResponseError(403)
            return

        thing = self.getThing(routeArgs)
        if thing is None:
            httpResponse.WriteResponseNotFound()
            return

        base_href = 'http{}://{}'.format(
            self.ssl_suffix,
            httpClient.GetRequestHeaders().get('host', None)
            or httpClient.GetRequestHeaders().get('Host', None)
            or ''
        )
        ws_href = 'ws{}://{}'.format(
            self.ssl_suffix,
            httpClient.GetRequestHeaders().get('host', None)
            or httpClient.GetRequestHeaders().get('Host', None)
            or ''
        )

        description = thing.as_thing_description()
        description['links'].append({
            'rel': 'alternate',
            'href': '{}{}'.format(ws_href, thing.get_href()),
        })
        description['base'] = '{}{}'.format(base_href, thing.get_href())
        description['securityDefinitions'] = {
            'nosec_sc': {
                'scheme': 'nosec',
            },
        }
        description['security'] = 'nosec_sc'

        httpResponse.WriteResponseJSONOk(
            obj=description,
            headers=_CORS_HEADERS,
        )

    @print_exc
    def propertiesGetHandler(self, httpClient, httpResponse, routeArgs=None):
        """Handle a GET request for a property."""
        thing = self.getThing(routeArgs)
        if thing is None:
            httpResponse.WriteResponseNotFound()
            return
        httpResponse.WriteResponseJSONOk(thing.get_properties())

    @print_exc
    def propertyGetHandler(self, httpClient, httpResponse, routeArgs=None):
        """Handle a GET request for a property."""
        if not self.validateHost(httpClient.GetRequestHeaders()):
            httpResponse.WriteResponseError(403)
            return

        thing, prop = self.getProperty(routeArgs)
        if thing is None or prop is None:
            httpResponse.WriteResponseNotFound()
            return
        httpResponse.WriteResponseJSONOk(
            obj={prop.get_name(): prop.get_value()},
            headers=_CORS_HEADERS,
        )

    @print_exc
    def propertyPutHandler(self, httpClient, httpResponse, routeArgs=None):
        """Handle a PUT request for a property."""
        if not self.validateHost(httpClient.GetRequestHeaders()):
            httpResponse.WriteResponseError(403)
            return

        thing, prop = self.getProperty(routeArgs)
        if thing is None or prop is None:
            httpResponse.WriteResponseNotFound()
            return
        args = httpClient.ReadRequestContentAsJSON()
        if args is None:
            httpResponse.WriteResponseBadRequest()
            return
        try:
            prop.set_value(args[prop.get_name()])
        except PropertyError:
            httpResponse.WriteResponseBadRequest()
            return
        httpResponse.WriteResponseJSONOk(
            obj={prop.get_name(): prop.get_value()},
            headers=_CORS_HEADERS,
        )

    # === MicroWebSocket callbacks ===

    @print_exc
    def _acceptWebSocketCallback(self, webSocket, httpClient):
        reqPath = httpClient.GetRequestPath()
        if WS_messages:
            print('WS ACCEPT reqPath =', reqPath)
            if ws_run_in_thread or srv_run_in_thread:
                # Print thread list so that we can monitor maximum stack size
                # of WebServer thread and WebSocket thread if any is used
                _thread.list()
        webSocket.RecvTextCallback = self._recvTextCallback
        webSocket.RecvBinaryCallback = self._recvBinaryCallback
        webSocket.ClosedCallback = self._closedCallback
        things = self.things.get_things()
        if len(things) == 1:
            thing_id = 0
        else:
            thing_id = int(reqPath.split('/')[1])
        thing = things[thing_id]
        webSocket.thing = thing
        thing.add_subscriber(webSocket)

    @print_exc
    def _recvTextCallback(self, webSocket, msg):
        if WS_messages:
            print('WS RECV TEXT : %s' % msg)

    @print_exc
    def _recvBinaryCallback(self, webSocket, data):
        if WS_messages:
            print('WS RECV DATA : %s' % data)

    @print_exc
    def _closedCallback(self, webSocket):
        if WS_messages:
            if ws_run_in_thread or srv_run_in_thread:
                _thread.list()
            print('WS CLOSED')
