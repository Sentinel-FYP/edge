from model.thread import ModelThread
from memory_profiler import profile
import argparse
from dotenv import load_dotenv
from api import set_jwt, get_device
from dotenv import load_dotenv


# @profile
def spawn_model_process(num_of_processes, video_path, deviceMongoId):
    processes = []
    for _ in range(num_of_processes):
        model_process = ModelThread(video_path, deviceMongoId)
        processes.append(model_process)
        model_process.start()

    for p in processes:
        p.join()


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, help="Number of processes to spawn")
    parser.add_argument("video_path", type=str,
                        help="Path of video to process")
    args = parser.parse_args()
    set_jwt()
    device = get_device()
    deviceMongoId = device["_id"]
    spawn_model_process(args.n, args.video_path, deviceMongoId)
