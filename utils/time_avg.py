import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str, help="path of log file")
    args = parser.parse_args()

    with open(args.path) as log:
        for line in log:
            if "total_frames" in line:
                print(line)
