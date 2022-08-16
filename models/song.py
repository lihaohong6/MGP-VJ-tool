import re
from collections import Counter
from dataclasses import dataclass, field
from itertools import groupby
from pathlib import Path
from typing import List, Dict

from models.color import ColorScheme
from models.creators import Creators, Person
from models.video import Video
from utils.helpers import prompt_response, prompt_multiline, prompt_choices, prompt_number
from utils.japanese import is_kana, is_kanji
from utils.string import is_empty

import tkinter as tk


@dataclass
class Lyrics:
    staff: list = field(default_factory=list)
    translator: str = None
    source_name: str = None
    source_url: str = None
    lyrics_chs: str = None
    lyrics_jap: str = None
    lyrics_roma: str = None


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
    lyrics: Lyrics
    image: Image
    videos: List[Video] = field(default_factory=list)
    albums: List[str] = field(default_factory=list)
    colors: ColorScheme = None


def process_translation(translation: str, group_length: int, target_line: int) -> str:
    index = 0
    result = []
    lines: List[str] = translation.split("\n")
    while index < len(lines):
        if is_empty(lines[index]):
            if len(lines) > 0 and not is_empty(result[-1]):
                result.append("")
            index += 1
        else:
            if index + target_line - 1 >= len(lines):
                break
            result.append(lines[index + target_line - 1])
            index += group_length
    return "\n".join(result)


def get_text(t: tk.Text) -> str:
    return t.get("1.0", tk.END).strip()


def get_manual_lyrics() -> Lyrics:
    root = tk.Tk("LyricsSelector")
    TRANSLATION_ROW_SPAN = 6
    translation = tk.Text(root, height=40, width=80)
    translation.grid(row=0, rowspan=TRANSLATION_ROW_SPAN)
    input_fields = tk.PanedWindow(root)
    entry_names = ['group_length', 'jap_line', 'chs_line', 'roma_line', 'translator', 'source_name', 'source_url']
    entries: Dict[str, tk.StringVar] = {}
    for index, entry_name in enumerate(entry_names):
        tk.Label(input_fields, text=entry_name).grid(row=index + TRANSLATION_ROW_SPAN)
        v = tk.StringVar()
        e = tk.Entry(input_fields, textvariable=v)
        e.grid(row=index + TRANSLATION_ROW_SPAN, column=1)
        entries[entry_name] = v
    input_fields.grid(row=TRANSLATION_ROW_SPAN)
    jap_label = tk.Label(root, text="jap")
    jap = tk.Text(root, height=10)
    chs_label = tk.Label(root, text="chs")
    chs = tk.Text(root, height=10)
    roma_label = tk.Label(root, text="roma")
    roma = tk.Text(root, height=10)
    buttons = tk.PanedWindow(root)

    def blob_translation(text: str) -> bool:
        jap_lines = []
        chs_lines = []
        blobs = re.split("\n\n+", text)
        for blob in blobs:
            lines = blob.split("\n")
            if len(lines) % 2 != 0:
                return False
            half = len(lines) // 2
            jap_lines.extend(lines[:half])
            chs_lines.extend(lines[half:])
            jap_lines.append("")
            chs_lines.append("")
        jap_text = "\n".join(jap_lines).strip()
        chs_text = "\n".join(chs_lines).strip()
        if any(is_kana(c) for c in chs_text):
            return False
        jap.replace("1.0", tk.END, jap_text)
        chs.replace("1.0", tk.END, chs_text)
        return True

    def auto_line_numbers():
        translation_text: str = get_text(translation)
        if blob_translation(translation_text):
            return
        groups = [len(list(repeat)) for char, repeat in groupby(translation_text) if char == '\n']
        possibilities = list(Counter(groups).keys())
        text = translation_text
        while len(possibilities) > 0:
            text = text.split("\n" * possibilities[-1])
            for section in text:
                if len(section.split("\n")) != len(text[0].split("\n")):
                    break
            else:
                break
            text = text[0].strip()
            possibilities.pop()
        if len(possibilities) == 0:
            print("Failed...")
            return
        group_length = len(text[0].split("\n")) + 1
        entries['group_length'].set(str(group_length))
        section1 = translation_text.split("\n")[0:group_length]
        for line_number, line in enumerate(section1):
            if any([is_kana(c) for c in line]):
                entries['jap_line'].set(str(line_number + 1))
            if any([is_kanji(c) for c in line]) and all([not is_kana(c) for c in line]):
                entries['chs_line'].set(str(line_number + 1))
            if all([c.isascii() for c in line]) and not is_empty(line):
                entries['roma_line'].set(str(line_number + 1))
        convert_translation()

    auto = tk.Button(buttons, text="auto", command=auto_line_numbers)

    def convert_translation():
        translation_text: str = translation.get("1.0", tk.END).strip()
        group_length = int(entries['group_length'].get())
        chs_line = int(entries['chs_line'].get())
        chs.replace("1.0", tk.END, process_translation(translation_text, group_length, chs_line))
        if not is_empty(entries['jap_line'].get()):
            jap_line = int(entries['jap_line'].get())
            jap.replace("1.0", tk.END, process_translation(translation_text, group_length, jap_line))
        if not is_empty(entries['roma_line'].get()):
            roma_line = int(entries['roma_line'].get())
            roma.replace("1.0", tk.END, process_translation(translation_text, group_length, roma_line))

    convert = tk.Button(buttons, text="convert", command=convert_translation)

    result = Lyrics()

    def destroy():
        nonlocal result
        result = Lyrics(translator=entries['translator'].get(), source_name=entries['source_name'].get(),
                        source_url=entries['source_url'].get(),
                        lyrics_chs=get_text(chs), lyrics_jap=get_text(jap), lyrics_roma=get_text(roma))
        root.destroy()

    confirm = tk.Button(buttons, text="done", command=destroy)
    col_2_widgets: List = [jap_label, jap, chs_label, chs, roma_label, roma, buttons, auto, convert, confirm]
    for index, w in enumerate(col_2_widgets):
        w.grid(row=index, column=2)
    root.mainloop()
    return result
