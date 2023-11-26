import socketio
from api import APIClient
import asyncio
import dotenv
import os
import camera


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

    # camera events
    @sio.on("cameras:discover")
    async def on_cameras_discover(data):
        print("cameras:discover")
        cameras = []
        with open(camera.CAMS_CACHE_FILE) as f:
            for line in f:
                cameras.append(line.strip())
        await sio.emit("cameras:discovered", {"cameras": cameras, 'deviceId': os.getenv("DEVICE_ID")})

    @sio.on("cameras:add")
    async def on_cameras_add(data):
        print("cameras:add")
        print(data)
        await sio.emit("cameras:added", {"camera": data["camera"]})

    await sio.connect(f'{os.getenv("SERVER_URL")}?token={token}')
    await sio.emit("create room", {"deviceId": os.getenv("DEVICE_ID")})
    return sio


async def main():
    try:
        dotenv.load_dotenv()
        sio = await sio_client()
        await sio.wait()
    except KeyboardInterrupt:
        print("Keyboard Interrupted")
        await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
