import logging
import traceback
from dataclasses import dataclass, field

import yaml
from yaml import Loader
from yaml.scanner import ScannerError


@dataclass
class WikitextConfig(yaml.YAMLObject):
    yaml_tag = u'!WikitextConfig'
    lyrics_chs_fail_fast: bool = False
    uploader_note: bool = True


@dataclass
class ColorConfig(yaml.YAMLObject):
    yaml_tag = u'!ColorConfig'
    color_from_image: bool = True
    fg_color_threshold: int = 60
    senyu_mode: bool = False


@dataclass
class ImageConfig(yaml.YAMLObject):
    yaml_tag = u'!ImageConfig'
    download_all: bool = True
    crop: bool = True
    crop_threshold: int = 20


@dataclass
class Config(yaml.YAMLObject):
    yaml_tag = u'!Config'
    wikitext: WikitextConfig = WikitextConfig()
    color: ColorConfig = ColorConfig()
    image: ImageConfig = ImageConfig()


config_xxx = Config()


def load_config(filename: str):
    global config_xxx
    try:
        with open(filename) as f:
            config_xxx = yaml.load(f.read(), Loader=Loader)
    except Exception as e:
        logging.error(e, exc_info=e)
        print("Fallin back to default config.")


def get_config() -> Config:
    return config_xxx
