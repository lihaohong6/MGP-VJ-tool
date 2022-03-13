import dataclasses
import logging
from functools import reduce
from pathlib import Path
from typing import Union

import cv2
import numpy as np
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


@dataclasses.dataclass
class Color:
    red: int
    green: int
    blue: int

    def __getitem__(self, item: int):
        if item == 0:
            return self.red
        if item == 1:
            return self.green
        if item == 2:
            return self.blue
        raise IndexError("A color only has length 3.")

    def perceived_lightness(self) -> int:
        vR = self.red / 255
        vG = self.green / 255
        vB = self.blue / 255

        def rgb_to_linear(color_channel):
            if color_channel <= 0.04045:
                return color_channel / 12.92
            else:
                return pow(((color_channel + 0.055) / 1.055), 2.4)

        Y = (0.2126 * rgb_to_linear(vR) +
             0.7152 * rgb_to_linear(vG) +
             0.0722 * rgb_to_linear(vB))
        if Y <= (216 / 24389):
            ans = Y * (24389 / 27)
        else:
            ans = pow(Y, (1 / 3)) * 116 - 16
        return round(ans)

    def to_hex(self) -> str:
        return '#%02x%02x%02x' % (self.red, self.green, self.blue)


def text_color(c: Color) -> Color:
    white = Color(255, 255, 255)
    num = c.perceived_lightness()
    if num > white.perceived_lightness() / 2:
        return Color(0, 0, 0)
    return white


@dataclasses.dataclass
class ColorScheme:
    text: Color
    background: Color = None


Coordinate = list[int]


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


def download_thumbnail(videos: list[Video], filename: str) -> Union[str, None]:
    weight = {
        Site.YOUTUBE: 0,
        Site.NICO_NICO: 1,
        Site.BILIBILI: 2,
    }
    videos = sorted(videos, key=lambda vid: weight[vid.site])
    for v in videos:
        if v.thumb_url:
            logging.info("Downloading cover from " + v.site.value + " with url " + v.thumb_url)
            temp_dir = "./output/temp.jpeg"
            download_file(v.thumb_url, temp_dir)
            image_name = f"./output/{filename}"
            remove_black_boarders(temp_dir, image_name)
            return image_name
    return None
