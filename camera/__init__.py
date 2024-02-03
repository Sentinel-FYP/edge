from .Camera import Camera, CameraDisconnected, TextColors
import socket
import tqdm
from api import APIClient
from sio_client import SioClient
from asyncio import AbstractEventLoop
from inference import create_model_thread
import os
import traceback

CAMS_CACHE_FILE = "data/cams.txt"
CAMERAS: list[Camera] = []
CONNECTED_CAMERAS: list[Camera] = []

test_camera = None

# Comment out the following code block for testing your camera
test_camera = Camera.from_credentials(
    "192.168.100.9", "8534", "admin", "admin", "Test Camera"
)

if test_camera:
    CAMERAS.append(test_camera)


def register_camera_events(
    sio: SioClient, async_loop: AbstractEventLoop, api_client: APIClient
):
    @sio.on("cameras:add")
    def on_cameras_add(data):
        print("cameras:add")
        try:
            ip, port = data["cameraIP"].split(":")
            new_camera = Camera.from_credentials(
                ip=ip,
                port=port,
                username=data["username"],
                password=data["password"],
                name="New Camera",
            )
            print(f"Connecting to new Camera {new_camera}")
            new_camera.connect()
            print("Connected")
            create_model_thread(new_camera, sio, api_client, async_loop)
            sio.send_camera_added(new_camera)
        except Exception:
            print("connection failed")
            sio.emit(
                "cameras:added",
                {
                    "message": "Camera Connection Error",
                    "deviceId": os.getenv("DEVICE_ID"),
                },
            )
            traceback.print_exc()


def fetch_registered_cameras(api_client: APIClient):
    try:
        print("Fetching registered cameras from database...")
        camerasCredentials = api_client.device["cameras"]
        print("Total Registered Cameras", len(camerasCredentials))
        for cred in camerasCredentials:
            camera = Camera.from_credentials(
                ip=cred["localIP"],
                port=cred["port"],
                username=cred["username"],
                password=cred["password"],
                name=cred["cameraName"],
            )
            if cred["active"]:
                CAMERAS.append(camera)
            else:
                print(f"{camera} is disabled at database. Skipping...")
    except KeyError:
        print(f"{cred} is not a valid camera credentials. Skipping...")


def connect_to_cameras():
    print("Connecting to cameras fetched from database....")
    for camera in CAMERAS:
        try:
            print(f"Connecting to {camera}")
            camera.connect()
            CONNECTED_CAMERAS.append(camera)
            print("Connected")
        except Exception:
            print(f"Failed to connect to {camera}")
            continue


def get_local_ip():
    # Get the local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        # Doesn't actually send data, just connects
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except socket.error:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip


def discover_cameras():
    local_ip = get_local_ip()

    # Get the first three octets of the local IP address
    base_ip = ".".join(local_ip.split(".")[:3]) + "."

    # Set the range of ports to scan (adjust as needed)
    port_range = [534, 8534]
    ip_range = range(1, 20)

    cams = []
    print("Discovering cameras on the local network...")
    for i in tqdm.tqdm(ip_range):
        ip = base_ip + str(i)
        for port in port_range:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect((ip, port))
                cams.append(f"{ip}:{port}")
            except (socket.timeout, socket.error):
                pass
            finally:
                sock.close()
    cache_to_file(cams)


def cache_to_file(cams: list):
    with open(CAMS_CACHE_FILE, "w") as f:
        for cam in cams:
            f.write(cam + "\n")
