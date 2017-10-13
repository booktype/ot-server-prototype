import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from autobahn.asyncio.websocket import WebSocketServerFactory

from protocol import WSServerProtocol
from config import HOST, PORT

# our uvloop loop
loop = asyncio.get_event_loop()

# server factory
server_factory = WebSocketServerFactory("ws://{}:{}".format(HOST, PORT))
server_factory.protocol = WSServerProtocol

_generator = loop.create_server(server_factory, port=PORT)
ws_server = loop.run_until_complete(_generator)

loop.run_forever()
