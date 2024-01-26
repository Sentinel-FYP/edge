import cv2
import base64
import socketio
import os


class Streamer:
    def __init__(self, sio_client):
        self.sio_client: socketio.AsyncClient = sio_client

    def stream(self, frame):
        # encode to base64
        retval, buffer = cv2.imencode(".jpg", frame)
        jpg_as_text = base64.b64encode(buffer)
        self.sio_client.emit(
            "stream:send", {"deviceId": os.getenv("DEVICE_ID"), "frame": jpg_as_text}
        )
