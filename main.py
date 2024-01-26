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
import traceback


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

    # cameras = [Camera(url="videos/video.mp4")]
    cameras: list[Camera] = []
    processes = {}
    tasks_queue = Queue()
    for camera in cameras:
        streamer = Streamer(sio_client=sio)
        model_process = ModelThread(
            camera=camera,
            tasks_queue=tasks_queue,
            async_loop=asyncio.get_event_loop(),
            streamer=streamer,
            api_client=api_client,
        )
        processes[camera.name] = model_process
        model_process.start()

    event_loop = asyncio.get_event_loop()
    while True:

        @sio.on("cameras:add")
        def on_cameras_add(data):
            print("cameras:add")
            try:
                ip, port = data["cameraIP"].split(":")

                new_camera = Camera.from_credentials(
                    ip=ip,
                    port=port,
                    username=data["username"],
                    password=data["password"],
                    name="New Camera",
                )
                print(f"Connecting to new Camera {new_camera}")
                new_camera.connect()
                print("Connected")
                streamer = Streamer(sio_client=sio)
                new_process = ModelThread(
                    camera=new_camera,
                    tasks_queue=tasks_queue,
                    async_loop=event_loop,
                    streamer=streamer,
                    api_client=api_client,
                )

                new_process.start()
                processes[data["cameraIP"]] = new_process
                sio.emit(
                    "cameras:added",
                    {"message": "Camera added", "deviceId": os.getenv("DEVICE_ID")},
                )
            except Exception as e:
                print("connection failed")
                sio.emit(
                    "cameras:added",
                    {
                        "message": "Camera Connection Error",
                        "deviceId": os.getenv("DEVICE_ID"),
                    },
                )
                traceback.print_exc()

        @sio.on("stream:start")
        def on_stream_start(data):
            print("stream:start event")
            cameraIP = data["cameraIP"]
            if cameraIP in processes:
                processes[cameraIP].enable_stream()
            else:
                print(f"Invalid start stream request. Camera {cameraIP} not found")

        @sio.on("stream:stop")
        def on_stream_stop(data):
            print("stream:start event")
            cameraIP = data["cameraIP"]
            if cameraIP in processes:
                processes[cameraIP].disable_stream()
            else:
                print(f"Invalid start stream request. Camera {cameraIP} not found")

        try:
            # HANDLE TASKS QUEUE FOR API REQUESTS
            while tasks_queue.qsize() > 0:
                task_to_run = tasks_queue.get()
                await task_to_run
            time.sleep(5)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            break


if __name__ == "__main__":
    asyncio.run(main())
