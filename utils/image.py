import logging
import tkinter
from pathlib import Path
from tkinter import Tk, ttk, messagebox
from typing import Union, List, Tuple, Optional

import numpy as np
import requests
from PIL import Image, ImageOps, ImageTk

from config.config import get_config, output_path
from models.color import Color, get_text_color, ColorScheme, black, white
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


def remove_black_boarders(image_in: Union[str, Path], image_out: Union[str, Path], crop_threshold: float):
    img = Image.open(image_in)
    gray = ImageOps.grayscale(img)
    img = np.array(img)
    gray = np.array(gray)

    # use np to sum rows until row sum exceeds a threshold
    row_sums = gray.sum(axis=1) / len(gray[0])
    column_sums = gray.sum(axis=0) / len(gray)

    def get_nums(arr) -> Tuple[int, int]:
        start = next((index for index, x in enumerate(arr) if x >= crop_threshold), 0)
        end = len(arr) - next((index for index, x in enumerate(reversed(arr)) if x >= crop_threshold), 0) - 1
        return start, end

    y1, y2 = get_nums(row_sums)
    x1, x2 = get_nums(column_sums)
    crop = Image.fromarray(img[y1:y2, x1:x2])
    crop.save(image_out)


def image_size(image: Union[str, Path]) -> int:
    img = Image.open(image)
    width, height = img.size
    return height * width


def pick_color(image_in: [str, Path], image_out: [str, Path]) -> ColorScheme:
    remove_black_boarders(image_in, image_out, get_config().image.crop_threshold)
    root = Tk()
    bg_color: Color = black()
    fg_color: Color = white()
    color_mode = 1
    auto_fg = False
    img = Image.open(image_out)
    image_label: Union[tkinter.Label, None] = None
    img_pixels = img.load()
    crop_threshold = tkinter.Entry(root, width=5)
    crop_threshold.insert(0, str(get_config().image.crop_threshold))
    crop_threshold.place(x=600, y=5)
    root.geometry("1280x720")
    root.resizable(True, True)

    def update_preview():
        nonlocal fg_color
        if auto_fg:
            fg_color = get_text_color(bg_color)
        text = tkinter.Label(root, text="测试文字", bg=bg_color.to_hex(), fg=fg_color.to_hex())
        text.config(font=("", 24))
        text.place(x=10, y=10)
        text = tkinter.Label(root, text="文字颜色模式" if color_mode == 1 else "背景颜色模式")
        text.place(x=280, y=5)
        tkinter.Label(root, text="文字：" + fg_color.to_hex() + "\n" + "背景：" + bg_color.to_hex()) \
            .place(x=400, y=10)

    def change_color_mode():
        nonlocal color_mode
        color_mode = 3 - color_mode
        update_preview()

    def click_event(event):
        nonlocal fg_color, bg_color
        selected = Color(*img_pixels[event.x, event.y])
        if color_mode == 1:
            fg_color = selected
        else:
            bg_color = selected
        update_preview()

    def display_image(parent, image: [str, Path]):
        nonlocal img, img_pixels
        img = Image.open(image)
        img_pixels = img.load()
        width, height = img.size
        img = ImageTk.PhotoImage(img)
        nonlocal image_label
        if image_label is not None:
            image_label.destroy()
        image_label = tkinter.Label(image=img)
        image_label.image = img
        image_label.place(in_=parent, x=0, y=60)
        image_label.bind('<Button-1>', click_event)

    def reprocess_image():
        threshold: str = crop_threshold.get()
        threshold = threshold.strip()
        if threshold.isdigit() and 0 <= int(threshold) <= 255:
            remove_black_boarders(image_in, image_out, int(threshold))
            display_image(root, image_out)
        else:
            messagebox.showerror("非法数值", "输入的" + threshold + "不是0到255间的数字")

    def toggle_auto_fg():
        nonlocal auto_fg
        auto_fg = not auto_fg
        update_preview()

    def run_color_picker(image: [str, Path]):
        display_image(root, image)
        exit_button = ttk.Button(root, text="退出", command=root.destroy)
        exit_button.place(x=500, y=5)
        mode_button = ttk.Button(root, text="切换模式", command=change_color_mode)
        mode_button.place(x=280, y=25)
        auto_fg_button = ttk.Button(root, text="自动生成文字颜色", command=toggle_auto_fg)
        auto_fg_button.place(x=120, y=10)
        reprocess_button = ttk.Button(root, text="重新处理黑边", command=reprocess_image)
        reprocess_button.place(x=650, y=5)
        update_preview()
        root.mainloop()

    run_color_picker(image_out)
    return ColorScheme(background=bg_color, text=fg_color)


def download_image(url: str, site: Site, index: int) -> Union[Path, None]:
    try:
        temp_dir = output_path.joinpath("temp.jpeg")
        logging.info("Downloading cover from " + site.value + " with url " + url)
        download_file(url, temp_dir)
        image_name = output_path.joinpath(f"temp{index}.jpeg")
        image_name.unlink(missing_ok=True)
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
    target.unlink(missing_ok=True)
    return result[0][0].rename(target), result[0][1]


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
    target.unlink(missing_ok=True)
    if len(candidates) == 0:
        return None
    elif len(candidates) == 1:
        return candidates[0][0].rename(target), candidates[0][1]
    candidates = sorted([(c, image_size(c[0])) for c in candidates], key=lambda c: c[1])
    return candidates[-1][0][0].rename(target), candidates[-1][0][1]
