import math
from typing import Union, Callable, List

import requests

from config.config import get_config
from utils.save_input import save_input
from utils.string import is_empty


def get_input() -> str:
    s = input()
    save_input(s)
    return s


def prompt_response(prompt: str, auto_strip: bool = True,
                    validity_checker: Callable[[str], bool] = lambda x: True) -> str:
    print(prompt)
    while True:
        s = get_input()
        if auto_strip:
            s = s.strip()
        if validity_checker(s):
            return s


def get_number_validity_checker(start: int, end: int) -> Callable[[str], bool]:
    def validity_checker(response: str):
        try:
            r = int(response)
            if start <= r <= end:
                return True
            else:
                print(f"{r} is not in range.")
        except Exception as e:
            print(e)
            return False

    return validity_checker


def prompt_choices(prompt: str, choices: List[str], allow_zero: bool = False) -> int:
    prompt += "\n" + "\n".join([f"{index + 1}: {choice}"
                                for index, choice in enumerate(choices)])
    min_val = 0 if allow_zero else 1
    return int(prompt_response(prompt, validity_checker=get_number_validity_checker(min_val, len(choices))))


def prompt_number(prompt: str, start: int = -math.inf, end: int = math.inf) -> int:
    return int(prompt_response(prompt, validity_checker=get_number_validity_checker(start, end)))


def prompt_multiline(prompt: str, terminator: Union[Callable[[str], bool], str] = is_empty,
                     auto_strip: bool = True) -> List[str]:
    if isinstance(terminator, str):
        string = terminator

        def t(x: str): return x == string

        terminator = t
    print(prompt)
    res = []
    while True:
        s = get_input()
        if terminator(s):
            return res
        if auto_strip:
            s = s.strip()
        res.append(s)


def http_get(url: str, use_proxy: bool, **kwargs):
    if use_proxy and get_config().proxies:
        proxies = {
            'https': get_config().proxies,
            'http': get_config().proxies
        }
    else:
        proxies = None
    return requests.get(url, proxies=proxies, **kwargs)
