from pydantic import ValidationError
import websockets
import asyncio

# import logging
from common.log import logger
from common.types import AgentMessage
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed


class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri  # "ws://localhost:8000/ws"
        self.websocket: WebSocketClientProtocol = None

    async def connect(self):
        try:
            self.websocket: WebSocketClientProtocol = await websockets.connect(self.uri, ping_timeout=None)
        except Exception as e:
            print(f"Websocket connection error: {e}")

    async def send_message(self, message: AgentMessage):
        max_retries = 3
        retries = 0

        while retries < max_retries:
            if self.websocket and self.websocket.open:
                try:
                    await self.websocket.send(message)
                    break

                except ConnectionClosed as e:
                    logger.error(e)
                    retries += 1
                    await asyncio.sleep(3)
                except (TypeError, Exception) as e:
                    raise
            else:
                retries += 1
                await asyncio.sleep(3)
                await self.connect()

        if retries >= max_retries:
            print("Failed to send message after several attempts.")

    async def receive_message(self) -> AgentMessage:
        max_retries = 3
        retries = 0

        while retries < max_retries:
            if self.websocket and self.websocket.open:
                try:
                    message = await self.websocket.recv()
                    message = AgentMessage.model_validate_json(message)
                    return message
                except (ConnectionClosed, RuntimeError) as e:
                    logger.error(e)
                    retries += 1
                    await asyncio.sleep(3)
                except (ValidationError, Exception) as e:
                    raise

            else:
                retries += 1
                await asyncio.sleep(3)
                await self.connect()
                print("reconnect succeed!")

        if retries >= max_retries:
            print("Failed to receive message after several attempts.")

    async def close(self):
        await self.websocket.close()
