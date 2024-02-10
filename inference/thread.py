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
from queue import Queue
from sio_client import SioClient
import traceback

ANOMALY_THRESHOLD = 0.9


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

    def anomaly_detected(self, frame, fps):
        if not self.anomaly_started:
            print("Anomaly Started")
            self.anomaly_started = True
            self.occurredAt = datetime.now().isoformat()
            self.clipFileName = f"videos/{uuid.uuid4()}.mp4"
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
            clipFileName=self.clipFileName,
            endedAt=self.endedAt,
        )

    def normal_detected(self):
        if self.anomaly_started:
            print("Anomaly Ended")
            self.anomaly_started = False
            self.endedAt = datetime.now().isoformat()
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
        # tasks_queue: Queue,
        async_loop: asyncio.AbstractEventLoop,
        api_client: APIClient,
        sio_client: SioClient,
    ):
        Thread.__init__(self)
        logging.basicConfig(format="%(threadName)s | %(message)s", level=logging.INFO)
        self.camera = camera
        self.terminate_event = Event()
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        # self.tasks_queue = tasks_queue
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
                "saved_models/a0_stream_5.0", clip_length=64, output_size=(172, 172)
            )
        else:
            model = LiteModel(
                "saved_models/a0_stream_5.0.tflite",
                clip_length=64,
                output_size=(172, 172),
            )
        self.logger.info("Loaded Model")
        start = timer()
        # log_sent = False
        # anomaly_log = None
        # video_writer = None
        anomaly_handler = AnomalyHandler(
            self.api_client, self.sio_client, self.async_loop
        )
        fc = 0
        try:
            while True:
                if self.terminate_event.is_set():
                    break
                frame = self.camera.get_frame()
                fc += 1
                # if video_writer is not None:
                #     video_writer.write(frame)
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
                    self.logger.info(
                        f"prediction : {model.prediction} | probability : {model.probability}"
                    )
                if (
                    model.prediction == AnomalyType.ANOMALY
                    and model.probability > ANOMALY_THRESHOLD
                ):
                    fps = self.camera.get_fps()
                    anomaly_handler.anomaly_detected(frame, fps)
                if model.prediction == AnomalyType.NORMAL:
                    anomaly_handler.normal_detected()

                # if model.prediction == AnomalyType.ANOMALY and log_sent == True:
                #     log_sent = False
                #     anomaly_log = None
                # if (
                #     model.prediction == AnomalyType.ANOMALY
                #     and log_sent == False
                #     and anomaly_log is None
                # ):
                #     print("Anomaly Detected")
                #     clipFileName = f"videos/{uuid.uuid4()}.mp4"
                #     video_writer = cv2.VideoWriter(
                #         clipFileName,
                #         cv2.VideoWriter_fourcc(*"mp4v"),
                #         self.camera.get_fps(),
                #         frame.shape[:2][::-1],
                #     )
                #     anomaly_log = AnomalyLog(
                #         occurredAt=datetime.now().isoformat(),
                #         fromDevice=self.api_client.deviceMongoId,
                #         clipFileName=clipFileName,
                #     )
                # if (
                #     model.prediction == AnomalyType.NORMAL
                #     and log_sent == False
                #     and anomaly_log is not None
                # ):
                #     video_writer.release()
                #     video_writer = None
                #     print("Normal detected. posting to server")
                #     anomaly_log.endedAt = datetime.now().isoformat()
                #     asyncio.ensure_future(
                #         self.api_client.post_anomaly_log(anomaly_log),
                #         loop=self.async_loop,
                #     )

                #     # log_task = self.async_loop.create_task(
                #     #     self.api_client.post_anomaly_log(anomaly_log)
                #     # )
                #     # self.tasks_queue.put(log_task)
                #     log_sent = True
        except CameraDisconnected:
            print("Camera Disconnected. Terminating thread")
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            # if (
            #     model.prediction == AnomalyType.ANOMALY
            #     and log_sent == False
            #     and anomaly_log is not None
            # ):
            #     video_writer.release()
            #     video_writer = None
            #     print("Loop Ended. Posting to server")
            #     anomaly_log.endedAt = datetime.now().isoformat()
            #     log_task = self.async_loop.create_task(
            #         self.api_client.post_anomaly_log(anomaly_log)
            #     )
            #     self.tasks_queue.put(log_task)
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
