from inference import ModelThread
from memory_profiler import profile
from dotenv import load_dotenv
from sio_client import sio_client
import asyncio
from camera import Camera
import asyncio
from queue import Queue
import time


async def main():
    load_dotenv()
    # sio = await sio_client()
    connection_strs = ["./videos/merged.mp4"]
    processes: list[ModelThread] = []
    tasks_queue = Queue()
    for conn in connection_strs:
        camera = Camera(conn)
        camera.connect()
        model_process = ModelThread(
            camera=camera, tasks_queue=tasks_queue, async_loop=asyncio.get_event_loop())
        processes.append(model_process)
        model_process.start()
    while True:
        while tasks_queue.qsize() > 0:
            task_to_run = tasks_queue.get()
            await task_to_run
        time.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
