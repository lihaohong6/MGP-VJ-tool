import logging
import re

import requests
from bs4 import BeautifulSoup
import data
from models.song import Lyrics
from utils.helpers import prompt_response, prompt_choices
from utils.string import is_empty


def parse_at_wiki_header(header: str) -> list[tuple[str, str]]:
    lines = header.split("\n")
    result: list[tuple[str, str]] = []
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


def strip_initial_lines(lines: list[str]) -> list[str]:
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


def get_at_wiki_body(name: str, url: str, lang: str) -> Lyrics:
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    # TODO: more robust searching mechanism
    match = soup.find("div", {"id": "wikibody"}).find("ul").find_all("li", limit=1)
    if len(match) == 0 or not match[0].find("a") or match[0].find("a").text != name:
        url = prompt_response(f"Atwiki song in {lang} not found. Supply URL?")
        if is_empty(url):
            return Lyrics()
    else:
        # FIXME: adjust for multiple songs found
        url = "https:" + match[0].find("a").get("href")
    logging.debug("At wiki url " + url)
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    res = parse_body(name, soup.find("div", {"id": "wikibody"}).text)
    return Lyrics(staff=res[0], source_name="VOCALOID中文wiki", source_url=url, lyrics=res[1])


def parse_body(name: str, text: str) -> (list[tuple[str, str]], str):
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


def get_japanese_lyrics(name: str) -> str:
    logging.info("Trying to fetch Japanese lyrics from atwiki.")
    url_jap = f"https://w.atwiki.jp/hmiku/search?andor=and&keyword={name}"
    return get_at_wiki_body(name, url_jap, "Japanese").lyrics


def get_chinese_lyrics(name: str) -> Lyrics:
    logging.info("Trying to fetch Chinese lyrics from atwiki.")
    url_chs = f"https://w.atwiki.jp/vocaloidchly/search?andor=and&keyword={name}"
    return get_at_wiki_body(name, url_chs, "Chinese")


def get_lyrics(name: str) -> (list[tuple[str, str]], str, str):
    raise NotImplementedError("This function is deprecated.")
    url_jap = f"https://w.atwiki.jp/hmiku/search?andor=and&keyword={name}"
    url_chs = f"https://w.atwiki.jp/vocaloidchly/search?andor=and&keyword={name}"
    jap = get_at_wiki_body(name, url_jap, "Japanese")
    chs = get_at_wiki_body(name, url_chs, "Chinese")
    for job, name in chs[0]:
        if job == "翻譯" or job == "翻译":
            jap[0].append((job, name))
    return jap[0], jap[1], chs[1]
