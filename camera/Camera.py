import cv2
import argparse
import time
import json
from enum import Enum
import socket
import base64
import events
import config
from sio_client import SioClient
import uuid


class TextColors(Enum):
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)


class Camera:
    def __init__(
        self,
        url,
        should_reconnect=True,
        name=None,
        cameraIP=None,
        username=None,
        password=None,
        id=None,
    ) -> None:
        self.url = url
        self.should_reconnect = should_reconnect
        self.suspend_time = 4
        self.name = name
        self.cameraIP = cameraIP
        self.username = username
        self.password = password
        self.fc = 0
        # self.skip_rate = config.FRAME_SKIP_RATE
        self.clipFileName = None
        self.video_writer: cv2.VideoWriter = None
        self.id = id
        self.cap = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, o: object) -> bool:
        return self.id == o.id

    @classmethod
    def from_credentials(
        cls, cameraIP: str, username: str, password: str, name, id=None, channel=None
    ):
        url = f"rtsp://{username.strip()}:{password.strip()}@{cameraIP}"
        if channel:
            url += channel
        return cls(
            url,
            name=name,
            cameraIP=cameraIP,
            username=username,
            password=password,
            id=id,
        )

    def is_online(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = True
        try:
            ip, port = self.cameraIP.split(":")
            if "/" in port:
                port = port.split("/")[0]
            port = int(port)
            s.connect((ip, port))
        except socket.error:
            result = False
        finally:
            s.close()
        return result

    def connect(self):
        if not self.is_online():
            print(f"{self} is offline")
            raise Exception("Camera is offline")
        self.cap = cv2.VideoCapture(self.url)
        if not self.cap.isOpened():
            raise Exception("Video source not found")

    def disconnect(self):
        cv2.destroyAllWindows()
        if self.cap:
            self.cap.release()
        self.cap = None

    def reconnect(self):
        self.disconnect()
        time.sleep(self.suspend_time)
        self.connect()

    def get_frame(self, show=False):
        if self.cap is None:
            raise CameraDisconnected("Camera disconnected")
        if self.clipFileName is None:
            for _ in range(config.FRAME_SKIP_RATE - 1):
                ret = self.cap.grab()
                self.fc += 1
                if not ret:
                    raise CameraDisconnected("Camera disconnected")
        else:
            for _ in range(config.FRAME_SKIP_RATE - 1):
                ret, frame = self.cap.read()
                self.fc += 1
                if not ret or frame is None:
                    raise CameraDisconnected("Camera disconnected")
                else:
                    self.video_writer.write(frame)
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise CameraDisconnected("Camera disconnected")
        # if show:
        #     cv2.imshow("frame", frame)
        #     if cv2.waitKey(1) & 0xFF == ord("q"):
        #         self.disconnect()
        #         raise CameraDisconnected("Camera disconnected")
        self.fc += 1
        if self.clipFileName is not None:
            self.video_writer.write(frame)
        return frame

    def display(self):
        while True:
            try:
                self.get_frame(show=True)
            except CameraDisconnected:
                print("Stream ended")
                break

    def start_recording(self, frame):
        print("Starting recording")
        self.clipFileName = config.Paths.CLIPS_DIR.value / f"{uuid.uuid4()}.mp4"
        self.video_writer = cv2.VideoWriter(
            str(self.clipFileName),
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.get_fps(),
            frame.shape[:2][::-1],
            isColor=True,
        )
        return str(self.clipFileName)

    def stop_recording(self):
        print("Stopping recording")
        self.video_writer.release()
        self.clipFileName = None

    @staticmethod
    def put_text_overlay(frame, text, color: TextColors = TextColors.RED):
        cv2.putText(
            frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color.value, 2
        )

    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)

    async def update_thumbnail(self, frame, sio_client: SioClient):
        # Convert frame to base64
        _, buffer = cv2.imencode(".jpg", frame)
        base64_string = base64.b64encode(buffer).decode("utf-8")
        await sio_client.emit(
            events.CAMERAS_UPDATE,
            {
                "cameraID": self.id,
                "thumbnail": base64_string,
                "active": True,
            },
        )

    async def update_active_status(self, sio_client: SioClient, active: bool):
        await sio_client.emit(
            events.CAMERAS_UPDATE,
            {
                "cameraID": self.id,
                "active": active,
            },
        )

    def __str__(self):
        return f"Camera#{self.id} {self.name} at {self.url}"


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
