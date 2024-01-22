from inference import ModelThread
from memory_profiler import profile
from dotenv import load_dotenv
from sio_client import sio_client
import asyncio
from camera import Camera
import asyncio
from queue import Queue
import time
from streamer import Streamer
import uuid
from api import APIClient


async def main():
    load_dotenv()
    api_client = APIClient()
    token = api_client.auth_token
    sio = sio_client(token)
    connection_strs = ["./videos/normal.mp4"]
    processes: list[ModelThread] = []
    tasks_queue = Queue()
    for conn in connection_strs:
        camera = Camera(conn)
        camera.connect()
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
        while tasks_queue.qsize() > 0:
            task_to_run = tasks_queue.get()
            await task_to_run
        time.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
