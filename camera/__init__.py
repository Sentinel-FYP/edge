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
from typing import List

CAMERAS: List[Camera] = []
CONNECTED_CAMERAS: List[Camera] = []

# For testing multiple cameras


# TEST CAMERA CONFIG IN config.py file
if config.TEST_CAMERA_CONFIG:
    for i in range(config.TEST_CAM_COUNT):
        test_camera = Camera.from_credentials(
            *config.TEST_CAMERA_CONFIG, f"test_camera_{i + 1}", id="test_camera_id"
        )
        CAMERAS.append(test_camera)


def register_camera_events(
    sio: SioClient, async_loop: AbstractEventLoop, api_client: APIClient
):
    @sio.on(events.CAMERAS_ADD)
    async def on_cameras_add(data):
        print(events.CAMERAS_ADD)
        try:
            new_camera: Camera = Camera.from_credentials(
                cameraIP=data["cameraIP"],
                username=data["username"],
                password=data["password"],
                name=data["cameraName"],
            )
            print(f"Connecting to new Camera {new_camera}")
            new_camera.connect()
            print("Connected")
            await sio.emit(
                events.CAMERAS_ADDED,
                {
                    "cameraName": new_camera.name,
                    "cameraIP": str(new_camera.cameraIP),
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
            discovered_cams = map(lambda x: x.strip(), discovered_cams)
            discovered_cams = list(filter(lambda x: x != "", discovered_cams))
            connected_cams_ips = [x.cameraIP for x in CONNECTED_CAMERAS]
            discovered_cams = list(
                filter(lambda x: x not in connected_cams_ips, discovered_cams)
            )
            await sio.emit(
                events.CAMERAS_DISCOVERED,
                {"cameras": discovered_cams, "deviceID": config.DEVICE_ID},
            )


async def fetch_registered_cameras(api_client: APIClient):
    try:
        print("Fetching registered cameras from database...")
        camerasCredentials = api_client.device["cameras"]
        print("Total Registered Cameras", len(camerasCredentials))
        for cred in camerasCredentials:
            camera = Camera.from_credentials(
                cameraIP=cred["cameraIP"],
                username=cred["username"],
                password=cred["password"],
                name=cred["cameraName"],
                id=cred["_id"],
            )
            CAMERAS.append(camera)
    except KeyError:
        print(f"{cred} is not a valid camera credentials. Skipping...")


async def connect_to_cameras(sio_client: SioClient):
    print("Connecting to cameras fetched from database....")
    for camera in CAMERAS:
        try:
            print(f"Connecting to {camera}")
            camera.connect()
            CONNECTED_CAMERAS.append(camera)
            print("Connected")
        except Exception as e:
            print(f"Failed to connect to {camera}")
            print(e)
            await camera.update_active_status(sio_client, False)
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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        for port in config.CAM_PORTS:
            try:
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


def cache_to_file(cams: List):
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
