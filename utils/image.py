import logging
from functools import reduce
from pathlib import Path
from typing import Union

import cv2
import requests

from config.config import get_config
from models.color import Color
from models.video import Video, Site


def download_file(url: str, target: Union[str, Path]) -> bool:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return True


def write_to_file(output: str, filename: str):
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
    _, thresh = cv2.threshold(gray, get_config().image.crop_threshold, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    x, y, w, h = reduce(
        bigger_rect,
        [cv2.boundingRect(cnt)
         for cnt in contours])
    crop = img[y:y + h, x:x + w]
    cv2.imwrite(image_out, crop)


Coordinate = list[int]


def image_size(image: str) -> int:
    img = cv2.imread(image)
    height, width, *rest = img.shape
    return height * width


def select_pixel(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        param[0] = x
        param[1] = y


def pick_color(image: str) -> Color:
    image = cv2.imread(image)
    window_name = "Click on the Image to Select a Color"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    target = Coordinate([-1, -1])
    cv2.setMouseCallback(window_name, select_pixel, param=target)
    cv2.imshow(window_name, image)
    while True:
        if cv2.waitKey(10) != -1:
            break
        if target[0] != -1:
            break
    cv2.destroyWindow(window_name)
    if target[0] == -1:
        target = [0, 0]
    color = image[target[1]][target[0]]
    return Color(color[2], color[1], color[0])


def download_image(url: str, site: Site, index: int) -> Union[Path, None]:
    try:
        temp_dir = Path("./output/temp.jpeg")
        logging.info("Downloading cover from " + site.value + " with url " + url)
        download_file(url, temp_dir)
        image_name = Path(f"./output/temp{index}.jpeg")
        if get_config().image.crop:
            remove_black_boarders(str(temp_dir), str(image_name))
        else:
            temp_dir.rename(image_name)
        return image_name
    except Exception as e:
        logging.error("An error occurred while downloading from " + site.value)
        logging.debug("Debugging info: ", exc_info=e)
        return None


def download_all(videos: list[Video], stop_after_success: bool) -> list[Path]:
    candidates = []
    for index, v in enumerate(videos):
        if v.thumb_url:
            image = download_image(v.thumb_url, v.site, index)
            if image:
                if stop_after_success:
                    return [image]
                candidates.append(image)
    return candidates


def download_first(videos: list[Video], target: Path) -> Union[Path, None]:
    result = download_all(videos, stop_after_success=True)
    if len(result) == 0:
        return None
    return result[0].rename(target)


def download_thumbnail(videos: list[Video], filename: str) -> Union[Path, None]:
    weight = {
        Site.YOUTUBE: 0,
        Site.NICO_NICO: 1,
        Site.BILIBILI: 2,
    }
    videos = sorted(videos, key=lambda vid: weight[vid.site])
    target = Path(Path("./output"), Path(filename))
    if not get_config().image.download_all:
        return download_first(videos, target)
    candidates = download_all(videos, stop_after_success=False)
    if len(candidates) == 0:
        return None
    elif len(candidates) == 1:
        return candidates[0].rename(target)
    candidates = sorted([(c, image_size(str(c))) for c in candidates], key=lambda c: c[1])
    return candidates[-1][0].rename(target)
