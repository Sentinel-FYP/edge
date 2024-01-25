import cv2
import argparse
import time
import json


class Camera:
    def __init__(self, url, should_reconnect=True, name=None) -> None:
        self.url = url
        self.should_reconnect = should_reconnect
        self.suspend_time = 4
        self.name = name

    @classmethod
    def from_credentials(cls, ip, port, username, password, name):
        url = f"rtsp://{username}:{password}@{ip}:{port}/"
        return cls(url, name=name)

    def connect(self):
        self.cap = cv2.VideoCapture(self.url)
        if not self.cap.isOpened():
            raise Exception("Video source not found")

    def disconnect(self):
        cv2.destroyAllWindows()
        self.cap.release()

    def reconnect(self):
        self.disconnect()
        time.sleep(self.suspend_time)
        self.connect()

    def get_frame(self, show=False):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            if self.should_reconnect:
                print("Reconnecting...")
                self.reconnect()
                return
            else:
                raise CameraDisconnected("Camera disconnected")
        if show:
            cv2.imshow("frame", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.disconnect()
                raise CameraDisconnected("Camera disconnected")
        return frame

    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)

    def __str__(self):
        return f"Camera {self.name} at {self.url}"


class CameraDisconnected(Exception):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str)
    parser.add_argument("--json", type=str)
    args = parser.parse_args()
    if args.url is None and args.json is None:
        print(args.url, args.json)
        raise Exception("Please provide url or json file")
    if args.json:
        with open(args.json, "r") as f:
            json_data = json.load(f)
        cam_data = json_data[0]
        camera = Camera.from_credentials(
            cam_data["ip"], cam_data["port"], cam_data["username"], cam_data["password"]
        )
    else:
        camera = Camera(args.url)
    camera.connect()
    while True:
        try:
            frame = camera.get_frame(show=True)
        except CameraDisconnected:
            print("Stream ended")
            break
