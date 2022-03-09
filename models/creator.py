from utils.helpers import split
from utils.name_converter import name_to_chinese

CreatorList = list[tuple[str, str]]

VOCALOID_KEYWORD = ['歌', '唄', '演唱']


def get_vocaloid_names(creators: CreatorList) -> list[str]:
    names = []
    for c in creators:
        if c[0] in VOCALOID_KEYWORD:
            names.extend(split(c[1]))
    names = set(names)
    return list(names)


def get_vocaloid_names_chs(creators: CreatorList, wrapper: tuple[str, str] = ("", "")) -> list[str]:
    return [wrapper[0] + name_to_chinese(name) + wrapper[1] for name in get_vocaloid_names(creators)]


def get_producers(creators: CreatorList) -> list[str]:
    keywords = ["作曲", "作詞", "作词"]
    result = []
    for c in creators:
        for k in keywords:
            if c[0] == k:
                result.extend(c[1].split("・"))
    return list(set(result))