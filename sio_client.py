import socketio
import asyncio
import dotenv
import os
import camera
from queue import Queue

import json


class SioClient:
    def __init__(self):
        self.sio = socketio.AsyncClient()

    @classmethod
    async def create(cls, token):
        # api_client.disconnect()
        self = cls()
        sio = self.sio

        @sio.event
        async def connect():
            print("socket connected to server")
            await sio.emit("room:create", {"deviceId": os.getenv("DEVICE_ID")})

        @sio.event
        async def message(data):
            print("Message from server:", data)

        @sio.event
        async def disconnect():
            print("socket disconnected from server")

        # camera events
        @sio.on("cameras:discover")
        async def on_cameras_discover(data):
            print("cameras:discover")
            cameras = []
            with open(camera.CAMS_CACHE_FILE) as f:
                for line in f:
                    cameras.append(line.strip())
            await sio.emit(
                "cameras:discovered",
                {"cameras": cameras, "deviceId": os.getenv("DEVICE_ID")},
            )

        # @sio.on("cameras:add")
        # async def on_cameras_add(data):
        #     print("cameras:add")
        #     print(f"Adding camera at {data}")
        #     try:
        #         ip, port = data["ip"].split(":")
        #         new_camera = camera.Camera(ip=ip, port=port)
        #         new_camera.connect(data["username"], data["password"])
        #         new_thread = ModelThread(camera=new_camera)
        #         new_thread.start()
        #         await sio.emit("cameras:added", {"message": "Camera added", 'deviceId': os.getenv("DEVICE_ID")})
        #     except Exception as e:
        #         await sio.emit("cameras:added", {"message": "Camera Connection Error", 'deviceId': os.getenv("DEVICE_ID")})
        #         print(e)

        # await sio.connect(f'{os.getenv("SERVER_URL")}?token={token}')
        await sio.connect(f'{os.getenv("SERVER_URL")}')
        return self

    async def close(self):
        await self.sio.disconnect()

    async def send_alert(self, deviceId, localIP):
        await self.sio.emit("alert:send", {"deviceId": deviceId, "localIP": localIP})
