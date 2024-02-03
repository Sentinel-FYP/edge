from video import Video
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", type=str, help="path of log file")
    parser.add_argument("video_path", type=str, help="path of video file")
    parser.add_argument("thread_name", type=str, help="thread name")
    args = parser.parse_args()

    def get_predictions(thread_name):
        predictions = []
        with open(args.log_path) as log:
            for line in log:
                if "prediction" in line and thread_name in line:
                    label = line.split(":")[-2].strip()
                    prob = line.split(":")[-1].strip()
                    predictions.append(f"{label}: {prob}")
        return predictions
    video = Video(args.video_path, output_size=(172, 172))
    predictions = get_predictions(args.thread_name)

    for i, frame in enumerate(video.get_frames(show=True)):
        video.text = predictions[i]
