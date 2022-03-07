# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import re
from pathlib import Path

from data import chinese_at_wiki_id
from models.video import Site, video_from_site, Video, view_count_from_site
from utils.at_wiki import get_lyrics
from utils.helpers import auto_lj, download_file, is_empty, prompt_choices, prompt_response, datetime_to_ymd, \
    only_canonical_videos, get_video

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


def get_vocaloid_names() -> list[str]:
    names = []
    for c in creators:
        if c[0] == '歌' or c[0] == '唄':
            names.extend(c[1].split("・"))
    names = set(names)
    return list(names)


def get_vocaloid_names_chs() -> list[str]:
    return [name_to_chinese(name) for name in get_vocaloid_names()]


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


def videos_to_str(videos: list[Video]) -> list[str]:
    videos = only_canonical_videos(videos)
    result = []
    for i in range(len(videos)):
        if i == 0 or videos[i].uploaded != videos[i - 1].uploaded:
            date = datetime_to_ymd(videos[i].uploaded)
        else:
            date = "同日"

        s = f"于{date}投稿至{videos[i].site.value}，再生数为{view_count_from_site(videos[i])}"
        result.append(s)
    return result


def create_header(videos: list[Video]) -> str:
    top = ""
    nico = get_video(videos, Site.NICO_NICO)
    if nico and nico.views >= 100000:
        top = "{{VOCALOID殿堂曲题头}}"
    sites = {
        Site.NICO_NICO: "nnd_id",
        Site.BILIBILI: "bb_id",
        Site.YOUTUBE: "yt_id"
    }
    video_id = "".join([f"|{sites.get(s)} = {get_video(videos, s).identifier}\n"
                        for s in sites.keys() if get_video(videos, s) and get_video(videos, s).canonical])
    return f"""{top}\n{{{{VOCALOID_Songbox
|image    = {name_chinese}封面.jpg
|图片信息 = 
|颜色     = 
|演唱     = {"、".join([f"[[{name_to_chinese(name)}]]" for name in get_vocaloid_names()])}
|歌曲名称 = {"<br/>".join(get_song_names())}
|P主 = {"<br/>".join([auto_lj('[[' + p + ']]') for p in get_producers()])}
{video_id}|其他资料 = {"<br/>".join(videos_to_str(videos))}
}}}}
"""


def list_to_str(l: list[str]) -> str:
    if len(l) == 0:
        return ""
    if len(l) == 1:
        return l[0]
    front = "、".join(l[:len(l) - 1])
    return front + "和" + l[-1]


def create_intro(videos: list[Video]):
    start = "《'''" + auto_lj(name_japanese) + "'''》"
    return f"{start}" \
           f"{'' if name_chinese == name_japanese or name_chinese.isspace() else f'（{name_chinese}）'}" \
           f"是由{auto_lj('[[' + get_producers()[0] + ']]')}于{datetime_to_ymd(videos[0].uploaded)}投稿至[[{videos[0].site.value}]]的日文原创歌曲，" \
           f"由{list_to_str([f'[[{name_to_chinese(n)}]]' for n in get_vocaloid_names()])}演唱。"


def create_song(videos: list[Video]):
    video_player = ""
    for v in videos:
        if v.site == Site.BILIBILI:
            video_player = f"{{{{" \
                           f"bilibiliVideo|id={v.identifier}" \
                           f"}}}}"
    groups = [(job if job != "歌" and job !="唄" else "演唱", name) for job, name in creators]
    groups = [f"|group{index + 1} = {g[0]}\n"
              f"|list{index + 1} = {auto_lj(g[1])}\n"
              for index, g in enumerate(groups)]
    return f"== 歌曲 ==\n" \
           f"{{{{VOCALOID Songbox Introduction\n" \
           f"|lbgcolor=#000\n|ltcolor=white\n" \
           f"{''.join(groups)}" \
           f"}}}}\n\n{video_player}"


def create_lyrics(lyrics_jap: str, lyrics_chs: str, translator: str):
    chs_exist = True if lyrics_chs else False
    if chs_exist:
        translation_notice = f"*翻译：{translator if translator else 'ERROR!'}" \
                             f"<ref>翻译转载自[https://w.atwiki.jp/vocaloidchly/pages/{chinese_at_wiki_id}.html " \
                             f"VOCALOID中文歌词wiki]</ref>"
    else:
        translation_notice = "{{求翻译}}"

    return f"== 歌词 ==\n" \
           f"{translation_notice}\n" \
           f"{{{{LyricsKai\n" \
           f"|original={lyrics_jap}\n" \
           f"{f'|translated={lyrics_chs}' if lyrics_chs else ''}\n" \
           f"}}}}"


def create_end():
    return """== 注释与外部链接 ==
<references/>
[[分类:日本音乐作品]]
[[分类:使用VOCALOID的歌曲]]\n""" + \
           "\n".join([f'[[分类:{name}歌曲]]'
                      for name in get_vocaloid_names_chs()])


def main():
    global name_japanese, name_chinese, name_other, creators, bv, nc_id, yt_id
    name_japanese = prompt_response("Japanese name?")
    name_chinese = prompt_response("Chinese name?")
    if is_empty(name_chinese):
        name_chinese = name_japanese
    name_other = prompt_response("Other names?")
    creators, lyrics_jap, lyrics_chs = get_lyrics(name_japanese)
    translator = None
    for job, name in creators:
        if job == "翻譯":
            creators.remove((job, name))
            translator = name
    bv = prompt_response("Bilibili link?")
    if bv.isspace() or len(bv) == 0:
        bv = None
    bv_canonical = True
    if bv:
        bv_canonical = prompt_choices("BV canonical?", ["Yes", "No"])
        bv_canonical = bv_canonical == 1
    nc_id = prompt_response("NicoNico link?")
    yt_id = prompt_response("YouTube link?")
    videos = [(Site.BILIBILI, bv, bv_canonical), (Site.NICO_NICO, nc_id), (Site.YOUTUBE, yt_id)]
    videos = [video_from_site(*video) for video in videos if len(video[1]) > 0 and not video[1].isspace()]
    videos = sorted(videos, key=lambda v: v.uploaded)
    header = create_header(videos)
    intro = create_intro(videos)
    song = create_song(videos)
    lyrics = create_lyrics(lyrics_jap, lyrics_chs, translator)
    end = create_end()
    Path("./output").mkdir(exist_ok=True)
    f = open(f"./output/{name_chinese}.wikitext", "w")
    f.write("\n".join([header, intro, song, lyrics, end]))
    weight = {
        Site.YOUTUBE: 0,
        Site.BILIBILI: 1,
        Site.NICO_NICO: 2
    }
    videos.sort(key=lambda vid: weight[vid.site])
    for v in videos:
        if v.thumb_url:
            print("Downloading cover from " + v.thumb_url)
            download_file(v.thumb_url, f"./output/{name_chinese}封面.jpg")
            break


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
