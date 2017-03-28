#!/usr/bin/env python

import asyncio
import websockets
import json

# @asyncio.coroutine
# def hello():
#     websocket = yield from websockets.connect('ws://localhost:6437/v6.json')

#     try:
#         yield from websocket.send(json.dumps("{enableGestures: true}"))
#         yield from websocket.send(json.dumps("{focused: true}"))

#         greeting = yield from websocket.recv()
#         print(greeting)

#     finally:
#         yield from websocket.close()

# @asyncio.coroutine
# def handler(websocket):
#     # msg = json.dumps("{enableGestures: true}")
#     # websocket.send(msg)
#     # msg = json.dumps("{focused: true}")
#     # websocket.send(msg)

#     while True:
#         message = websocket.recv()
#         result = json.loads(message)
#         print(result)

# @asyncio.coroutine
# def main():
#     websocket = yield from websockets.connect('ws://localhost:6437/v6.json')

#     # Keep this process running until Enter is pressed
#     print("Press Enter to quit...")
#     try:
#         while True:
#             handler(websocket)
#         # asyncio.get_event_loop().run_until_complete(handler())
#         # asyncio.get_event_loop().run_forever()
#     except KeyboardInterrupt:
#         pass

# if __name__ == "__main__":
#     main()


import asyncio
import websockets

@asyncio.coroutine
def hello():
    websocket = yield from websockets.connect('ws://localhost:6437/v6.json')
    name = input("What's your name? ")
    yield from websocket.send(name)
    print("> {}".format(name))
    greeting = yield from websocket.recv()
    print("< {}".format(greeting))
    yield from websocket.close()

asyncio.get_event_loop().run_until_complete(hello())