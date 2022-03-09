# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import logging
import re
from pathlib import Path

import data
from data import name_japanese, name_chinese
from models.creator import CreatorList, get_vocaloid_names_chs, get_producers, VOCALOID_KEYWORD
from models.video import Site, video_from_site, Video, view_count_from_site
from utils.at_wiki import get_lyrics
from utils.helpers import auto_lj, download_file, is_empty, prompt_choices, prompt_response, datetime_to_ymd, \
    only_canonical_videos, get_video, list_to_str, assert_str_exists, split, prompt_multiline
from utils.name_converter import name_to_cat


def get_song_names(name_other: str) -> list[str]:
    names = [auto_lj(name_japanese), name_chinese, *re.split("[，,]+", name_other)]
    names = [name for name in names if not is_empty(name)]
    return list(set(names))


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


def create_header(videos: list[Video], creators: CreatorList, name_other: str) -> str:
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
|演唱     = {"、".join(get_vocaloid_names_chs(creators, ("[[", "]]")))}
|歌曲名称 = {"<br/>".join(get_song_names(name_other))}
|P主 = {"<br/>".join([auto_lj('[[' + p + ']]') for p in get_producers(creators)])}
{video_id}|其他资料 = {"<br/>".join(videos_to_str(videos))}
}}}}
"""


def create_intro(videos: list[Video], creators: CreatorList):
    start = "《'''" + auto_lj(name_japanese) + "'''》"
    return f"{start}" \
           f"{'' if name_chinese == name_japanese else f'（{name_chinese}）'}" \
           f"是由{auto_lj('[[' + (get_producers(creators)[0] if len(get_producers(creators)) > 0 else 'ERROR') + ']]')}" \
           f"于{datetime_to_ymd(videos[0].uploaded)}投稿至[[{videos[0].site.value}]]的日文原创歌曲，" \
           f"由{assert_str_exists(list_to_str(get_vocaloid_names_chs(creators, ('[[', ']]'))))}演唱。"


def create_song(videos: list[Video], creators: CreatorList):
    video_player = ""
    v = get_video(videos, Site.BILIBILI)
    if v:
        video_player = f"{{{{" \
                       f"bilibiliVideo|id={v.identifier}" \
                       f"}}}}"
    groups = [(job if job not in VOCALOID_KEYWORD else "演唱", name) for job, name in creators]
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
        translation_notice = f"*翻译：{assert_str_exists(translator)}" \
                             f"<ref>翻译转载自[https://w.atwiki.jp/vocaloidchly/pages/{data.chinese_at_wiki_id}.html " \
                             f"VOCALOID中文歌词wiki]</ref>"
    else:
        translation_notice = "{{求翻译}}"

    return f"== 歌词 ==\n" \
           f"{translation_notice}\n" \
           f"{{{{LyricsKai\n" \
           f"|original={assert_str_exists(lyrics_jap)}\n" \
           f"{f'|translated={lyrics_chs}' if lyrics_chs else ''}\n" \
           f"}}}}"


def create_end(creators: CreatorList):
    return """== 注释与外部链接 ==
<references/>
[[分类:日本音乐作品]]
[[分类:使用VOCALOID的歌曲]]\n""" + \
           "\n".join([f'[[分类:{name_to_cat(name)}歌曲]]'
                      for name in get_vocaloid_names_chs(creators)])


def main():
    logging.basicConfig(filename="logs.txt", level=logging.INFO)
    data.name_japanese = prompt_response("Japanese name?")
    data.name_chinese = prompt_response("Chinese name?")
    if is_empty(data.name_chinese):
        data.name_chinese = data.name_japanese
    name_other = prompt_response("Other names?")
    bv = prompt_response("Bilibili link?")
    if bv.isspace() or len(bv) == 0:
        bv = None
    bv_canonical = True
    if bv:
        bv_canonical = prompt_choices("BV canonical?", ["Yes", "No"])
        bv_canonical = bv_canonical == 1
    nc_id = prompt_response("NicoNico link?")
    yt_id = prompt_response("YouTube link?")
    # search AtWiki for lyrics and creators
    creators, lyrics_jap, lyrics_chs = get_lyrics(data.name_japanese)
    if len(creators) == 0:
        r = prompt_multiline("Creators not found. Input manually.")
        colon = ":："
        creators = [(split(c, colon)[0], split(c, colon)[1])
                    for c in r if len(split(c, colon)) >= 2]
    translator = None
    for job, name in creators:
        if job == "翻譯" or job == "翻译":
            creators.remove((job, name))
            translator = name
    videos = [(Site.BILIBILI, bv, bv_canonical), (Site.NICO_NICO, nc_id), (Site.YOUTUBE, yt_id)]
    videos = [video_from_site(*video) for video in videos if not is_empty(video[1])]
    videos = sorted(videos, key=lambda vid: vid.uploaded)
    header = create_header(videos, creators, name_other)
    intro = create_intro(videos, creators)
    song = create_song(videos, creators)
    lyrics = create_lyrics(lyrics_jap, lyrics_chs, translator)
    end = create_end(creators)
    Path("./output").mkdir(exist_ok=True)
    f = open(f"./output/{data.name_chinese}.wikitext", "w")
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
            download_file(v.thumb_url, f"./output/{data.name_chinese}封面.jpg")
            break


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
