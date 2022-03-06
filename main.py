# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from utils.helpers import auto_lj
from utils.two_way_dict import TwoWayDict

name_japanese = ""
name_chinese = ""
name_other = ""
bv = ""
nc_id = ""
yt_id = ""
creators: list[tuple[str, str]] = []

vocaloid_names = dict()


def init_names():
    vocaloid_names['初音ミク'] = "初音未来"
    vocaloid_names['IA'] = "IA"
    vocaloid_names['鏡音リン'] = "镜音铃"
    vocaloid_names['鏡音レン'] = "镜音连"
    vocaloid_names['巡音ルカ'] = "巡音流歌"
    vocaloid_names['カイト'] = "KAITO"
    vocaloid_names['メイコ'] = "MEIKO"
    vocaloid_names['GUMI'] = "GUMI"


init_names()


def prompt_choices(prompt: str, choices: list[str]):
    print(prompt)
    for index, choice in enumerate(choices):
        print(f"{index + 1}: {choice}")
    while True:
        response = input()
        try:
            r = int(response)
            if 1 <= r <= len(choices):
                return r
            else:
                print(f"{r} is not in range.")
        except Exception as e:
            print(e)
            continue


def prompt_response(prompt: str) -> str:
    print(prompt)
    return input()


def str_to_date(date: str) -> datetime:
    date = date.split("-")
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    return datetime(year=year, month=month, day=day)


def get_nc_info(vid: str) -> (int, datetime):
    url = f"https://www.nicovideo.jp/watch/{vid}"
    result = requests.get(url).text
    soup = BeautifulSoup(result, "html.parser")
    for s in soup.find_all('script'):
        t: str = s.get_text()
        index_start = t.find("uploadDate")
        if index_start == -1:
            continue
        index_start += len("uploadDate") + 3
        date = t[index_start:index_start + 10]
        return -1, str_to_date(date)
    return -1, datetime.fromtimestamp(0)


def get_bb_info(vid: str) -> (int, datetime):
    url = f"http://api.bilibili.com/x/web-interface/view?bvid={vid}"
    response = json.loads(requests.get(url).text)
    epoch_time = int(response['data']['pubdate'])
    return -1, datetime.fromtimestamp(epoch_time)


def get_yt_info(vid: str) -> (int, datetime):
    url = 'https://www.youtube.com/watch?v=' + vid
    text = requests.get(url).text
    soup = BeautifulSoup(text, "html.parser")
    views = int(soup.select_one('meta[itemprop="interactionCount"][content]')['content'])
    date = str_to_date(soup.select_one('meta[itemprop="datePublished"][content]')['content'])
    return views, date


def parse_at_wiki_header(header: str) -> list[tuple[str, str]]:
    lines = header.split("\n")
    result: list[tuple[str, str]] = []
    for line in lines:
        index = line.find("：")
        if index != -1:
            result.append((line[:index], line[index + 1:]))
    return result


def parse_at_wiki_body(body: str) -> str:
    lines = body.split("\n")
    result = []
    index = 0
    while index < len(lines):
        if not lines[index].isspace():
            break
        index += 1
    state = 0
    while index < len(lines):
        if len(lines[index]) == 0 or lines[index].isspace():
            state += 1
        else:
            if state > 2:
                result.append("")
            result.append(lines[index])
            state = 0
        index += 1
    return "\n".join(result)


def get_at_wiki_body(name: str, url: str) -> (list[tuple[str, str]], str):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    # TODO: more robust searching mechanism
    match = soup.find("div", {"id": "wikibody"}).find("ul").find_all("li")[0]
    url = "https:" + match.find("a").get("href")
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    return parse_body(name, soup.find("div", {"id": "wikibody"}).text)


def parse_body(name: str, text: str) -> (list[tuple[str, str]], str):
    index_comment = text.find("\nコメント\n")
    if index_comment != -1:
        text = text[:index_comment]
    colon_index = text.rfind("：")
    divider = text.find("\n", colon_index)
    header = text[:divider]
    body = text[divider:]
    keywords = ["ブロマガより転載", "\n歌詞\n", "\n" + name + "\n"]
    index = max([body.find(k) for k in keywords])
    if index == -1:
        index = 0
    index = body.find("\n", index) + 1
    body = body[index:]
    return parse_at_wiki_header(header), parse_at_wiki_body(body)


def get_lyrics(name: str) -> (list[tuple[str, str]], str, str):
    url_jap = f"https://w.atwiki.jp/hmiku/search?andor=and&keyword={name}"
    url_chs = f"https://w.atwiki.jp/vocaloidchly/search?andor=and&keyword={name}"
    jap = get_at_wiki_body(name, url_jap)
    chs = get_at_wiki_body(name, url_chs)
    return chs[0], jap[1], chs[1]


def get_vocaloid_names() -> list[str]:
    names = []
    for c in creators:
        if c[0] == '歌':
            names.extend(c[1].split("・"))
    names = set(names)
    return list(names)


def name_to_chinese(name: str) -> str:
    if name in vocaloid_names.keys():
        return vocaloid_names[name]
    return name


def get_song_names() -> list[str]:
    names = [auto_lj(name_japanese), *re.split("[，,]+", name_other)]
    if name_chinese != name_japanese:
        names.append(name_chinese)
    names = [name for name in names if len(name) != 0 and not name.isspace()]
    return list(set(names))


def get_producers() -> list[str]:
    keywords = ["作曲", "作詞"]
    result = []
    for c in creators:
        for k in keywords:
            if c[0] == k:
                result.extend(c[1].split("・"))
    return list(set(result))


def create_header() -> str:
    return f"""{{{{VOCALOID_Songbox
|image    = {name_chinese}封面.jpg
|图片信息 = 
|颜色     = 
|演唱     = {"、".join([f"[[{name_to_chinese(name)}]]" for name in get_vocaloid_names()])}
|歌曲名称 = {"<br/>".join(get_song_names())}
|P主 = {"<br/>".join(['[[' + p + ']]' for p in get_producers()])}
|nnd_id   = {nc_id}
|yt_id    = {yt_id}
|bb_id    = {bv}
|其他资料 = 于2015年5月8日投稿至niconico，再生数为{{NiconicoCount|id=sm26209559}}<br/>于2017年10月5日投稿人声本家至YouTube，再生数为114,000+
}}}}
"""


def main():
    global name_japanese, name_chinese, name_other, creators, bv, nc_id, yt_id
    name_japanese = prompt_response("Japanese name?")
    name_chinese = prompt_response("Chinese name?")
    name_other = prompt_response("Other names?")
    creators, lyrics_jap, lyrics_chs = get_lyrics(name_japanese)
    bv = prompt_response("Bilibili link?")
    nc_id = prompt_response("NicoNico link?")
    yt_id = prompt_response("YouTube link?")
    print(create_header())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
