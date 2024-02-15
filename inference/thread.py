from threading import Thread, Event
from .lite import LiteModel, AnomalyType
from .gpu import GPUModel
import logging
from timeit import default_timer as timer
from api.models import AnomalyLog
from datetime import datetime
import cv2
import uuid
from api import APIClient
import asyncio
import utils
import tensorflow as tf
from camera import Camera, CameraDisconnected, TextColors
from config import Paths
import config
from sio_client import SioClient
import traceback

ANOMALY_THRESHOLD = 0.5
THUMBNAIL_UPDATE_FREQUENCY = 1000


class AnomalyHandler:
    def __init__(
        self,
        api_client: APIClient,
        sio_client: SioClient,
        async_loop: asyncio.AbstractEventLoop,
    ):
        self.api_client = api_client
        self.sio_client = sio_client
        self.async_loop = async_loop
        self.anomaly_started = False
        self.occurredAt = None
        self.endedAt = None
        self.clipFileName = None
        self.video_writer = None

    def reset(self):
        self.anomaly_started = False
        self.occurredAt = None
        self.endedAt = None
        self.clipFileName = None
        self.video_writer = None

    def handle_anomaly_frame(self, frame):
        self.video_writer.write(frame)

    def anomaly_detected(self, frame, fps, camera_name):
        if not self.anomaly_started:
            print("Anomaly Started")
            asyncio.ensure_future(
                self.sio_client.send_alert(
                    "Anomaly Detected", f"Anomaly Detected in the {camera_name}"
                ),
                loop=self.async_loop,
            )
            self.anomaly_started = True
            self.occurredAt = datetime.now().isoformat()
            self.clipFileName = Paths.CLIPS_DIR.value / f"{uuid.uuid4()}.mp4"
            self.video_writer = cv2.VideoWriter(
                self.clipFileName,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                frame.shape[:2][::-1],
            )
        self.handle_anomaly_frame(frame)

    def create_anomaly_log(self):
        return AnomalyLog(
            occurredAt=self.occurredAt,
            fromDevice=self.api_client.deviceMongoId,
            clipFileName=self.clipFileName.name,
            endedAt=self.endedAt,
        )

    def normal_detected(self):
        if self.anomaly_started:
            print("Anomaly Ended")
            self.anomaly_started = False
            self.endedAt = datetime.now().isoformat()
            # asyncio.ensure_future(
            #     utils.upload_to_s3(self.clipFileName), loop=self.async_loop
            # )
            asyncio.ensure_future(
                self.api_client.post_anomaly_log(self.create_anomaly_log()),
                loop=self.async_loop,
            )
            self.video_writer.release()
            self.reset()


class ModelThread(Thread):
    def __init__(
        self,
        camera: Camera,
        async_loop: asyncio.AbstractEventLoop,
        api_client: APIClient,
        sio_client: SioClient,
    ):
        Thread.__init__(self)
        log_file = (
            None
            if config.LOGS_FILE is None
            else str(Paths.LOGS_DIR.value / config.LOGS_FILE)
        )
        logging.basicConfig(
            format="%(threadName)s | %(message)s",
            level=logging.INFO,
            filename=log_file,
            filemode="w",
        )
        self.camera = camera
        self.terminate_event = Event()
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.async_loop = async_loop
        self.sio_client = sio_client
        self.should_pause = Event()

    def run(self):
        try:
            self._run()
        except KeyboardInterrupt:
            self.terminate()

    def _run(self):
        self.logger.info("Model thread started")
        self.logger.info("Loading Model")
        if utils.get_system_ram() > 8 and tf.test.is_gpu_available(cuda_only=True):
            model = GPUModel(
                str(Paths.GPU_MODEL.value), clip_length=64, output_size=(172, 172)
            )
        else:
            model = LiteModel(
                str(Paths.TF_LITE_MODEL.value),
                clip_length=64,
                output_size=(172, 172),
            )
        self.logger.info("Loaded Model")
        start = timer()
        anomaly_handler = AnomalyHandler(
            self.api_client, self.sio_client, self.async_loop
        )
        fc = -1
        fps = self.camera.get_fps()
        try:
            while True:
                if self.terminate_event.is_set():
                    break
                # self.should_pause.wait()
                frame = self.camera.get_frame()
                fc += 1
                model.feed_frame(frame)
                Camera.put_text_overlay(
                    frame,
                    text=f"{model.prediction}: {model.probability*100:.2f}%",
                    color=(
                        TextColors.GREEN
                        if model.prediction == AnomalyType.NORMAL
                        else TextColors.RED
                    ),
                )
                if fc % 100 == 0:
                    self.logger.info(f"prediction : {model.prediction}")
                    self.logger.info(f"probability : {model.probability*100:.2f}%")
                    self.logger.info(f"fps : {fc/(timer()-start):.2f}")

                if (
                    fc % THUMBNAIL_UPDATE_FREQUENCY == 0
                    and self.camera.name != "test_camera"
                ):
                    asyncio.ensure_future(
                        self.camera.update_thumbnail(frame, self.sio_client),
                        loop=self.async_loop,
                    )
                if (
                    model.prediction == AnomalyType.ANOMALY
                    and model.probability > ANOMALY_THRESHOLD
                ):
                    anomaly_handler.anomaly_detected(frame, fps, self.camera.name)
                if model.prediction == AnomalyType.NORMAL:
                    anomaly_handler.normal_detected()
        except CameraDisconnected:
            print("Camera Disconnected. Terminating thread")
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            anomaly_handler.normal_detected()
            end = timer()
            self.logger.info(
                f"total_frames : {fc} | time_taken : {end - start} | latency : {(end - start) / fc}"
            )
            self.logger.info("Model thread terminated")
            self.terminate_event.set()
            self.camera.disconnect()

    def terminate(self):
        self.terminate_event.set()

    def pause(self):
        self.should_pause.set()

    def unpause(self):
        self.should_pause.clear()
