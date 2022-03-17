from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from models.color import ColorScheme
from models.creators import Creators, Person
from models.video import Video
from utils.helpers import prompt_response, prompt_multiline, prompt_choices, prompt_number
from utils.string import is_empty


@dataclass
class Lyrics:
    staff: list = field(default_factory=list)
    translator: str = None
    source_name: str = None
    source_url: str = None
    lyrics: str = None


@dataclass
class Image:
    path: Path
    file_name: str
    source_url: str
    creators: List[Person] = None


@dataclass
class Song:
    name_jap: str
    name_chs: str
    name_other: List[str]
    creators: Creators
    lyrics_jap: str
    lyrics_chs: Lyrics
    image: Image
    videos: List[Video] = field(default_factory=list)
    albums: List[str] = field(default_factory=list)
    colors: ColorScheme = None


def get_manual_lyrics() -> Lyrics:
    name = prompt_response("Source name?")
    url = prompt_response("Source url?")
    translator = prompt_response("Translator name?")
    translation = prompt_multiline("Translation? End with 'END'", terminator="END")
    choice = prompt_choices("Process translation?", ["Sure.", "It's good enough."])
    if choice == 2:
        return Lyrics(translator=translator, source_name=name, source_url=url, lyrics="\n".join(translation))
    group_length = prompt_number("How many lines form a translation group?")
    target_line = prompt_number("Which line contains Chinese lyrics?")
    index = 0
    result = []
    while index < len(translation):
        if is_empty(translation[index]):
            if len(translation) > 0 and not is_empty(result[-1]):
                result.append("")
            index += 1
        else:
            if index + target_line - 1 >= len(translation):
                break
            result.append(translation[index + target_line - 1])
            index += group_length
    return Lyrics(staff=[], translator=translator, source_name=name, source_url=url,
                  lyrics="\n".join(result))