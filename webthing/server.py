"""Python Web Thing server implementation."""

import json
import socket
from microWebSrv2 import MicroWebSrv
import _thread
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


class WebThingServer:
  """Server to represent a Web Thing over HTTP."""

  def __init__(self, things, name=None, port=80, ssl_options=None):
    """
    Initialize the WebThingServer.

    things -- list of Things managed by this server
    name -- name of this device -- this is only needed if the server is
            managing multiple things
    port -- port to listen on (defaults to 80)
    ssl_options -- dict of SSL options to pass to the tornado server
    """
    if type(things) is not list:
        things = [things]

    self.things = things
    self.port = port
    self.ip = get_ip()

    if len(self.things) > 1 and not name:
      raise Exception('name must be set when managing multiple things')

    if len(self.things) > 1:
      log.info('Registering multiple things')
      for idx, thing in enumerate(self.things):
          thing.set_href_prefix('/{}'.format(idx))
          thing.set_ws_href('{}://{}:{}/{}'.format(
              'wss' if ssl_options is not None else 'ws',
              self.ip,
              self.port,
              idx))

      self.name = name
      handlers = [
        ( '/',
          'GET',
          self.thingsGetHandler
        ),
        ( '/<thing_id>',
          'GET',
          self.thingGetHandler
        ),
        ( '/<thing_id>/properties/<property_name>',
          'GET',
          self.propertyGetHandler
        ),
        ( '/<thing_id>/properties/<property_name>',
          'PUT',
          self.propertyPutHandler
        ),
      ]
    else:
      log.info('Registering a single thing')
      self.things[0].set_ws_href('{}://{}:{}'.format(
          'wss' if ssl_options is not None else 'ws',
          self.ip,
          self.port))

      self.name = self.things[0].name
      handlers = [
        ( '/',
          'GET',
          self.thingGetHandler
        ),
        ( '/properties/<property_name>',
          'GET',
          self.propertyGetHandler
        ),
        ( '/properties/<property_name>',
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
    url = '{}://{}:{}/'.format('http',
                               self.ip,
                               self.port)
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
    if len(self.things) > 1:
      try:
        thing_id = int(routeArgs['thing_id'])
      except ValueError:
        return None
      if thing_id >= len(self.things):
        return None
      return self.things[thing_id]
    else:
      return self.things[0]

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
      for idx, thing in enumerate(self.things)
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
    except:
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

