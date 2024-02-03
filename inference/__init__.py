from .thread import ModelThread
from asyncio import AbstractEventLoop
from api import APIClient
from sio_client import SioClient
from camera import Camera

MODEL_THREADS = {}


def process_cameras(
    cameras: list[Camera],
    sio: SioClient,
    async_loop: AbstractEventLoop,
    api_client: APIClient,
):
    for camera in cameras:
        create_model_thread(camera, sio, api_client, async_loop)


def create_model_thread(
    camera: Camera, sio: SioClient, api_client: APIClient, async_loop: AbstractEventLoop
):
    model_thread = ModelThread(
        camera=camera,
        async_loop=async_loop,
        api_client=api_client,
        sio_client=sio,
    )
    MODEL_THREADS[camera] = model_thread
    model_thread.start()
