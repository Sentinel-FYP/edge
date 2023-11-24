import cv2
from PIL import Image
import uuid
import psutil
import tensorflow as tf


def generate_video_thumbnail(video_file: str):
    cap = cv2.VideoCapture(video_file)
    ret, frame = cap.read()
    cap.release()
    if ret and frame is not None:
        image = Image.fromarray(frame)
        image.resize((172, 172))
        filename = "temp/{}.jpg".format(uuid.uuid4())
        image.save(filename)
        return filename
    return None


def get_system_ram():
    return round(psutil.virtual_memory().total / (1024.0 ** 3))
