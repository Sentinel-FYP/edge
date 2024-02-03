from socketio import AsyncClient
import os
import config


class SioClient(AsyncClient):
    def __init__(self):
        super().__init__()

    @classmethod
    async def create(cls, token):
        # api_client.disconnect()
        self = cls()
        sio = self

        @sio.event
        async def connect():
            print("socket connected to server")
            await sio.emit("room:create", {"deviceId": config.DEVICE_ID})

        @sio.event
        async def message(data):
            print("Message from server:", data)

        @sio.event
        async def disconnect():
            print("socket disconnected from server")

        # await sio.connect(f'{config.SERVER_URL}?token={token}')
        await sio.connect(f"{config.SERVER_URL}")
        return self

    async def close(self):
        await self.disconnect()

    async def send_alert(self, deviceId, localIP):
        await self.emit("alert:send", {"deviceId": deviceId, "localIP": localIP})
