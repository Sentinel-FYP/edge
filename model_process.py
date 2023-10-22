from threading import Thread, Event, get_ident
from queue import Queue
from model import Model
import logging
from video import Video
from timeit import default_timer as timer
import tensorflow as tf


class ModelThread(Thread):
    def __init__(self, video_path):
        Thread.__init__(self)
        logging.basicConfig(filename=f"logs/{__name__}.log", filemode='w',
                            format="%(threadName)s | %(message)s",
                            level=logging.INFO)
        self.frames = Queue()
        self.video = Video(video_path, output_size=(172, 172))
        self.predictions = Queue()
        self.terminate_event = Event()
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Model thread started")
        self.logger.info("Loading Model")
        model = Model("saved_models/a0_stream_5.0.tflite",
                      clip_length=64, output_size=(172, 172))
        self.logger.info("Loaded Model")
        self.logger.info(f"video : {self.video.path}")
        for frame in self.video.get_frames(show=False):
            if self.terminate_event.is_set():
                break
            start = timer()
            model.feed_frame(frame)
            end = timer()
            self.logger.info(f"prediction : {model.prediction}")
            self.logger.info(f"latency : {end - start}")
            self.predictions.put(model.prediction)

        self.logger.info("Model thread terminated")
        self.terminate_event.set()

    def terminate(self):
        self.terminate_event.set()
