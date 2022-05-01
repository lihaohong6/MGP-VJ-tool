import asyncio
import json
import logging
import urllib
from typing import Union, List, Tuple

import requests
from bs4 import BeautifulSoup

from models.creators import Person
from utils.string import is_empty

BASE_TEMPLATE = "https://mzh.moegirl.org.cn/api.php?action=parse&format=json" \
                "&page=Template:{}&prop=categories"
BASE_CAT = "https://mzh.moegirl.org.cn/api.php?action=parse&format=json" \
           "&page=Category:{}作品"


def producer_template_exists(name: str) -> bool:
    url = BASE_TEMPLATE.format(urllib.parse.quote(name))
    result = json.loads(requests.get(url).text)
    if 'parse' not in result:
        return False
    cats = result['parse']['categories']
    for cat in cats:
        cat = cat['*']
        if cat == "音乐家模板" or cat == "虚拟歌手音乐人模板":
            return True
    return False


def producer_cat_exists(name: str) -> bool:
    url = BASE_CAT.format(urllib.parse.quote(name))
    result = json.loads(requests.get(url).text)
    return 'parse' in result


async def check_template_names(names: List[str]) -> Union[str, None]:
    for name in names:
        if producer_template_exists(name):
            return name
    return None


async def check_cat_names(names: List[str]) -> Union[str, None]:
    for name in names:
        if producer_cat_exists(name):
            return name
    return None


async def producer_checker(producers: List[Person], task):
    result = []
    for producer in producers:
        names = [producer.name, *producer.name_eng]
        names = [name for name in names if not is_empty(name)]
        names.extend([name[:-1] for name in names if name[-1] == 'P'])
        result.append(asyncio.create_task(task(names)))
    result = [await r for r in result]
    result = [r for r in result if r]
    return result


async def get_producer_templates(producers: List[Person]) -> List[str]:
    logging.info("Fetching producer templates for " + ", ".join([p.name for p in producers]))
    return await producer_checker(producers, check_template_names)


async def get_producer_cats(producers: List[Person]) -> List[str]:
    logging.info("Fetching producer categories for " + ", ".join([p.name for p in producers]))
    return await producer_checker(producers, check_cat_names)


async def get_producer_info(producers: List[Person]) -> Tuple[List[str], List[str]]:
    try:
        task1 = asyncio.create_task(get_producer_templates(producers))
        task2 = asyncio.create_task(get_producer_cats(producers))
        return await task1, await task2
    except Exception as e:
        logging.warning("Error occurred while trying to fetch MGP templates and cats. Continuing...", exc_info=e)
        return [], []
