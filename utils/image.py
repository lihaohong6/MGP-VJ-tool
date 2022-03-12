import logging
from functools import reduce
from pathlib import Path
from typing import Union

import cv2
import requests

from models.video import Video, Site


def download_file(url: str, target: Union[str, Path]) -> bool:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return True


def write_to_file(output: str, filename: str):
    Path("./output").mkdir(exist_ok=True)
    f = open(f"./output/{filename}", "w", encoding="UTF-8")
    f.write(output)
    f.close()


def bigger_rect(r1, r2):
    size1 = r1[2] * r1[3]
    size2 = r2[2] * r2[3]
    return r1 if size1 >= size2 else r2


def remove_black_boarders(image_in: str, image_out: str):
    img = cv2.imread(image_in)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    x, y, w, h = reduce(
        bigger_rect,
        [cv2.boundingRect(cnt)
         for cnt in contours])
    crop = img[y:y + h, x:x + w]
    cv2.imwrite(image_out, crop)


def download_thumbnail(videos: list[Video], filename: str):
    weight = {
        Site.YOUTUBE: 0,
        Site.BILIBILI: 1,
        Site.NICO_NICO: 2
    }
    videos = sorted(videos, key=lambda vid: weight[vid.site])
    for v in videos:
        if v.thumb_url:
            logging.info("Downloading cover from " + v.site.value + " with url " + v.thumb_url)
            temp_dir = "./output/temp.jpeg"
            download_file(v.thumb_url, temp_dir)
            remove_black_boarders(temp_dir, f"./output/{filename}")
            break
