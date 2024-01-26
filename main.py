from inference import ModelThread
from memory_profiler import profile
from dotenv import load_dotenv
from sio_client import SioClient
import asyncio
from camera import Camera, CameraDisconnected
import asyncio
from queue import Queue
import time
from streamer import Streamer
import uuid
from api import APIClient
import os


async def main():
    load_dotenv()
    api_client = await APIClient.create()

    token = api_client.auth_token
    sio_client = SioClient.create(token=token)
    sio = sio_client.sio

    # # Connect to all cameras
    # camerasCredentials = api_client.device["cameras"]
    # cameras: list[Camera] = []
    # for cred in camerasCredentials:
    #     camera = Camera.from_credentials(
    #         ip=cred["localIP"],
    #         port=cred["port"],
    #         username=cred["username"],
    #         password=cred["password"],
    #         name=cred["cameraName"],
    #     )
    #     if cred["active"]:
    #         cameras.append(camera)
    #     else:
    #         print(f"Camera {camera} is disabled at database. Skipping...")

    # print(f"Total cameras: {len(cameras)}")
    # connected_cameras = []
    # for camera in cameras:
    #     try:
    #         print(f"Connecting to {camera}")
    #         camera.connect()
    #         connected_cameras.append(camera)
    #         print("Connected")
    #     except Exception:
    #         print(f"Failed to connect to {camera}")
    #         continue
    # cameras = connected_cameras

    camera = Camera(url="videos/video.mp4")
    camera.connect()
    cameras = [camera]

    processes: list[ModelThread] = []
    tasks_queue = Queue()
    for camera in cameras:
        streamer = Streamer(sio_client=sio, channel=str(uuid.uuid4()))
        model_process = ModelThread(
            camera=camera,
            tasks_queue=tasks_queue,
            async_loop=asyncio.get_event_loop(),
            streamer=streamer,
            api_client=api_client,
        )
        processes.append(model_process)
        model_process.start()
    while True:
        # @sio.on("cameras:add")
        # async def on_cameras_add(data):
        #     print("cameras:add")
        #     try:
        #         ip, port = data["ip"].split(":")

        #         new_camera = Camera.from_credentials(
        #             ip=ip,
        #             port=port,
        #             username=data["username"],
        #             password=data["password"],
        #             name="New Camera",
        #         )
        #         new_thread = ModelThread(camera=new_camera)
        #         new_thread.start()
        #         await sio.emit(
        #             "cameras:added",
        #             {"message": "Camera added", "deviceId": os.getenv("DEVICE_ID")},
        #         )
        #     except Exception as e:
        #         await sio.emit(
        #             "cameras:added",
        #             {
        #                 "message": "Camera Connection Error",
        #                 "deviceId": os.getenv("DEVICE_ID"),
        #             },
        #         )
        #         print(e)

        while tasks_queue.qsize() > 0:
            task_to_run = tasks_queue.get()
            await task_to_run
        time.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
