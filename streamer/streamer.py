import cv2
import base64
import socketio
import os


class Streamer:
    def __init__(self, sio_client, channel):
        self.channel = channel
        self.sio_client: socketio.AsyncClient = sio_client

    def stream(self, frame):
        # encode to base64
        print("Streaming")
        retval, buffer = cv2.imencode(".jpg", frame)
        jpg_as_text = base64.b64encode(buffer)
        self.sio_client.emit(
            "stream", {"deviceId": os.getenv("DEVICE_ID"), "frame": jpg_as_text}
        )
