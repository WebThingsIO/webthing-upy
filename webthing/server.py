"""Python Web Thing server implementation."""

import json
from microWebSrv2 import MicroWebSrv
import logging
import sys

from utils import get_ip

log = logging.getLogger(__name__)

# set to True to print WebSocket messages
WS_messages = False

# =================================================
# Recommended configuration:
#   - run microWebServer in thread
#   - do NOT run MicroWebSocket in thread
# =================================================
# Run microWebServer in thread
srv_run_in_thread = True
# Run microWebSocket in thread
ws_run_in_thread = False


def print_exc(func):
  def wrapper(*args, **kwargs):
    try:
      log.debug('Calling {}'.format(func.__name__))
      ret = func(*args, **kwargs)
      log.debug('Back from {}'.format(func.__name__))
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
    return self.thing.name


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

  def __init__(self, things, port=80, ssl_options=None):
    """
    Initialize the WebThingServer.

    things -- list of Things managed by this server
    port -- port to listen on (defaults to 80)
    ssl_options -- dict of SSL options to pass to the tornado server
    """
    self.things = things
    self.name = things.get_name()
    self.port = port
    self.ip = get_ip()

    if isinstance(self.things, MultipleThings):
      log.info('Registering multiple things')
      for idx, thing in enumerate(self.things.get_things()):
          thing.set_href_prefix('/{}'.format(idx))
          thing.set_ws_href('{}://{}:{}/{}'.format(
              'wss' if ssl_options is not None else 'ws',
              self.ip,
              self.port,
              idx))

      handlers = [
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
      self.things.get_thing(0).set_ws_href('{}://{}:{}'.format(
          'wss' if ssl_options is not None else 'ws',
          self.ip,
          self.port))

      handlers = [
        (
          '/',
          'GET',
          self.thingGetHandler
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

    self.server = MicroWebSrv(webPath='/flash/www',
                              routeHandlers=handlers,
                              port=port)
    #self.srv.MaxWebSocketRecvLen = 256
    #self.WebSocketThreaded = ws_run_in_thread
    #self.srv.WebSocketStackSize      = 4096
    #self.srv.AcceptWebSocketCallback = _acceptWebSocketCallback

  def start(self):
    """Start listening for incoming connections."""
    #url = '{}://{}:{}/'.format('http',
    #                           self.ip,
    #                           self.port)
    #self.service_info = ServiceInfo(
    #  '_webthing._sub._http._tcp.local.',
    #  '{}._http._tcp.local.'.format(self.name),
    #  address=socket.inet_aton(self.ip),
    #  port=self.port,
    #  properties={
    #      'url': url,
    #  },
    #  server='{}.local.'.format(socket.gethostname()))
    #self.zeroconf = Zeroconf()
    #self.zeroconf.register_service(self.service_info)

    # If WebSocketS used and NOT running in thread, and WebServer IS
    # running in thread make shure WebServer has enough stack size to
    # handle also the WebSocket requests.
    log.info('Starting Web Server')
    self.server.Start(threaded=srv_run_in_thread, stackSize=8192)

  def stop(self):
    """Stop listening."""
    #self.zeroconf.unregister_service(self.service_info)
    #self.zeroconf.close()
    self.server.Stop()

  def getThing(self, routeArgs):
    thing_id = routeArgs['thing_id'] if 'thing_id' in routeArgs else None
    return self.things.get_thing(thing_id)

  def getProperty(self, routeArgs):
    thing = self.getThing(routeArgs)
    if thing:
      property_name = routeArgs['property_name']
      if thing.has_property(property_name):
        return thing, thing.find_property(property_name)
    return None, None

  @print_exc
  def thingsGetHandler(self, httpClient, httpResponse):
    httpResponse.WriteResponseJSONOk([
      thing.as_thing_description()
      for idx, thing in enumerate(self.things.get_things())
    ])

  @print_exc
  def thingGetHandler(self, httpClient, httpResponse, routeArgs=None):
    self.thing = self.getThing(routeArgs)
    if self.thing is None:
      httpResponse.WriteResponseNotFound()
      return
    httpResponse.WriteResponseJSONOk(self.thing.as_thing_description())

  @print_exc
  def propertyGetHandler(self, httpClient, httpResponse, routeArgs=None):
    thing, prop = self.getProperty(routeArgs)
    if thing is None or prop is None:
      httpResponse.WriteResponseNotFound()
      return
    httpResponse.WriteResponseJSONOk({prop.get_name(): prop.get_value()})

  @print_exc
  def propertyPutHandler(self, httpClient, httpResponse, routeArgs=None):
    thing, prop = self.getProperty(routeArgs)
    if thing is None or prop is None:
      httpResponse.WriteResponseNotFound()
      return
    print('Method =', httpClient.GetRequestMethod())
    print('Request Headers =', httpClient.GetRequestHeaders())
    print('Content Length =', httpClient.GetRequestContentLength())
    print('Content type =', httpClient.GetRequestContentType())
    content = httpClient.ReadRequestContent()
    print('content =', content)
    #args = httpClient.ReadRequestContentAsJSON()
    try:
      args = json.loads(content)
    except ValueError:
      args = None
    if args is None:
      httpResponse.WriteResponseBadRequest()
      return
    try:
      prop.set_value(args[prop.get_name()])
    except AttributeError:
      httpResponse.WriteResponseForbidden()
      return
    httpResponse.WriteResponseJSONOk({prop.get_name(): prop.get_value()})
