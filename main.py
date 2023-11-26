from model.thread import ModelThread
from memory_profiler import profile
import argparse
from dotenv import load_dotenv
from sio_client import sio_client
import asyncio
from camera import Camera


async def main():
    load_dotenv()
    # sio = await sio_client()
    cameras_credentials = [{
        "ip": "192.168.100.9",
        "port": "8534",
        "username": "admin",
        "password": "admin"
    }]
    processes: list[ModelThread] = []
    for cred in cameras_credentials:
        print("Connecting to camera")
        camera = Camera(cred["ip"], cred["port"])
        camera.connect(cred["username"], cred["password"])
        model_process = ModelThread(camera=camera)
        processes.append(model_process)
        model_process.start()

    for process in processes:
        process.join()
    # await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
