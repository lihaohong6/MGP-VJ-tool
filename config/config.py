import logging
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Optional

import yaml
from yaml import Loader

from utils.string import is_empty

if getattr(sys, 'frozen', False):
    # The user needs to edit some files, so can't use _MEIPASS
    application_path = Path(os.path.dirname(sys.executable))
else:
    application_path = Path(os.path.dirname(os.path.abspath(__file__)))
    application_path = application_path.joinpath("..")

# os.environ['PYWIKIBOT_DIR'] = str(application_path.absolute())
# this will be changed later when the config is loaded
program_output_path: Path = application_path.joinpath("output")


def get_output_path() -> Path:
    return program_output_path


@dataclass
class WikitextConfig(yaml.YAMLObject):
    yaml_tag = u'!WikitextConfig'
    process_lyrics_jap: bool = True
    furigana_local: bool = True
    furigana_all: bool = True
    lyrics_chs_fail_fast: bool = True
    uploader_note: bool = False
    producer_template_and_cat: bool = True


@dataclass
class ColorConfig(yaml.YAMLObject):
    yaml_tag = u'!ColorConfig'
    color_from_image: bool = True
    fg_color_threshold: int = 60
    senyu_mode: bool = False


@dataclass
class ImageConfig(yaml.YAMLObject):
    yaml_tag = u'!ImageConfig'
    download_cover: bool = False
    download_all: bool = False
    crop: bool = True
    crop_threshold: int = 20
    auto_upload: bool = False


@dataclass
class Config(yaml.YAMLObject):
    yaml_tag = u'!Config'
    save_to_file: str = None
    vocadb_manual: bool = False
    output_dir: str = ""
    wikitext: WikitextConfig = WikitextConfig()
    color: ColorConfig = ColorConfig()
    image: ImageConfig = ImageConfig()


config_xxx = Config()


def is_absolute_directory(d: str) -> Optional[Path]:
    p = platform.system()
    if p == 'Windows':
        match = re.search("[A-Z]:\\\\", d)
        if match.start() == 0:
            return Path(d)
        return None
    # posix
    if "~" in d or d[0] == '/':
        path = Path(d)
        if "~" in d:
            return path.expanduser()
        return path
    return None




def load_config(filename: Union[str, Path]):
    global config_xxx, program_output_path
    try:
        with open(filename, mode="r", encoding="UTF-8") as f:
            config_xxx = yaml.load(f.read(), Loader=Loader)
    except Exception as e:
        logging.debug(e, exc_info=e)
        logging.info("Cannot read config file. Falling back to default config.")
    if is_empty(get_config().output_dir):
        config_xxx.output_dir = "output"
    p = is_absolute_directory(get_config().output_dir)
    if p is not None:
        program_output_path = p
        logging.info("Absolute path detected. Writing output to " + str(program_output_path.resolve()))
    else:
        program_output_path = application_path.joinpath(get_config().output_dir)
        logging.info("Relative path detected. Writing output to " + str(get_output_path().resolve()))
    program_output_path.mkdir(exist_ok=True, parents=True)


def get_config() -> Config:
    return config_xxx
