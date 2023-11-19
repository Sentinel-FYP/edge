import httpx
import os
from anomaly_log import AnomalyLog
import utils


class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=os.getenv("BASE_URL"))
        data = {"deviceID": os.getenv("DEVICE_ID")}
        with httpx.Client(base_url=os.getenv("BASE_URL")) as sync_client:
            response = sync_client.post("deviceAuth", json=data)
            # set bearer token in client
            self.client.headers["Authorization"] = f"Bearer {response.json()['token']}"
            self.deviceMongoId = response.json()["edgeDevice"]["_id"]

    async def post_anomaly_log(self, anomaly_log: AnomalyLog):
        data = anomaly_log.__dict__
        thumbnail = utils.generate_video_thumbnail(anomaly_log.clipFileName)
        response = await self.client.post("anomalyLog", params=data, files={"thumbnail": open(thumbnail, "rb")})
        return response.json()
