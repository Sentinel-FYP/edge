import httpx
import os
from .models import AnomalyLog
import utils


class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=os.getenv("BASE_URL"))
        self.auth_token = None
        data = {"deviceID": os.getenv("DEVICE_ID")}
        with httpx.Client(base_url=os.getenv("BASE_URL")) as sync_client:
            response = sync_client.post("deviceAuth", json=data)
            # set bearer token in client
            self.auth_token = response.json()["token"]
            self.client.headers["Authorization"] = f"Bearer {response.json()['token']}"
            self.deviceMongoId = response.json()["edgeDevice"]["_id"]

    async def post_anomaly_log(self, anomaly_log: AnomalyLog):
        print("posting anomaly")
        data = anomaly_log.__dict__
        thumbnail = utils.generate_video_thumbnail(anomaly_log.clipFileName)
        response = await self.client.post("anomalyLog", data=data, files={"thumbnail": open(thumbnail, "rb")})
        return response.json()

    async def disconnect(self):
        await self.client.aclose()
