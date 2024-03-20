import httpx
from .models import AnomalyLog
import utils
import config


class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=config.BASE_URL)
        with open(config.Paths.TOKEN_FILE.value, "r") as file:
            self.auth_token = file.read()
            self.auth_token = self.auth_token if self.auth_token else "temp_token"
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
        if "message" in response and response["message"] == "TOKEN_ERROR":
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
            with open(config.Paths.TOKEN_FILE.value, "w") as file:
                file.write(self.auth_token)
        else:
            print("TOKEN VALID: REUSING TOKEN")
            self.deviceMongoId = response["_id"]
            self.device = response
        self.device["cameras"] = await self.get_cameras()
        return self

    async def get_cameras(self):
        deviceID = self.device["deviceID"]
        response = await self.client.get(f"cameras?deviceID={deviceID}&offline=true")
        return response.json()

    async def get_camera_by_id(self, id):
        response = await self.client.get(f"cameras/{id}")
        response = response.json()
        if "message" in response:
            return None
        return response

    async def post_anomaly_log(self, anomaly_log: AnomalyLog):
        print("posting anomaly...")
        data = dict(anomaly_log.__dict__)
        del data["clipFileName"]
        print(data)
        thumbnail = utils.generate_video_thumbnail(anomaly_log.clipFileName)
        response = await self.client.post(
            "anomalyLogs",
            data=data,
            files={
                "thumbnail": open(thumbnail, "rb"),
                "video": open(anomaly_log.clipFileName, "rb"),
            },
        )
        print("anomaly posted")
        print(response.json())
        return response.json()

    async def close(self):
        await self.client.aclose()
