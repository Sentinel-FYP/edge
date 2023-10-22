from model_process import ModelThread
from memory_profiler import profile
import argparse


@profile
def spawn_model_process(num_of_processes):
    processes = []
    for _ in range(num_of_processes):
        model_process = ModelThread("videos/video.mp4")
        processes.append(model_process)
        model_process.start()

    for p in processes:
        p.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, help="Number of processes to spawn")
    args = parser.parse_args()
    spawn_model_process(args.n)
