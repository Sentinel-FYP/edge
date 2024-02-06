from memory_profiler import profile
import config
from sio_client import SioClient
import asyncio
import camera
import asyncio
from api import APIClient
from streamer import register_stream_events, release_peer_connections
from inference import process_cameras, kill_threads
import traceback
from httpx import ConnectError

api_client: APIClient = None
sio: SioClient = None


async def shutdown():
    print("Shutting down gracefully")
    await release_peer_connections()
    print("Closed all webrtc peer connections")
    kill_threads()
    print("All threads killed")
    camera.release_all_cams()
    print("Released all cameras")
    if api_client:
        await api_client.close()
        print("API Client Closed")
    if sio:
        await sio.close()
        print("Socket Connection Closed")


async def main():
    global api_client, sio
    print("SERVER_URL", config.SERVER_URL)
    print("BASE_URL", config.BASE_URL)
    print("DEVICE_ID", config.DEVICE_ID)
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
    # process_cameras(camera.CONNECTED_CAMERAS, sio, asyncio.get_event_loop(), api_client)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Keyboard Interrupt, exiting")
        pass
    except ConnectError:
        print("Connection Error")
        print("Server is offline")
    except Exception:
        traceback.print_exc()
    finally:
        print("Shutting down...")
        loop.run_until_complete(shutdown())
        exit(0)
