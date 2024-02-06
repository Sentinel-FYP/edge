import httpx
from .models import AnomalyLog
import utils
import config


class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=config.BASE_URL)
        with open("TOKEN", "r") as file:
            self.auth_token = file.read()
        self.client.headers["Authorization"] = f"Bearer {self.auth_token}"
        self.deviceID = config.DEVICE_ID
        self.deviceMongoId = None
        self.device = None

    @classmethod
    async def create(cls):
        self = cls()
        # validate if token is valid
        response = await self.client.get(f"edgeDevices/{self.deviceID}")
        response = response.json()
        if type(response) != list and response["message"] == "TOKEN_ERROR":
            print("TOKEN EXPIRED: GETTING NEW TOKEN")
            # obtain new token
            data = {"deviceID": config.DEVICE_ID}
            response = await self.client.post("deviceAuth", json=data)
            response = response.json()
            self.auth_token = response["token"]
            self.client.headers["Authorization"] = f"Bearer {response['token']}"
            self.deviceMongoId = response["edgeDevice"]["_id"]
            self.device = response["edgeDevice"]
            # write token to file
            with open("TOKEN", "w") as file:
                file.write(self.auth_token)
        else:
            print("TOKEN VALID: REUSING TOKEN")
            self.deviceMongoId = response[0]["_id"]
            self.device = response[0]
        return self

    async def post_anomaly_log(self, anomaly_log: AnomalyLog):
        print("posting anomaly")
        data = anomaly_log.__dict__
        thumbnail = utils.generate_video_thumbnail(anomaly_log.clipFileName)
        response = await self.client.post(
            "anomalyLog", data=data, files={"thumbnail": open(thumbnail, "rb")}
        )
        return response.json()

    async def close(self):
        await self.client.aclose()
