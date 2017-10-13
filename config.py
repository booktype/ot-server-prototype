DEBUG = False

HOST = 'localhost'
PORT = '8765'

try:
    from local_config import *
except ImportError:
    pass
