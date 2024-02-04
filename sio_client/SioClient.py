from socketio import AsyncClient
import events
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
            await sio.emit(events.CREATE_ROOM, {"deviceId": config.DEVICE_ID})

        @sio.event
        async def message(data):
            print("Message from server:", data)

        @sio.event
        async def disconnect():
            print("socket disconnected from server")

        # await sio.connect(f'{config.SERVER_URL}?token={token}', wait_timeout = 10)
        await sio.connect(f"{config.SERVER_URL}", wait_timeout=10)
        return self

    async def close(self):
        await self.disconnect()

    async def send_alert(self, deviceId, localIP):
        await self.emit(events.ALERT_SEND, {"deviceId": deviceId, "localIP": localIP})

    async def send_error(self, message):
        await self.emit(events.ERROR, {"message": message})
