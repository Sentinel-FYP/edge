DEVICE_ID = "abc"
SERVER_URL = "http://localhost:5000"
# SERVER_URL = "http://13.51.86.179:5500"
BASE_URL = f"{SERVER_URL}/api/"

# Config for camera scanning
CAMS_CACHE_FILE = "data/cams.txt"
CAM_PORTS = [8534, 8554, 554]
SCAN_LIMIT = 10

# (ip, port, username, password, camera_name)
TEST_CAMERA_CONFIG = ("192.168.100.9", "8534", "admin", "admin", "test_camera")

# To prevent using test camera uncomment below line
TEST_CAMERA_CONFIG = None
