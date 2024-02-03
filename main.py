from inference import ModelThread
from memory_profiler import profile
from dotenv import load_dotenv
from sio_client import SioClient
import asyncio
from camera import Camera, CameraDisconnected
import asyncio
from queue import Queue
import time
from streamer import VideoStreamer
import uuid
from api import APIClient
import os
import traceback

# FOR TESTING VIDEO
MEDIA_PATH = "videos/normal_long_long.mp4"
IS_RTSP_STREAM = False

# FOR TESTING CAMERA
# MEDIA_PATH = "rtsp://:8554/"
# IS_RTSP_STREAM = True
STREAMERS: set[VideoStreamer] = set()
THREADS: set[ModelThread] = set()
api_client: APIClient = None
sio_client: SioClient = None


async def shutdown():
    coros = [streamer.close() for streamer in STREAMERS]
    await asyncio.gather(*coros)
    STREAMERS.clear()
    for thread in THREADS:
        thread.terminate()
    if api_client:
        await api_client.close()
    if sio_client:
        await sio_client.close()


async def main():
    load_dotenv(override=True)
    print("SERVER_URL", os.getenv("SERVER_URL"))
    print("BASE_URL", os.getenv("BASE_URL"))
    print("DEVICE_ID", os.getenv("DEVICE_ID"))
    api_client = await APIClient.create()
    token = api_client.auth_token
    sio_client = await SioClient.create(token=token)
    sio = sio_client.sio

    @sio.on("webrtc:offer")
    async def offer(data):
        streamer = VideoStreamer(media_path=MEDIA_PATH, is_rtsp=IS_RTSP_STREAM)
        STREAMERS.add(streamer)
        answer = await streamer.handle_offer(data)
        print("\nAnswer Created", answer)
        await sio.emit(
            "webrtc:answer",
            answer,
        )

    # Connect to all cameras
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

    # cameras: list[Camera] = []

    # FOR TESTING YOUR OWN VIDEO
    # c = Camera(url="videos/normal_long_long.mp4")
    # c.connect()
    # cameras.append(c)

    # processes = {}
    # tasks_queue = Queue()
    # for camera in cameras:
    #     model_process = ModelThread(
    #         camera=camera,
    #         tasks_queue=tasks_queue,
    #         async_loop=asyncio.get_event_loop(),
    #         api_client=api_client,
    #     )
    #     processes[camera.name] = model_process
    #     model_process.start()

    # event_loop = asyncio.get_event_loop()

    # @sio.on("cameras:add")
    # def on_cameras_add(data):
    #     print("cameras:add")
    #     try:
    #         ip, port = data["cameraIP"].split(":")

    #         new_camera = Camera.from_credentials(
    #             ip=ip,
    #             port=port,
    #             username=data["username"],
    #             password=data["password"],
    #             name="New Camera",
    #         )
    #         print(f"Connecting to new Camera {new_camera}")
    #         new_camera.connect()
    #         print("Connected")
    #         new_process = ModelThread(
    #             camera=new_camera,
    #             tasks_queue=tasks_queue,
    #             async_loop=event_loop,
    #             api_client=api_client,
    #         )

    #         new_process.start()
    #         processes[data["cameraIP"]] = new_process
    #         sio.emit(
    #             "cameras:added",
    #             {"message": "Camera added", "deviceId": os.getenv("DEVICE_ID")},
    #         )
    #     except Exception:
    #         print("connection failed")
    #         sio.emit(
    #             "cameras:added",
    #             {
    #                 "message": "Camera Connection Error",
    #                 "deviceId": os.getenv("DEVICE_ID"),
    #             },
    #         )
    #         traceback.print_exc()

    # while True:
    #     try:
    #         # HANDLE TASKS QUEUE FOR API REQUESTS
    #         while tasks_queue.qsize() > 0:
    #             task_to_run = tasks_queue.get()
    #             await task_to_run
    #         time.sleep(5)
    #     except KeyboardInterrupt:
    #         print("KeyboardInterrupt")
    #         break


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Keyboard Interrupt, exiting")
        pass
    finally:
        print("Shutting down...")
        loop.run_until_complete(shutdown())
        exit(0)
