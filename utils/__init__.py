import cv2
from PIL import Image
import uuid
import psutil
from config import Paths
import pathlib


def generate_video_thumbnail(video_file: str):
    cap = cv2.VideoCapture(video_file)
    ret, frame = cap.read()
    cap.release()
    if ret and frame is not None:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        image.resize((172, 172))
        filename = Paths.TEMP_DIR.value / "{}.jpg".format(uuid.uuid4())
        image.save(filename)
        return filename
    return None


def get_system_ram():
    return round(psutil.virtual_memory().total / (1024.0**3))
