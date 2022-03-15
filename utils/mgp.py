import asyncio
import logging
import urllib
from typing import Union, List

import requests
from bs4 import BeautifulSoup

from models.creators import Person

BASE = "https://zh.moegirl.org.cn/Template:{}"


def producer_template_exists(name: str) -> bool:
    url = BASE.format(urllib.parse.quote(name))
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    result = soup.find("div", {"id", "mw-normal-catlinks"})
    if not result:
        return False
    cats = result.find_all("a")
    for cat in cats:
        if cat.text == "音乐家模板" or cat.text == "虚拟歌手音乐人模板":
            return True
    return False


async def check_template_names(names: List[str]) -> Union[str, None]:
    for name in names:
        if producer_template_exists(name):
            return name
    return None


async def get_producer_templates(producers: List[Person]) -> List[str]:
    logging.info("Fetching producer templates for " + ", ".join([p.name for p in producers]))
    result = []
    for producer in producers:
        names = [producer.name, *producer.name_eng]
        names.extend([name[:-1] for name in names if name[-1] == 'P'])
        result.append(asyncio.create_task(check_template_names(names)))
    result = [await r for r in result]
    result = [r for r in result if r]
    return result
