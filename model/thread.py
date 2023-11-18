from threading import Thread, Event
from queue import Queue
from model.lite import LiteModel, AnomalyType
import logging
from video import Video
from timeit import default_timer as timer
from anomaly_log import AnomalyLog
from datetime import datetime
import cv2
import uuid


class ModelThread(Thread):
    def __init__(self, video_path, deviceMongoId):
        Thread.__init__(self)
        logging.basicConfig(filename=f"logs/{__name__}.log", filemode='w',
                            format="%(threadName)s | %(message)s",
                            level=logging.INFO)
        self.frames = Queue()
        self.video = Video(video_path, output_size=(172, 172))
        self.predictions = Queue()
        self.terminate_event = Event()
        self.deviceMongoId = deviceMongoId
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Model thread started")
        self.logger.info("Loading Model")
        model = LiteModel("saved_models/a0_stream_5.0.tflite",
                          clip_length=64, output_size=(172, 172))
        self.logger.info("Loaded Model")
        self.logger.info(f"video : {self.video.path}")
        start = timer()
        log_sent = False
        anomaly_log = None
        video_writer = None
        for fc, frame in enumerate(self.video.get_frames(show=True)):
            if video_writer is not None:
                video_writer.write(frame)
            if self.terminate_event.is_set():
                break
            model.feed_frame(frame)
            self.logger.info(
                f"prediction : {model.prediction} | probability : {model.probability}")
            self.predictions.put(model.prediction)
            if model.prediction == AnomalyType.ANOMALY and log_sent == True:
                log_sent = False
                anomaly_log = None
            if model.prediction == AnomalyType.ANOMALY and log_sent == False and anomaly_log is None:
                print("Anomaly Detected")
                clipFileName = f"{uuid.uuid4()}.mp4"
                video_writer = cv2.VideoWriter(
                    f"videos/{clipFileName}", cv2.VideoWriter_fourcc(*'mp4v'), self.video.fps, frame.shape[:2][::-1])
                anomaly_log = AnomalyLog(
                    occurredAt=datetime.now().isoformat(), fromDevice=self.deviceMongoId, clipFileName=clipFileName)
            if model.prediction == AnomalyType.NORMAL and log_sent == False and anomaly_log is not None:
                print("Normal detected. posting to server")
                anomaly_log.post_to_server(endedAt=datetime.now().isoformat())
                log_sent = True
                video_writer.release()
                video_writer = None

        if model.prediction == AnomalyType.ANOMALY and log_sent == False and anomaly_log is not None:
            print("Loop Ended. Posting to server")
            anomaly_log.post_to_server(endedAt=datetime.now().isoformat())
            video_writer.release()
            video_writer = None

        end = timer()
        self.logger.info(
            f"total_frames : {fc} | time_taken : {end - start} | latency : {(end - start) / fc}")
        self.logger.info("Model thread terminated")
        self.terminate_event.set()

    def terminate(self):
        self.terminate_event.set()
