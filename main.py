# from inference import ModelThread, process_cameras
from memory_profiler import profile
from dotenv import load_dotenv
from sio_client import SioClient
import asyncio
import camera
import asyncio
from api import APIClient
import os
from streamer import STREAMERS, register_stream_events
from inference import process_cameras
import traceback

api_client: APIClient = None
sio: SioClient = None


async def shutdown():
    coros = [streamer.close() for streamer in STREAMERS]
    await asyncio.gather(*coros)
    STREAMERS.clear()
    # for thread in THREADS:
    #     thread.terminate()
    if api_client:
        await api_client.close()
    if sio:
        await sio.close()


async def main():
    load_dotenv(override=True)
    print("SERVER_URL", os.getenv("SERVER_URL"))
    print("BASE_URL", os.getenv("BASE_URL"))
    print("DEVICE_ID", os.getenv("DEVICE_ID"))
    api_client = await APIClient.create()
    token = api_client.auth_token
    sio = await SioClient.create(token=token)
    camera.fetch_registered_cameras(api_client)
    print("Total Registered Cameras", len(camera.CAMERAS))
    camera.connect_to_cameras()
    print("Total Connected Cameras", len(camera.CONNECTED_CAMERAS))
    # Events for adding camera
    camera.register_camera_events(sio, asyncio.get_event_loop(), api_client)
    # Events for streaming video
    register_stream_events(sio)
    # Run inference on connected cameras in threads
    process_cameras(camera.CONNECTED_CAMERAS, sio, asyncio.get_event_loop(), api_client)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Keyboard Interrupt, exiting")
        pass
    except Exception:
        traceback.print_exc()
    finally:
        print("Shutting down...")
        loop.run_until_complete(shutdown())
        exit(0)
