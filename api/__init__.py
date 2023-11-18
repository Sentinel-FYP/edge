import httpx
import os
from anomaly_log import AnomalyLog


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
        response = await self.client.post("anomalyLog", json=data)
        return response.json()
