import re
from datetime import datetime

import requests

from models.video import Video, Site


def auto_lj(s: str) -> str:
    if s.isascii():
        return s
    return "{{lj|" + s + "}}"


def is_empty(s: str) -> bool:
    return s.isspace() or len(s) == 0


def download_file(url, target):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def split(s: str) -> list[str]:
    return re.split("[・/ ]+", s)


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


def prompt_response(prompt: str) -> str:
    print(prompt)
    return input()


def datetime_to_ymd(u: datetime) -> str:
    return f"{u.year}年{u.month}月{u.day}日"


def only_canonical_videos(videos: list[Video]) -> list[Video]:
    return [v for v in videos if v.canonical]


def get_video(videos: list[Video], site: Site):
    for v in videos:
        if v.site == site:
            return v
    return None