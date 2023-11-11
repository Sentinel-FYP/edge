import requests
from urllib.parse import urljoin
import os


def set_jwt():
    url = urljoin(os.getenv("BASE_URL"), "api/deviceAuth")
    data = {"deviceID": os.getenv("DEVICE_ID")}
    response = requests.post(url, json=data)
    os.environ["token"] = response.json()["token"]


def get_device():
    url = urljoin(os.getenv("BASE_URL"), "api/edgeDevice")
    headers = {"Authorization": f"Bearer {os.getenv('token')}"}
    response = requests.get(url, headers=headers)
    for device in response.json():
        if device["deviceID"] == os.getenv("DEVICE_ID"):
            return device
