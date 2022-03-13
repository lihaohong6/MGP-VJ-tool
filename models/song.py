from dataclasses import dataclass, field

from models.creators import Creators
from models.video import Video
from utils.image import Color, ColorScheme


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
    name_other: list[str]
    creators: Creators
    lyrics_jap: str
    lyrics_chs: Lyrics
    videos: list[Video] = field(default_factory=list)
    albums: list[str] = field(default_factory=list)
    colors: ColorScheme = None
