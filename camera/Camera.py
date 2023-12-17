import cv2
import argparse
import time


class Camera:
    def __init__(self, ip, port, username, password) -> None:
        self.__init__(f'rtsp://{username}:{password}@{ip}:{port}')

    def __init__(self, connection_str):
        self.connection_str = connection_str
        self.suspend_stream = False
        self.suspend_time = 4

    def connect(self):
        self.cap = cv2.VideoCapture(self.connection_str)
        if not self.cap.isOpened():
            raise Exception("Video source not found")

    def disconnect(self):
        cv2.destroyAllWindows()
        self.cap.release()

    def get_frame(self, show=False):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            if not self.suspend_stream:
                print("Waiting for stream to resume")
                self.suspend_stream = True
                self.disconnect()
                time.sleep(self.suspend_time)
                self.connect()
                return
            raise CameraDisconnected("Camera disconnected")
        if show:
            cv2.imshow("frame", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.disconnect()
                raise CameraDisconnected("Camera disconnected")
        return frame

    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)


class CameraDisconnected(Exception):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, required=True)
    args = parser.parse_args()
    camera = Camera(args.url)
    camera.connect()
    while True:
        try:
            frame = camera.get_frame(show=True)
        except CameraDisconnected:
            print("Stream ended")
            break
