import logging
import re
from collections import Counter
from datetime import datetime
from itertools import groupby
from typing import Union, Callable, Tuple, List


def auto_lj(s: str) -> str:
    if s.isascii():
        return s
    return "{{lj|" + s + "}}"


def is_empty(s: str) -> bool:
    return not s or s.isspace() or len(s) == 0


def split(s: str, regex: str = "[・/，, ]+") -> List[str]:
    return re.split(regex, s)


def datetime_to_ymd(u: datetime) -> str:
    return f"{u.year}年{u.month}月{u.day}日"


def assert_str_exists(s: str) -> str:
    return s if not is_empty(s) else ""


def split_number(num: int) -> str:
    s = str(num)
    chunks = []
    index = len(s) - 3
    while index > 0:
        chunks.insert(0, s[index:index + 3])
        index -= 3
    chunks.insert(0, s[0:index + 3])
    if num >= 100000:
        chunks[-1] = "000+"
    return ",".join(chunks)


def join_string(lst: list, deliminator: Union[str, Tuple[str, str]] = ("、", "和"),
                inner_wrapper: Tuple[str, str] = ("", ""), outer_wrapper: Tuple[str, str] = ("", ""),
                mapper: Callable = lambda x: x) -> str:
    if isinstance(deliminator, str):
        deliminator = (deliminator, deliminator)
    lst = [(outer_wrapper[0] + mapper(inner_wrapper[0] + elem + inner_wrapper[1]) + outer_wrapper[1]) for elem in lst]
    if len(lst) == 0:
        return ""
    if len(lst) == 1:
        return lst[0]
    front = deliminator[0].join(lst[:len(lst) - 1])
    return front + deliminator[1] + lst[-1]


def process_lyrics_jap(lyrics: str) -> str:
    if is_empty(lyrics):
        return ""
    lyrics = lyrics.replace("\r", "")
    groups = [len(list(repeat)) for char, repeat in groupby(lyrics) if char == '\n']
    total = len(groups)
    counter = Counter(groups)
    if counter.get(1, 0) < total / 2:
        logging.info("Too many newlines. Trying to remove them.")
        divider = max(counter.keys(), key=counter.get)
        # newline chars below the divider -> one line; above the divider -> two lines
        sections = re.split("\n" * divider + "\n+", lyrics)
        lyrics = "\n\n".join(["\n".join(re.split("\n+", section)) for section in sections])
    return lyrics
