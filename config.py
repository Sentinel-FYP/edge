from pathlib import Path
from enum import Enum
from dotenv import load_dotenv
import os

load_dotenv(override=True)


# S3_BUCKET = os.getenv("S3_BUCKET")
# S3_KEY = os.getenv("S3_KEY")
# S3_SECRET = os.getenv("S3_SECRET")

# assert S3_BUCKET, "S3_BUCKET not found in environment"
# assert S3_KEY, "S3_KEY not found in environment"
# assert S3_SECRET, "S3_SECRET not found in environment"

STREAM_FPS = "24"
STREAM_RES = "320x240"
DEVICE_ID = os.getenv("DEVICE_ID") or "abc"
# SERVER_URL = "http://localhost:5000"
SERVER_URL = os.getenv("SERVER_URL") or "http://13.51.86.179:5500"
BASE_URL = f"{SERVER_URL}/api/"

ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD") or 0.99)
THUMBNAIL_UPDATE_FREQUENCY = int(os.getenv("THUMBNAIL_UPDATE_FREQUENCY") or 90000)

FRAME_SKIP_RATE = int(os.getenv("FRAME_SKIP_RATE") or 5)
# Config for camera scanning
CAM_PORTS = [8554, 554]
SCAN_LIMIT = int(os.getenv("SCAN_LIMIT") or 10)
# Timeout for client to wait for camera to respond
SCAN_TIMEOUT = int(os.getenv("SCAN_TIMEOUT") or 1)
LOGS_FILE = os.getenv("LOGS_FILE")

# (cameraIP, username, password, camera_name)
USE_TEST_CAM = os.getenv("USE_TEST_CAM") == "True" or False
if USE_TEST_CAM:
    TEST_CAMERA_CONFIG = (
        os.getenv("CAM_IP") or "192.168.1.8:8554",
        os.getenv("CAM_ID") or "admin",
        os.getenv("CAM_PASS") or "admin",
    )
else:
    TEST_CAMERA_CONFIG = None

TEST_CAM_COUNT = int(os.getenv("TEST_CAM_COUNT") or 1)

# To prevent using test camera uncomment below line

LOCAL_IP = os.getenv("LOCAL_IP") or "192.168.1.0"


class Paths(Enum):
    CLIPS_DIR: Path = Path.cwd() / "clips"
    TEMP_DIR: Path = Path.cwd() / "temp"
    CAMS_CACHE_FILE: Path = Path.cwd() / "data" / "cams.txt"
    TOKEN_FILE: Path = Path.cwd() / "data" / "token.txt"
    TF_LITE_MODEL: Path = Path.cwd() / "saved_models" / "model.tflite"
    GPU_MODEL: Path = Path.cwd() / "saved_models" / "model_gpu"
    LOGS_DIR: Path = Path.cwd() / "logs"

    @classmethod
    def create_paths(cls):
        if not cls.TF_LITE_MODEL.value.exists():
            raise FileNotFoundError(
                f"Tflite Model file not found at {cls.TF_LITE_MODEL.value}"
            )
        if not cls.GPU_MODEL.value.exists():
            raise FileNotFoundError(
                f"GPU Model files not found at {cls.GPU_MODEL.value}"
            )
        if not cls.CAMS_CACHE_FILE.value.parent.exists():
            cls.CAMS_CACHE_FILE.value.parent.mkdir(parents=True, exist_ok=True)
        cls.CAMS_CACHE_FILE.value.touch(exist_ok=True)
        cls.TOKEN_FILE.value.touch(exist_ok=True)
        cls.CLIPS_DIR.value.mkdir(parents=True, exist_ok=True)
        cls.TEMP_DIR.value.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.value.mkdir(parents=True, exist_ok=True)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)
