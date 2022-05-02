import argparse
import logging
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import Union, List, Tuple, Optional

import cv2
import numpy as np
import requests

from config.config import get_config, output_path
from models.color import Color
from models.video import Video, Site


def download_file(url: str, target: Union[str, Path]) -> bool:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return True


def write_to_file(output: str, filename: Union[str, Path]):
    f = open(filename, "w", encoding="UTF-8")
    f.write(output)
    f.close()


def bigger_rect(r1, r2):
    size1 = r1[2] * r1[3]
    size2 = r2[2] * r2[3]
    return r1 if size1 >= size2 else r2


def remove_black_boarders(image_in: str, image_out: str, crop_threshold: float):
    img = cv2.imread(image_in)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # use np to sum rows until row sum exceeds a threshold
    # no column support for now
    def get_row_num(start: int, step: int) -> int:
        index = start
        while 0 <= index < len(gray):
            s = np.sum(gray[index])
            average = s / len(gray[index])
            if average > crop_threshold:
                return index
            index += step

    y1, y2 = get_row_num(0, 1), get_row_num(len(gray) - 1, -1)
    x1, x2 = 0, len(gray[0])
    crop = img[y1:y2, x1:x2]
    cv2.imwrite(image_out, crop)


@dataclass
class Coordinate:
    x: int
    y: int

    def __getitem__(self, item: int):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        raise RuntimeError("Invalid item")


def image_size(image: str) -> int:
    img = cv2.imread(image)
    height, width, *rest = img.shape
    return height * width


def select_pixel(event, x, y, flags, param: Coordinate):
    if event == cv2.EVENT_LBUTTONDOWN:
        param.x = x
        param.y = y


def pick_color(image: str) -> Color:
    image = cv2.imread(image)
    window_name = "Click on the Image to Select a Color"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    target = Coordinate(-1, -1)
    cv2.setMouseCallback(window_name, select_pixel, param=target)
    height, width, *rest = image.shape
    cv2.resizeWindow(window_name, width, height)
    cv2.imshow(window_name, image)
    while True:
        if cv2.waitKey(10) != -1:
            break
        if target[0] != -1:
            break
    cv2.destroyWindow(window_name)
    cv2.waitKey(1)
    if target[0] == -1:
        logging.warning(f"Selected coordinates are ({target[0]}, {target[1]}), which are not valid.")
        target = [0, 0]
    color = image[target[1]][target[0]]
    color = Color(color[2], color[1], color[0])
    logging.info(f"Selected color with HEX {color.to_hex()}, "
                 f"RGB({color.red}, {color.green}, {color.blue}), "
                 f"and perceived lightness {color.perceived_lightness()}")
    return color


def download_image(url: str, site: Site, index: int) -> Union[Path, None]:
    try:
        temp_dir = output_path.joinpath("temp.jpeg")
        logging.info("Downloading cover from " + site.value + " with url " + url)
        download_file(url, temp_dir)
        image_name = output_path.joinpath(f"temp{index}.jpeg")
        if get_config().image.crop:
            remove_black_boarders(str(temp_dir), str(image_name), get_config().image.crop_threshold)
        else:
            temp_dir.rename(image_name)
        return image_name
    except Exception as e:
        logging.error("An error occurred while downloading from " + site.value)
        logging.debug("Debugging info: ", exc_info=e)
        return None


def download_all(videos: List[Video], stop_after_success: bool) -> List[Tuple[Path, Video]]:
    candidates = []
    for index, v in enumerate(videos):
        if v.thumb_url:
            image = download_image(v.thumb_url, v.site, index)
            if image:
                result = (image, v)
                if stop_after_success:
                    return [result]
                candidates.append(result)
    return candidates


def download_first(videos: List[Video], target: Path) -> Optional[Tuple[Path, Video]]:
    result = download_all(videos, stop_after_success=True)
    if len(result) == 0:
        return None
    result[0][0].rename(target)
    return target, result[0][1]


def download_thumbnail(videos: List[Video], filename: str) -> Optional[Tuple[Path, Video]]:
    weight = {
        Site.YOUTUBE: 0,
        Site.BILIBILI: 1,
        Site.NICO_NICO: 2,
    }
    videos = sorted(videos, key=lambda vid: weight[vid.site])
    target = output_path.joinpath(filename)
    if not get_config().image.download_all:
        return download_first(videos, target)
    candidates = download_all(videos, stop_after_success=False)
    if len(candidates) == 0:
        return None
    elif len(candidates) == 1:
        candidates[0][0].rename(target)
        return target, candidates[0][1]
    candidates = sorted([(c, image_size(str(c[0]))) for c in candidates], key=lambda c: c[1])
    candidates[-1][0][0].rename(target)
    return target, candidates[-1][0][1]
