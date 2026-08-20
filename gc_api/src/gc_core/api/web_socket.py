"""Web socket logic"""

### external imports
from collections import defaultdict
import datetime
from enum import Enum
from fastapi import WebSocket
import logging
from pydantic import BaseModel
from random import randint

### config logger
lg = logging.getLogger("app_logger")


class Duration(str, Enum):
    SHORT = "short"
    INF = "inf"


class SocketMessage(BaseModel):
    title: str
    info: str
    time: str
    id: int
    duration: str


class WebSocketManager:
    def __init__(self) -> None:
        self.socket_list: defaultdict[str, dict[str, WebSocket]] = defaultdict(dict)

    def add_websocket(self, api_key: str, socket_key: str, websocket: WebSocket):
        """Add new websocket to"""
        self.socket_list[api_key][socket_key] = websocket

    def remove_websocket(self, api_key: str, socket_key: str):
        print("removing", self.socket_list[api_key])
        self.socket_list[api_key].pop(socket_key, "")

    async def send_long_message(self, api_key: str, title: str, info: str):
        socket_msg = SocketMessage(
            title=title,
            info=info,
            time=f"{datetime.datetime.now().strftime('%H:%M:%S')}",
            id=randint(0, 10000000),
            duration=Duration.INF,
        )
        await self.send_message(api_key, socket_msg)

    async def send_message(self, api_key: str, message: SocketMessage):
        websocket = self.socket_list.get(api_key)
        if websocket is None:
            lg.info(f"No websocket for api-key {api_key}")
            lg.info(f"websocket list {self.socket_list}")
            return

        print(f"sending to {websocket.items()}")
        for _, wsocket in websocket.items():
            await wsocket.send_json(message.model_dump())
