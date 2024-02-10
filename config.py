from pathlib import Path
from enum import Enum

DEVICE_ID = "abc"
# SERVER_URL = "http://localhost:5000"
SERVER_URL = "http://13.51.86.179:5500"
BASE_URL = f"{SERVER_URL}/api/"

# Config for camera scanning
CAM_PORTS = [8534, 8554, 554]
SCAN_LIMIT = 10
# Timeout for client to wait for camera to respond
SCAN_TIMEOUT = 1

# (ip, port, username, password, camera_name)
# TEST_CAMERA_CONFIG = ("192.168.1.8", "8554", "admin", "admin", "test_camera")

# To prevent using test camera uncomment below line
TEST_CAMERA_CONFIG = None

LOCAL_IP = "192.168.1.0"


class Paths(Enum):
    CLIPS_DIR: Path = Path.cwd() / "clips"
    TEMP_DIR: Path = Path.cwd() / "temp"
    CAMS_CACHE_FILE: Path = Path.cwd() / "data" / "cams.txt"
    TF_LITE_MODEL: Path = Path.cwd() / "saved_models" / "model.tflite"
    GPU_MODEL: Path = Path.cwd() / "saved_models" / "model_gpu"

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
        cls.CLIPS_DIR.value.mkdir(parents=True, exist_ok=True)
        cls.TEMP_DIR.value.mkdir(parents=True, exist_ok=True)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)
