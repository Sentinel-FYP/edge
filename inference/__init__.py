from .thread import ModelThread
from asyncio import AbstractEventLoop

MODEL_THREADS = {}


def process_cameras(
    cameras: list,
    sio,
    async_loop: AbstractEventLoop,
    api_client,
):
    for camera in cameras:
        model_thread = ModelThread(
            camera=camera,
            async_loop=async_loop,
            api_client=api_client,
            sio_client=sio,
        )
        MODEL_THREADS[camera] = model_thread
        model_thread.start()
