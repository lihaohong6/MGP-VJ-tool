import logging

import requests
from bs4 import BeautifulSoup
import data


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
    if match.find("a").text != name:
        print("Not found on atwiki")
        return [], None
    url = "https:" + match.find("a").get("href")
    logging.info("At wiki url " + url)
    data.chinese_at_wiki_id = url[url.rfind("pageid=") + 7:]
    logging.info("At wiki id " + data.chinese_at_wiki_id)
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
    for job, name in chs[0]:
        if job == "翻譯" or job == "翻译":
            jap[0].append((job, name))
    for index in range(len(jap[0])):
        name, job = jap[0][index]
        jap[0][index] = (name.strip(), job.strip())
    return jap[0], jap[1], chs[1]
