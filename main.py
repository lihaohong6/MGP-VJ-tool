# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import logging
import sys
from pathlib import Path
from typing import Union

import data
from models.song import Song
from models.creators import Person, person_list_to_str, Staff, role_priority
from models.video import Site, video_from_site, Video, view_count_from_site
from utils.helpers import download_file, prompt_choices, prompt_response, only_canonical_videos, get_video
from utils.name_converter import name_to_cat, name_to_chinese
from utils.string import auto_lj, is_empty, datetime_to_ymd, assert_str_exists, join_string
from utils.vocadb import get_song_by_name


def get_song_names(song: Song) -> list[str]:
    # FIXME: disable name_other?
    names = [auto_lj(song.name_jap), song.name_chs if song.name_chs != song.name_jap else None, *song.name_other]
    return [name for name in names if not is_empty(name)]


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


def get_people_by_job(staffs: dict, job: str) -> Union[list[Person], None]:
    return staffs.get(job, None)


def create_header(song: Song) -> str:
    videos = sorted(song.videos, key=lambda v: v.uploaded)
    nico = get_video(videos, Site.NICO_NICO)
    top = ""
    if nico and nico.views >= 100000:
        if nico.views >= 1000000:
            top = "{{VOCALOID传说曲题头}}\n"
        else:
            top = "{{VOCALOID殿堂曲题头}}\n"
    sites = {
        Site.NICO_NICO: "nnd_id",
        Site.BILIBILI: "bb_id",
        Site.YOUTUBE: "yt_id"
    }
    video_id = "".join([f"|{sites.get(s)} = {get_video(videos, s).identifier}\n"
                        for s in sites.keys() if get_video(videos, s) and get_video(videos, s).canonical])
    illustrator = get_people_by_job(song.creators.staffs, "曲绘")
    image_info = ""
    if illustrator:
        # FIXME: what's a good deliminator for illustrators?
        image_info = "Illustration by " + join_string(person_list_to_str(illustrator), mapper=auto_lj, deliminator="、")
    return f"""{top}{{{{VOCALOID_Songbox
|image    = {data.name_chinese}封面.jpg
|图片信息 = {image_info}
|颜色     = 
|演唱     = {join_string(song.creators.vocalists_str(), outer_wrapper=("[[", "]]"),
                       mapper=name_to_chinese, deliminator="、")}
|歌曲名称 = {"<br/>".join(get_song_names(song))}
|P主 = {"<br/>".join([auto_lj('[[' + p.name + ']]') for p in song.creators.producers])}
{video_id}|其他资料 = {"<br/>".join(videos_to_str(videos))}
}}}}
"""


def videos_to_str2(videos: list[Video]):
    videos = only_canonical_videos(videos)
    dates = dict()
    for v in videos:
        original = dates.get(v.uploaded, [])
        original.append(v.site.value)
        dates[v.uploaded] = original
    lst = sorted(dates.keys())
    return join_string([
        f"于{datetime_to_ymd(date)}投稿至{join_string(dates[date], outer_wrapper=('[[', ']]'))}"
        for date in lst
    ], deliminator="，")


def create_intro(song: Song):
    nc = song.name_chs
    nj = song.name_jap
    videos = song.videos
    start = "《'''" + auto_lj(nj) + "'''》"
    albums = f"""收录于专辑{join_string(song.albums, mapper=auto_lj, outer_wrapper=("《", "》"))}。""" \
        if len(song.albums) > 0 else ""
    return (start +
            f"{'' if nc == nj else f'（{nc}）'}" +
            f"""是由{join_string(song.creators.producers_str()[:1],
                               inner_wrapper=('[[', ']]'),
                               mapper=auto_lj)}""" +
            videos_to_str2(videos) + "的日文原创歌曲。" +
            f"""由{join_string(song.creators.vocalists_str(),
                              outer_wrapper=('[[', ']]'),
                              mapper=name_to_chinese)}演唱。""" +
            albums)


