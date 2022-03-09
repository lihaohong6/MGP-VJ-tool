vocaloid_names = {
    '初音ミク': "初音未来",
    '鏡音リン': "镜音铃",
    '鏡音レン': "镜音连",
    '巡音ルカ': "巡音流歌",
    'カイト': "KAITO",
    'メイコ': "MEIKO",
    '音街ウナ': "音街鳗",
    '神威がくぽ': "神威乐步",
    'ブイフラワ': "v flower",
    'イア': "IA",
    'マユ': "MAYU"
}


def name_to_chinese(name: str) -> str:
    if name in vocaloid_names.keys():
        return vocaloid_names[name]
    return name


# 快给我变.jpg
cat_transform = {
    "GUMI": "Megpoid",
    "神威乐步": "Gackpoid"
}


def name_to_cat(name: str) -> str:
    name = name_to_chinese(name)
    if name in cat_transform.keys():
        return cat_transform[name]
    return name
