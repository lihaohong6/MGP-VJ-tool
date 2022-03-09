vocaloid_names = {
    '初音ミク': "初音未来",
    '鏡音リン': "镜音铃",
    '鏡音レン': "镜音连",
    '巡音ルカ': "巡音流歌",
    'カイト': "KAITO",
    'メイコ': "MEIKO"
}


def name_to_chinese(name: str) -> str:
    if name in vocaloid_names.keys():
        return vocaloid_names[name]
    return name
