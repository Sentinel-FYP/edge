import socketio
from api import APIClient
import asyncio
import dotenv
import os


async def sio_client():
    api_client = APIClient()
    token = api_client.auth_token
    await api_client.disconnect()

    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        print('socket connected to server')
        await sio.emit("create room", {"deviceId": os.getenv("DEVICE_ID")})

    @sio.event
    async def message(data):
        print('Message from server:', data)

    @sio.event
    async def disconnect():
        print('socket disconnected from server')

    await sio.connect(f'{os.getenv("SERVER_URL")}?token={token}')
    return sio


if __name__ == "__main__":
    dotenv.load_dotenv()
    asyncio.run(sio_client())
