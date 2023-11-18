import requests
from urllib.parse import urljoin
import os


class AnomalyLog:
    def __init__(self, occurredAt, fromDevice, clipFileName):
        self.occurredAt = occurredAt
        self.fromDevice = fromDevice
        self.clipFileName = clipFileName

    def post_to_server(self, endedAt):
        url = urljoin(os.getenv("BASE_URL"), "api/anomalyLog")
        data = {"occurredAt": self.occurredAt,
                "fromDevice": self.fromDevice, "endedAt": endedAt, "clipFileName": self.clipFileName}
        headers = {"Authorization": f"Bearer {os.getenv('token')}"}
        response = requests.post(url, json=data, headers=headers)
        return response.json()
