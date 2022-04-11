import logging
from dataclasses import dataclass

import yaml
from yaml import Loader


@dataclass
class WikitextConfig(yaml.YAMLObject):
    yaml_tag = u'!WikitextConfig'
    process_lyrics_jap: bool = True
    furigana_local: bool = True
    furigana_all: bool = True
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
    download_all: bool = False
    crop: bool = True
    crop_threshold: int = 20
    auto_upload: bool = False


@dataclass
class Config(yaml.YAMLObject):
    yaml_tag = u'!Config'
    save_to_file: str = None
    wikitext: WikitextConfig = WikitextConfig()
    color: ColorConfig = ColorConfig()
    image: ImageConfig = ImageConfig()


config_xxx = Config()


def load_config(filename: str):
    global config_xxx
    try:
        with open(filename, mode="r", encoding="UTF-8") as f:
            config_xxx = yaml.load(f.read(), Loader=Loader)
    except Exception as e:
        logging.debug(e, exc_info=e)
        logging.info("Cannot read config file. Falling back to default config.")


def get_config() -> Config:
    return config_xxx
