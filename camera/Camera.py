import cv2


class Camera:
    def __init__(self, ip, port) -> None:
        self.ip = ip
        self.port = port

    def connect(self, username, password):
        self.cap = cv2.VideoCapture(
            f'rtsp://{username}:{password}@{self.ip}:{self.port}')
        if not self.cap.isOpened():
            raise Exception("RTSP stream not found")

    def disconnect(self):
        self.cap.release()

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise CameraDisconnected("Camera disconnected")
        return frame

    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)


class CameraDisconnected(Exception):
    pass
