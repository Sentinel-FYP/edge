from inference import ModelThread
from memory_profiler import profile
import argparse
from dotenv import load_dotenv
from sio_client import sio_client
import asyncio
from camera import Camera
import asyncio


async def main():
    load_dotenv()
    loop = asyncio.get_running_loop()
    # sio = await sio_client()
    connection_strs = ["./videos/merged.mp4"]
    processes: list[ModelThread] = []
    for conn in connection_strs:
        camera = Camera(conn)
        camera.connect()
        model_process = ModelThread(camera=camera, async_loop=loop)
        processes.append(model_process)
        model_process.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    asyncio.run(main())
