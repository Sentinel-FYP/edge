from .Camera import Camera, CameraDisconnected, TextColors
import socket
import socket
import ipaddress
from api import APIClient
from sio_client import SioClient
from asyncio import AbstractEventLoop
from inference import create_model_thread
import traceback
import config
from config import Paths
import events

CAMERAS: list[Camera] = []
CONNECTED_CAMERAS: list[Camera] = []


# TEST CAMERA CONFIG IN config.py file
if config.TEST_CAMERA_CONFIG:
    test_camera = Camera.from_credentials(*config.TEST_CAMERA_CONFIG)
else:
    test_camera = None

# Comment out the following code block for testing your camera
# test_camera = Camera.from_credentials(
#     "192.168.1.7", "8554", "admin", "admin", "test_camera"
# )

if test_camera:
    CAMERAS.append(test_camera)


def register_camera_events(
    sio: SioClient, async_loop: AbstractEventLoop, api_client: APIClient
):
    @sio.on(events.CAMERAS_ADD)
    async def on_cameras_add(data):
        print(events.CAMERAS_ADD)
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
            await sio.emit(
                events.CAMERAS_ADDED,
                {
                    "cameraName": new_camera.name,
                    "cameraIP": str(new_camera.ip) + ":" + str(new_camera.port),
                    "username": new_camera.username,
                    "password": new_camera.password,
                    "deviceID": config.DEVICE_ID,
                },
            )
            create_model_thread(new_camera, sio, api_client, async_loop)
        except Exception:
            print("connection failed")
            await sio.emit(
                events.ERROR,
                {
                    "message": "Camera Connection Error",
                    "deviceID": config.DEVICE_ID,
                },
            )
            traceback.print_exc()

    @sio.on(events.CAMERAS_DISCOVER)
    async def on_cameras_discover(data):
        print(events.CAMERAS_DISCOVER)
        await scan_cameras(config.SCAN_LIMIT, sio)

    @sio.on(events.CAMERAS_DISCOVERED_GET)
    async def on_cameras_discovered_get(data):
        print(events.CAMERAS_DISCOVERED_GET)
        with open(Paths.CAMS_CACHE_FILE.value, "r") as f:
            discovered_cams = f.readlines()
            await sio.emit(
                events.CAMERAS_DISCOVERED,
                {"cameras": discovered_cams, "deviceID": config.DEVICE_ID},
            )


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


def get_connected_camera_by_name(name: str):
    for cam in CONNECTED_CAMERAS:
        if cam.name == name:
            return cam
    return None


def get_network_ip():
    # # Get the local hostname and IP address
    # hostname = socket.gethostname()
    # ip = socket.gethostbyname(hostname)
    # ip = ip[: ip.rfind(".")] + ".0"
    return ipaddress.ip_address(config.LOCAL_IP)


def increment_ip(ip):
    ip = ipaddress.ip_address(ip)
    ip += 1
    return str(ip)


def generate_ip_range(limit):
    network_ip = get_network_ip()
    ip = network_ip
    for i in range(limit):
        ip = increment_ip(ip)
        yield ip


async def scan_cameras(limit, sio: SioClient):
    cams = []
    for ipaddr in list(generate_ip_range(limit)):
        print("scanning port for ip: ", ipaddr)
        for port in config.CAM_PORTS:
            try:
                s = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
                )
                s.settimeout(config.SCAN_TIMEOUT)
                s.connect((str(ipaddr), port))
                cam = str(ipaddr) + ":" + str(port)
                print("Camera found at: ", cam)
                print("sending event " + events.CAMERAS_DISCOVED_NEW)
                await sio.emit(
                    events.CAMERAS_DISCOVED_NEW,
                    {"camera": cam, "deviceID": config.DEVICE_ID},
                )
                cams.append(str(ipaddr) + ":" + str(port) + "\n")
            except socket.error:
                pass
            finally:
                s.close()
    cache_to_file(cams)


def cache_to_file(cams: list):
    clear_cache()
    with open(Paths.CAMS_CACHE_FILE.value, "w") as f:
        for cam in cams:
            f.write(cam + "\n")


def clear_cache():
    with open(Paths.CAMS_CACHE_FILE.value, "w") as f:
        f.write("")


def release_all_cams():
    for cam in CONNECTED_CAMERAS:
        cam.disconnect()
