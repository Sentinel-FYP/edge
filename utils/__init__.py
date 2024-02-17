import cv2
from PIL import Image
import uuid
import psutil
from config import Paths
import pathlib

# import boto3
import config


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


async def upload_to_s3(file_path: pathlib.Path):
    # s3_client = boto3.client(
    #     "s3",
    #     aws_access_key_id=config.S3_KEY,
    #     aws_secret_access_key=config.S3_SECRET,
    # )
    # with open(file_path, "rb") as file:
    #     s3_client.upload_fileobj(file, config.S3_BUCKET, file_path.name)
    # s3_client.close()
    pass
