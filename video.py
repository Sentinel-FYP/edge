import tensorflow as tf
import cv2


class Video:
    def __init__(self, path, output_size=(172, 172), text=None):
        self.path = path
        self.src = cv2.VideoCapture(path)
        if not self.src.isOpened():
            raise Exception(f"{path} not found")
        self.output_size = output_size
        self.text = text

    def format_frames(self, frame):
        """
        Pad and resize an image from a video.

        Args:
            frame: Image that needs to resized and padded.
            output_size: Pixel size of the output frame image.

        Return:
            Formatted frame with padding of specified output size.
        """
        output_size = self.output_size
        frame = tf.image.convert_image_dtype(frame, tf.float32)
        frame = tf.image.resize_with_pad(frame, *output_size)
        return frame

    def get_frames(self, show=False):
        src = self.src
        while True:
            ret, frame = src.read()
            if not ret or frame is None:
                break
            if show:
                self.show_frame(frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            yield self.format_frames(frame)
        src.release()
        cv2.destroyAllWindows()

    def show_frame(self, frame):
        font_scale = 1
        thickness = 2
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (0, 255, 0)
        cv2.putText(frame, self.text, (30, 30),
                    font, font_scale, color, thickness)
        cv2.imshow('frame', frame)
        cv2.waitKey(1)