def create_song(song: Song):
    video_player = ""
    v = get_video(song.videos, Site.BILIBILI)
    if v:
        video_player = f"{{{{" \
                       f"bilibiliVideo|id={v.identifier}" \
                       f"}}}}"
    groups: list[Staff] = sorted(song.creators.staff_list(),
                                 key=lambda staff: role_priority(staff[0]))
    groups: list[str] = [f"|group{index + 1} = {g[0]}\n"
                         f"|list{index + 1} = {join_string(person_list_to_str(g[1]), deliminator='<br/>', mapper=auto_lj)}\n"
                         for index, g in enumerate(groups)]
    return f"== 歌曲 ==\n" \
           f"{{{{VOCALOID Songbox Introduction\n" \
           f"|lbgcolor=#000\n|ltcolor=white\n" \
           f"{''.join(groups)}" \
           f"}}}}\n\n{video_player}"


def create_lyrics(song: Song):
    lyrics_chs = song.lyrics_chs
    chs_exist = True if lyrics_chs.lyrics else False
    if chs_exist:
        translation_notice = f"*翻译：{assert_str_exists(lyrics_chs.translator)}" \
                             f"<ref>翻译转载自[{lyrics_chs.source_url} {lyrics_chs.source_name}]</ref>"
    else:
        translation_notice = "{{求翻译}}"

    return f"== 歌词 ==\n" \
           f"{translation_notice}\n" \
           f"{{{{LyricsKai\n" \
           f"|original={assert_str_exists(song.lyrics_jap)}\n" \
           f"{f'|translated={song.lyrics_chs.lyrics}' if song.lyrics_chs.lyrics else ''}\n" \
           f"}}}}"


def create_end(song: Song):
    return """== 注释与外部链接 ==
<references/>
[[分类:日本音乐作品]]
[[分类:使用VOCALOID的歌曲]]\n""" + \
           join_string(song.creators.vocalists_str(),
                       deliminator="\n", mapper=name_to_cat,
                       outer_wrapper=('[[分类:', '歌曲]]'))


def get_video_bilibili() -> Union[Video, None]:
    bv = prompt_response("Bilibili link?")
    if bv.isspace() or len(bv) == 0:
        return None
    if bv:
        bv_canonical = prompt_choices("BV canonical?", ["Yes", "No"])
        bv_canonical = bv_canonical == 1
        return video_from_site(Site.BILIBILI, bv, bv_canonical)


def setup_logger():
    logging.basicConfig(filename="logs.txt", level=logging.DEBUG,
                        format='%(name)s :: %(asctime)s :: %(levelname)-8s :: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)


def main():
    setup_logger()
    data.name_japanese = prompt_response("Japanese name?")
    data.name_chinese = prompt_response("Chinese name?")
    if is_empty(data.name_chinese):
        data.name_chinese = data.name_japanese
    song = get_song_by_name(data.name_japanese)
    song.name_chs = data.name_chinese
    video_bilibili = get_video_bilibili()
    if video_bilibili:
        song.videos.append(video_bilibili)
    for job, name in song.lyrics_chs.staff:
        if job == "翻譯" or job == "翻译":
            song.lyrics_chs.translator = name
            break
    header = create_header(song)
    intro = create_intro(song)
    song_body = create_song(song)
    lyrics = create_lyrics(song)
    end = create_end(song)
    Path("./output").mkdir(exist_ok=True)
    f = open(f"./output/{data.name_chinese}.wikitext", "w")
    f.write("\n".join([header, intro, song_body, lyrics, end]))
    weight = {
        Site.YOUTUBE: 0,
        Site.BILIBILI: 1,
        Site.NICO_NICO: 2
    }
    videos = song.videos
    videos = sorted(videos, key=lambda vid: weight[vid.site])
    for v in videos:
        if v.thumb_url:
            print("Downloading cover from " + v.site.value + " with url " + v.thumb_url)
            download_file(v.thumb_url, f"./output/{song.name_chs}封面.jpg")
            break
    print("Program ended. Go to output folder for result.")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
