import logging
import re

import requests
from bs4 import BeautifulSoup
from typing import Tuple, List, Optional

from config import data
from config.config import get_config
from models.song import Lyrics
from utils.helpers import prompt_response
from utils.string import is_empty


def parse_at_wiki_header(header: str) -> List[Tuple[str, str]]:
    lines = header.split("\n")
    result: List[Tuple[str, str]] = []
    for line in lines:
        index = line.find("：")
        if index != -1:
            result.append((line[:index].strip(), line[index + 1:].strip()))
    return result


def is_lyrics(line: str) -> bool:
    line = line.strip()
    return not (line == "歌詞" or
                line == data.name_japanese or
                (data.name_japanese in line and ("オリジナル" in line or
                                                 re.match("[【『]+", line) or
                                                 "歌詞" in line)) or
                (("転載" in line or "转载" in line or "取り" in line)
                 and re.match("[(（]+", line))
                )


def strip_initial_lines(lines: List[str]) -> List[str]:
    index = 0
    while index < len(lines):
        if not is_empty(lines[index]) and is_lyrics(lines[index]):
            return lines[index:]
        index += 1
    return []


def parse_at_wiki_body(body: str) -> str:
    lines = body.split("\n")
    result = []
    lines = strip_initial_lines(lines)
    state = 0
    index = 0
    while index < len(lines):
        if is_empty(lines[index]):
            state += 1
        else:
            if state > 2:
                result.append("")
            result.append(lines[index].strip())
            state = 0
        index += 1
    return "\n".join(result)


def shorten_url(url: str) -> str:
    if "&pageid=" in url:
        page_id = url.split("pageid=")[1]
        url = f"https://w.atwiki.jp/vocaloidchly/pages/{page_id}.html"
    return url


def get_at_wiki_body(name: str, urls: List[str], lang: str, producer: str) -> Optional[Lyrics]:
    try:
        found = None
        for url in urls:
            soup = BeautifulSoup(requests.get(url).text, "html.parser")
            match = soup.find("div", {"id": "wikibody"}).find("ul").find_all("li", limit=1)
            if len(match) > 0 and match[0].find("a") and (match[0].find("a").text == name or
                                                          match[0].find("a").text == name + "/" + producer):
                found = "https:" + match[0].find("a").get("href")
                break
        if found is None:
            return None
        logging.debug("At wiki url " + found)
        soup = BeautifulSoup(requests.get(found).text, "html.parser")
        res = parse_body(name, soup.find("div", {"id": "wikibody"}).text)
        translator = [s for s in res[0] if s[0] == "翻译" or s[0] == "翻譯"]
        if len(translator) == 0:
            translator = "ERROR!"
        else:
            translator = translator[0][1]
        return Lyrics(staff=res[0], source_name="VOCALOID中文wiki", source_url=shorten_url(found), lyrics_chs=res[1],
                      translator=translator)
    except Exception as e:
        logging.error(e)
        logging.error("An error occurred while fetching", lang, "lyrics from atwiki. Falling back...")
        return None


def parse_body(name: str, text: str) -> (List[Tuple[str, str]], str):
    index_comment = text.find("\nコメント\n")
    if index_comment != -1:
        text = text[:index_comment]
    split_index = max(text.find("翻譯"), text.find("翻译"))
    if split_index == -1:
        split_index = text.find("：")
    divider = text.find("\n", split_index)
    header = text[:divider]
    body = text[divider:]
    keywords = ["ブロマガより転載", "\n歌詞\n", "\n" + name + "\n"]
    index = max([body.find(k) for k in keywords])
    if index == -1:
        index = 0
    index = body.find("\n", index) + 1
    body = body[index:]
    return parse_at_wiki_header(header), parse_at_wiki_body(body)


def get_japanese_lyrics(name: str, producer: str = "") -> str:
    logging.info("Trying to fetch Japanese lyrics from atwiki.")
    url_jap = "https://w.atwiki.jp/hmiku/search?andor=and&keyword={}&search_field=source"
    res = get_at_wiki_body(name, [url_jap.format(name + "+" + producer), url_jap.format(name)], "Japanese", producer)
    return res.lyrics_chs if res else ""


def get_chinese_lyrics(name: str, producer: str = "") -> Optional[Lyrics]:
    logging.info("Trying to fetch Chinese lyrics from atwiki.")
    url_chs = "https://w.atwiki.jp/vocaloidchly/search?andor=and&keyword={}&search_field=source"
    return get_at_wiki_body(name, [url_chs.format(name + '+' + producer), url_chs.format(name)], "Chinese", producer)
