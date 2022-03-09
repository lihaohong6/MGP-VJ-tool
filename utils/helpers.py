import re
from datetime import datetime

import requests

from models.video import Video, Site


def auto_lj(s: str) -> str:
    if s.isascii():
        return s
    return "{{lj|" + s + "}}"


def is_empty(s: str) -> bool:
    return not s or s.isspace() or len(s) == 0


def download_file(url, target):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def split(s: str, regex: str = "[・/，, ]+") -> list[str]:
    return re.split(regex, s)


def prompt_choices(prompt: str, choices: list[str]):
    print(prompt)
    for index, choice in enumerate(choices):
        print(f"{index + 1}: {choice}")
    while True:
        response = input()
        try:
            r = int(response)
            if 1 <= r <= len(choices):
                return r
            else:
                print(f"{r} is not in range.")
        except Exception as e:
            print(e)
            continue


def prompt_response(prompt: str, auto_strip: bool = True) -> str:
    print(prompt)
    s = input()
    if auto_strip:
        return s.strip()
    return s


def prompt_multiline(prompt: str) -> list[str]:
    print(prompt + " End with empty line.")
    res = []
    while True:
        s = input()
        if is_empty(s):
            return res
        res.append(s)


def datetime_to_ymd(u: datetime) -> str:
    return f"{u.year}年{u.month}月{u.day}日"


def only_canonical_videos(videos: list[Video]) -> list[Video]:
    return [v for v in videos if v.canonical]


def get_video(videos: list[Video], site: Site):
    for v in videos:
        if v.site == site:
            return v
    return None


def list_to_str(l: list[str]) -> str:
    if len(l) == 0:
        return ""
    if len(l) == 1:
        return l[0]
    front = "、".join(l[:len(l) - 1])
    return front + "和" + l[-1]


def assert_str_exists(s: str) -> str:
    return s if not is_empty(s) else "ERROR!"
