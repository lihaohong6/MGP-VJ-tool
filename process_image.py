import argparse
from pathlib import Path

from utils.image import remove_black_boarders


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", dest="input", type=Path)
    parser.add_argument("-o", dest="output", type=Path)
    parser.add_argument("-t", dest="threshold", type=float)
    args = parser.parse_args()
    file_in: Path = args.input
    file_out: Path = args.output
    remove_black_boarders(file_in, file_out, args.threshold)


if __name__ == "__main__":
    main()
