from pathlib import Path
from typing import Optional
from typing.io import IO

from utils.string import is_empty

save_file: Optional[IO] = None


def setup_save_input(file_prefix: Optional[str]):
    global save_file
    if file_prefix is None or is_empty(file_prefix):
        return
    counter = 1
    while True:
        save_file_path = Path(file_prefix + str(counter) + ".txt")
        if not save_file_path.exists():
            save_file = open(save_file_path, "w")
            return
        counter += 1


def save_input(s: str):
    if save_file is not None:
        save_file.write(s)
        save_file.write("\n")
        save_file.flush()
