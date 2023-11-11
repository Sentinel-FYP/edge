import requests
from urllib.parse import urljoin
import os


class AnomalyLog:
    def __init__(self, occurredAt, fromDevice):
        self.occurredAt = occurredAt
        self.fromDevice = fromDevice

    def post_to_server(self, endedAt):
        url = urljoin(os.getenv("BASE_URL"), "api/anomalyLog")
        data = {"occurredAt": self.occurredAt,
                "fromDevice": self.fromDevice, "endedAt": endedAt}
        headers = {"Authorization": f"Bearer {os.getenv('token')}"}
        response = requests.post(url, json=data, headers=headers)
        return response.json()
