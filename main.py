from model.thread import ModelThread
from memory_profiler import profile
import argparse
from dotenv import load_dotenv
from sio_client import sio_client
import asyncio


# @profile
def spawn_model_process(num_of_processes, video_path):
    processes = []
    for _ in range(num_of_processes):
        model_process = ModelThread(video_path)
        processes.append(model_process)
        model_process.start()

    for p in processes:
        p.join()


async def main():
    load_dotenv()
    sio = await sio_client()
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, help="Number of processes to spawn")
    parser.add_argument("video_path", type=str,
                        help="Path of video to process")
    args = parser.parse_args()
    spawn_model_process(args.n, args.video_path)
    await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
