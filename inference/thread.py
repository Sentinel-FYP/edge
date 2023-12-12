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
from camera import Camera, CameraDisconnected
from queue import Queue


class ModelThread(Thread):
    def __init__(self, camera: Camera, tasks_queue: Queue, async_loop: asyncio.AbstractEventLoop):
        Thread.__init__(self)
        logging.basicConfig(
            format="%(threadName)s | %(message)s",
            level=logging.INFO)
        self.camera = camera
        self.terminate_event = Event()
        self.logger = logging.getLogger(__name__)
        self.api_client = APIClient()
        self.tasks_queue = tasks_queue
        self.async_loop = async_loop

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        self.logger.info("Model thread started")
        self.logger.info("Loading Model")
        if utils.get_system_ram() > 8 and tf.test.is_gpu_available(cuda_only=True):
            model = GPUModel("saved_models/a0_stream_5.0",
                             clip_length=64, output_size=(172, 172))
        else:
            model = LiteModel("saved_models/a0_stream_5.0.tflite",
                              clip_length=64, output_size=(172, 172))
        self.logger.info("Loaded Model")
        start = timer()
        log_sent = False
        anomaly_log = None
        video_writer = None
        fc = 0
        try:
            while True:
                frame = self.camera.get_frame()
                fc += 1
                if video_writer is not None:
                    video_writer.write(frame)
                if self.terminate_event.is_set():
                    break
                model.feed_frame(frame)
                self.logger.info(
                    f"prediction : {model.prediction} | probability : {model.probability}")
                if model.prediction == AnomalyType.ANOMALY and log_sent == True:
                    log_sent = False
                    anomaly_log = None
                if model.prediction == AnomalyType.ANOMALY and log_sent == False and anomaly_log is None:
                    print("Anomaly Detected")
                    clipFileName = f"videos/{uuid.uuid4()}.mp4"
                    video_writer = cv2.VideoWriter(
                        clipFileName, cv2.VideoWriter_fourcc(*'mp4v'), self.camera.get_fps(), frame.shape[:2][::-1])
                    anomaly_log = AnomalyLog(
                        occurredAt=datetime.now().isoformat(), fromDevice=self.api_client.deviceMongoId, clipFileName=clipFileName)
                if model.prediction == AnomalyType.NORMAL and log_sent == False and anomaly_log is not None:
                    video_writer.release()
                    video_writer = None
                    print("Normal detected. posting to server")
                    anomaly_log.endedAt = datetime.now().isoformat()
                    log_task = self.async_loop.create_task(
                        self.api_client.post_anomaly_log(anomaly_log))
                    self.tasks_queue.put(log_task)
                    log_sent = True
        except CameraDisconnected:
            print("Camera Disconnected. Terminating thread")
        except Exception as e:
            print(e)
        finally:
            if model.prediction == AnomalyType.ANOMALY and log_sent == False and anomaly_log is not None:
                video_writer.release()
                video_writer = None
                print("Loop Ended. Posting to server")
                anomaly_log.endedAt = datetime.now().isoformat()
                log_task = self.async_loop.create_task(
                    self.api_client.post_anomaly_log(anomaly_log))
                self.tasks_queue.put(log_task)
            end = timer()
            self.logger.info(
                f"total_frames : {fc} | time_taken : {end - start} | latency : {(end - start) / fc}")
            self.logger.info("Model thread terminated")
            self.terminate_event.set()
            self.camera.disconnect()

    def terminate(self):
        self.terminate_event.set()
