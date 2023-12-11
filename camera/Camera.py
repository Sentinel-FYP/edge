import cv2


class Camera:
    def __init__(self, ip, port, username, password) -> None:
        self.connection_str = f'rtsp://{username}:{password}@{ip}:{port}'

    def __init__(self, connection_str):
        self.connection_str = connection_str

    def connect(self):
        self.cap = cv2.VideoCapture(self.connection_str)
        if not self.cap.isOpened():
            raise Exception("Video source not found")

    def disconnect(self):
        self.cap.release()

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.disconnect()
            raise CameraDisconnected("Camera disconnected")
        return frame

    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)


class CameraDisconnected(Exception):
    pass
