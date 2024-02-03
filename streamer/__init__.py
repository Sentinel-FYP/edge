from .streamer import VideoStreamer
from sio_client import SioClient
from camera import get_connected_camera_by_name

STREAMERS: set[VideoStreamer] = set()
# FOR TESTING VIDEO
MEDIA_PATH = "videos/normal_long_long.mp4"
IS_RTSP_STREAM = False

# FOR TESTING CAMERA
# MEDIA_PATH = "rtsp://:8554/"
# IS_RTSP_STREAM = True


def register_stream_events(sio: SioClient):
    @sio.on("webrtc:offer")
    async def offer(data):
        print("webrtc:offer")
        cameraName = data["cameraName"]
        print("fetching camera", cameraName)
        camera = get_connected_camera_by_name(cameraName)
        if not camera:
            print("Camera not found")
            return
        else:
            streamer = VideoStreamer(media_path=camera.url, is_rtsp=True)
            STREAMERS.add(streamer)
            answer = await streamer.handle_offer(data)
            print("\nAnswer Created", answer)
            await sio.emit(
                "webrtc:answer",
                answer,
            )
