from .streamer import VideoStreamer
from sio_client import SioClient

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
        streamer = VideoStreamer(media_path=MEDIA_PATH, is_rtsp=IS_RTSP_STREAM)
        STREAMERS.add(streamer)
        answer = await streamer.handle_offer(data)
        print("\nAnswer Created", answer)
        await sio.emit(
            "webrtc:answer",
            answer,
        )
