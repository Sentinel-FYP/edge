from collections import defaultdict
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str, help="path of log file")
    args = parser.parse_args()

    processes = defaultdict(lambda: [])
    with open(args.path) as log:
        for line in log:
            if "latency" in line:
                thread_name = line.split("|")[0]
                time = float(line.split(":")[-1])
                processes[thread_name].append(time)

    for thread_name, times in processes.items():
        print(f"{thread_name} avg time: {sum(times) / len(times)}")
