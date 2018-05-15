import sys
import logging

logging.basicConfig(logging.DEBUG)
log = logging.getLogger(__name__)

sys.path.append('/flash/upy')
sys.path.append('/flash/webthing')
sys.path.append('/flash/example')

# remove ourselves so that we can be re-imported
mod_name = __name__
g = globals()
if mod_name in g:
    print('Deleting', mod_name, 'from globals')
    del g[mod_name]
if mod_name in sys.modules:
    print('Deleting', mod_name, 'from sys.modules')
    del sys.modules[mod_name]

import connect

def rgb():
  print('importing esp32_wrover_kit_rgb...')
  import esp32_wrover_kit_rgb
  print('Starting esp32_wrover_kit_rgb server...')
  esp32_wrover_kit_rgb.run_server()

def single():
  print('importing single_thing...')
  import single_thing
  print('Starting single_thing server...')
  single_thing.run_server()

def multi():
  print('importing multiple_things...')
  import multiple_things
  print('Starting multiple_things server...')
  multiple_things.run_server()
