import asyncio
import json
import logging
import sys
import urllib
from asyncio import Future
from concurrent.futures import as_completed
from json import JSONDecodeError
from typing import Union, List, Tuple, Callable

import requests
from bs4 import BeautifulSoup
from requests_futures.sessions import FuturesSession

from models.creators import Person
from utils.string import is_empty

BASE_TEMPLATE = "https://mzh.moegirl.org.cn/api.php?action=parse&format=json" \
                "&page=Template:{}&prop=categories"
BASE_CAT = "https://mzh.moegirl.org.cn/api.php?action=parse&format=json" \
           "&page=Category:{}作品"


def producer_template_exists(response: str) -> bool:
    result = json.loads(response)
    if 'parse' not in result:
        return False
    cats = result['parse']['categories']
    for cat in cats:
        cat = cat['*']
        if cat == "音乐家模板" or cat == "虚拟歌手音乐人模板":
            return True
    return False


def producer_cat_exists(response: str) -> bool:
    result = json.loads(response)
    return 'parse' in result


def expand_name(producer) -> List[str]:
    names = [producer.name, *producer.name_eng]
    names = [name for name in names if not is_empty(name)]
    names.extend([name[:-1] for name in names if len(name) > 0 and name[-1] == 'P'])
    return names


async def producer_checker(producers: List[Person], base_url: str, predicate: Callable[[str], bool]):
    try:
        with FuturesSession() as session:
            futures: List[Future] = []
            for p in producers:
                names = expand_name(p)
                for name in names:
                    url = base_url.format(urllib.parse.quote(name))
                    futures.append(session.get(url))
                    futures[-1].producer_name = name
            return [response.producer_name for response in as_completed(futures)
                    if not response.exception() and predicate(response.result().text)]
    except Exception as e:
        session.close()
        logging.error("Error occurred.", exc_info=e)
        return []


async def get_producer_templates(producers: List[Person]) -> List[str]:
    logging.info("Fetching producer templates for " + ", ".join([p.name for p in producers]))
    return await producer_checker(producers, BASE_TEMPLATE, producer_template_exists)


async def get_producer_cats(producers: List[Person]) -> List[str]:
    logging.info("Fetching producer categories for " + ", ".join([p.name for p in producers]))
    return await producer_checker(producers, BASE_CAT, producer_cat_exists)


async def get_producer_info(producers: List[Person]) -> Tuple[List[str], List[str]]:
    try:
        task1 = asyncio.create_task(get_producer_templates(producers))
        task2 = asyncio.create_task(get_producer_cats(producers))
        return await task1, await task2
    except Exception as e:
        logging.warning("Error occurred while trying to fetch MGP templates and cats. Continuing...", exc_info=e)
        return [], []
