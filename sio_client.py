import socketio
import asyncio
import dotenv
import os
import camera
from queue import Queue

# from inference import ModelThread
import json


class SioClient:
    def __init__(self):
        self.sio = socketio.Client()

    @classmethod
    def create(cls, token):
        # api_client.disconnect()
        self = cls()
        sio = self.sio

        @sio.event
        def connect():
            print("socket connected to server")
            sio.emit("create room", {"deviceId": os.getenv("DEVICE_ID")})

        @sio.event
        def message(data):
            print("Message from server:", data)

        @sio.event
        def disconnect():
            print("socket disconnected from server")

        # camera events
        @sio.on("cameras:discover")
        def on_cameras_discover(data):
            print("cameras:discover")
            cameras = []
            with open(camera.CAMS_CACHE_FILE) as f:
                for line in f:
                    cameras.append(line.strip())
            sio.emit(
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

        sio.connect(f'{os.getenv("SERVER_URL")}?token={token}')
        sio.emit("create room", {"deviceId": os.getenv("DEVICE_ID")})
        return self
