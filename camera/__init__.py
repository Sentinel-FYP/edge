from .Camera import Camera, CameraDisconnected, TextColors
import socket
import socket
import ipaddress
from api import APIClient
from sio_client import SioClient
from asyncio import AbstractEventLoop
from inference import create_model_thread
import os
import traceback
import config

CAMS_CACHE_FILE = "data/cams.txt"
CAM_PORTS = [8534, 8554, 554]
SCAN_LIMIT = 255
CAMERAS: list[Camera] = []
CONNECTED_CAMERAS: list[Camera] = []

test_camera = None

# Comment out the following code block for testing your camera
test_camera = Camera.from_credentials(
    "192.168.100.9", "8534", "admin", "admin", "test_camera"
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
                    "deviceId": config.DEVICE_ID,
                },
            )
            traceback.print_exc()

    @sio.event("cameras:discover")
    async def on_cameras_discover(data):
        print("cameras:discover")
        scan_cameras(SCAN_LIMIT)

    @sio.event("cameras:discovered")
    async def on_cameras_discovered(data):
        print("cameras:discovered")
        with open(CAMS_CACHE_FILE, "r") as f:
            discovered_cams = f.readlines()
            await sio.emit(
                "cameras:discovered",
                {"cams": discovered_cams, "deviceId": config.DEVICE_ID},
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
    # Get the local hostname and IP address
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    ip = ip[: ip.rfind(".")] + ".0"
    return ipaddress.ip_address(ip)


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


def scan_cameras(limit):
    cams = []
    for ipaddr in list(generate_ip_range(limit)):
        print("scanning port for ip: ", ipaddr)
        for port in CAM_PORTS:
            try:
                s = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
                )
                s.settimeout(1)
                s.connect((str(ipaddr), port))
                cams.append(str(ipaddr) + ":" + str(port) + "\n")
            except socket.error:
                continue
    cache_to_file(cams)


def cache_to_file(cams: list):
    clear_cache()
    with open(CAMS_CACHE_FILE, "w") as f:
        for cam in cams:
            f.write(cam + "\n")


def clear_cache():
    with open(CAMS_CACHE_FILE, "w") as f:
        f.write("")
