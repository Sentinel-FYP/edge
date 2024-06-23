from threading import Thread, Event
from .lite import LiteModel, AnomalyType
from .gpu import GPUModel
import logging
from timeit import default_timer as timer
from api.models import AnomalyLog
from datetime import datetime, UTC
from api import APIClient
import asyncio
import utils
import tensorflow as tf
from camera import Camera, CameraDisconnected, TextColors
from config import Paths
import config
from sio_client import SioClient
import traceback


class AnomalyHandler:
    def __init__(
        self,
        api_client: APIClient,
        sio_client: SioClient,
        async_loop: asyncio.AbstractEventLoop,
        camera: Camera,
    ):
        self.api_client = api_client
        self.sio_client = sio_client
        self.async_loop = async_loop
        self.camera = camera
        self.anomaly_started = False
        self.anomaly_log: AnomalyLog = AnomalyLog()

    def anomaly_detected(self, frame):
        if not self.anomaly_started:
            print("Anomaly Started")
            asyncio.ensure_future(
                self.sio_client.send_alert(
                    "Anomaly Detected",
                    f"Anomaly Detected in the {self.camera.name}",
                    self.camera.id,
                ),
                loop=self.async_loop,
            )
            self.anomaly_started = True
            self.anomaly_log.occurredAt = datetime.utcnow().isoformat()
            self.anomaly_log.clipFileName = self.camera.start_recording(frame)
            self.anomaly_log.fromDevice = self.api_client.deviceMongoId
            self.anomaly_log.fromCamera = self.camera.id

    def normal_detected(self):
        if self.anomaly_started:
            print("Anomaly Ended")
            self.anomaly_started = False
            self.anomaly_log.endedAt = datetime.now(UTC).isoformat()
            self.camera.stop_recording()
            asyncio.ensure_future(
                self.api_client.post_anomaly_log(self.anomaly_log.clone()),
                loop=self.async_loop,
            )
            self.anomaly_log.reset()


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
        handlers = [logging.StreamHandler()]
        if log_file:
            handlers.append(logging.FileHandler(log_file, mode="w"))
        logging.basicConfig(
            format="%(threadName)s | %(message)s",
            level=logging.INFO,
            handlers=handlers,
        )
        self.camera = camera
        self.terminate_event = Event()
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.async_loop = async_loop
        self.sio_client = sio_client

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
            self.api_client, self.sio_client, self.async_loop, self.camera
        )
        loop_counter = 0
        fc = 0
        try:
            while True:
                if self.terminate_event.is_set():
                    break
                frame = self.camera.get_frame()
                fc = self.camera.fc
                model.feed_frame(frame, threshold=config.ANOMALY_THRESHOLD)
                # Camera.put_text_overlay(
                #     frame,
                #     text=f"{model.prediction}: {model.probability*100:.2f}%",
                #     color=(
                #         TextColors.GREEN
                #         if model.prediction == AnomalyType.NORMAL
                #         else TextColors.RED
                #     ),
                # )
                if fc % 100 == 0:
                    self.logger.info(f"prediction : {model.prediction}")
                    self.logger.info(f"probability : {model.probability*100:.2f}%")
                    self.logger.info(f"fps : {fc/(timer()-start):.2f}")

                if (loop_counter) % config.THUMBNAIL_UPDATE_FREQUENCY == 0 and not (
                    "test_camera" in self.camera.name
                ):
                    print("Updating Thumbnail")
                    asyncio.ensure_future(
                        self.camera.update_thumbnail(frame, self.sio_client),
                        loop=self.async_loop,
                    )
                if (
                    model.prediction == AnomalyType.ANOMALY
                    and model.probability > config.ANOMALY_THRESHOLD
                ):
                    anomaly_handler.anomaly_detected(frame)
                elif (
                    model.prediction == AnomalyType.ANOMALY
                    and model.probability <= config.ANOMALY_THRESHOLD
                ):
                    anomaly_handler.normal_detected()
                if model.prediction == AnomalyType.NORMAL:
                    anomaly_handler.normal_detected()
                loop_counter += 1
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
            asyncio.ensure_future(
                self.camera.update_active_status(self.sio_client, False),
                loop=self.async_loop,
            )
            self.logger.info("Model thread terminated")
            self.terminate_event.set()
            self.camera.disconnect()

    def terminate(self):
        self.terminate_event.set()
