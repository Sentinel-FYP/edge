from .thread import ModelThread
from asyncio import AbstractEventLoop
from api import APIClient
from sio_client import SioClient
from camera import Camera
from typing import List, Dict
import config

MODEL_THREADS: Dict[Camera, ModelThread] = {}


def process_cameras(
    cameras: List[Camera],
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
    config.FRAME_SKIP_RATE = config.FRAME_SKIP_RATE + 2
    model_thread.start()


def kill_threads():
    for thread in MODEL_THREADS.values():
        thread.terminate()
    MODEL_THREADS.clear()


def pause_threads():
    for thread in MODEL_THREADS.values():
        thread.pause()


def unpause_threads():
    for thread in MODEL_THREADS.values():
        thread.unpause()
