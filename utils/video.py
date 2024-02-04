import cv2
import sys


class Video:
    def __init__(self, path, output_size=(172, 172), text=None):
        self.path = path
        self.src = cv2.VideoCapture(path)
        if not self.src.isOpened():
            raise Exception(f"{path} not found")
        self.output_size = output_size
        self.text = text
        self.fps = self.src.get(cv2.CAP_PROP_FPS)

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
            yield frame
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

    def get_fourcc(self):
        fourcc = self.src.get(cv2.CAP_PROP_FOURCC)
        return int(fourcc).to_bytes(4, byteorder=sys.byteorder).decode()
