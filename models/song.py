from dataclasses import dataclass, field

from typing import List

from models.creators import Creators
from models.video import Video
from models.color import Color, ColorScheme


@dataclass
class Lyrics:
    staff: list = field(default_factory=list)
    translator: str = None
    source_name: str = None
    source_url: str = None
    lyrics: str = None


@dataclass
class Song:
    name_jap: str
    name_chs: str
    name_other: List[str]
    creators: Creators
    lyrics_jap: str
    lyrics_chs: Lyrics
    videos: List[Video] = field(default_factory=list)
    albums: List[str] = field(default_factory=list)
    colors: ColorScheme = None
