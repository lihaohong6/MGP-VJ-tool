# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import asyncio
import logging
import os
import sys
import traceback
import webbrowser
from typing import List

from config import data
from config.config import load_config, get_config, application_path, output_path
from models.creators import Person, person_list_to_str, Staff, role_priority
from models.song import Song
from models.video import Site, Video, view_count_from_site, get_video, only_canonical_videos
from utils import login
from utils.helpers import prompt_choices, prompt_response, prompt_multiline
from utils.image import write_to_file
from utils.mgp import get_producer_info
from utils.name_converter import name_to_cat, name_to_chinese
from utils.save_input import setup_save_input
from utils.string import auto_lj, is_empty, datetime_to_ymd, assert_str_exists, join_string
from utils.upload import upload_image
from utils.vocadb import get_song_by_name


def get_song_names(song: Song) -> List[str]:
    # FIXME: disable name_other?
    names = [auto_lj(song.name_jap), song.name_chs if song.name_chs != song.name_jap else None, *song.name_other]
    return [name for name in names if not is_empty(name)]


def videos_to_str(videos: List[Video]) -> List[str]:
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


def create_header(song: Song) -> str:
    videos = sorted(song.videos, key=lambda v: v.uploaded)
    nico = get_video(videos, Site.NICO_NICO)
    top = ""
    if nico and nico.views >= 100000:
        if nico.views >= 1000000:
            top = "{{VOCALOID传说曲题头}}\n"
        else:
            top = "{{VOCALOID殿堂曲题头}}\n"
    if song.name_chs != song.name_jap:
        top += "{{标题替换|" + auto_lj(song.name_jap) + "}}\n"
    sites = {
        Site.NICO_NICO: "nnd_id",
        Site.BILIBILI: "bb_id",
        Site.YOUTUBE: "yt_id"
    }
    video_id = "".join([f"|{sites.get(s)} = {get_video(videos, s).identifier}\n"
                        for s in sites.keys() if get_video(videos, s) and get_video(videos, s).canonical])
    illustrator: List[Person] = song.image.creators
    image_info = ""
    if illustrator:
        # FIXME: what's a good deliminator for illustrators?
        image_info = "Illustration by " + join_string(person_list_to_str(illustrator), mapper=auto_lj, deliminator="、")
    return f"""{top}{{{{VOCALOID_Songbox
|image    = {song.name_chs}封面.jpg
|图片信息 = {image_info}
|颜色    = {f"{song.colors.background.to_hex()};color:{song.colors.text.to_hex()}" if song.colors else ''}
|演唱    = {join_string(song.creators.vocalists_str(), outer_wrapper=("[[", "]]"),
                      mapper=name_to_chinese, deliminator="、")}
|歌曲名称 = {"<br/>".join(get_song_names(song))}
|P主 = {"<br/>".join([auto_lj('[[' + p.name + ']]') for p in song.creators.producers])}
{video_id}|其他资料 = {"<br/>".join(videos_to_str(videos))}
}}}}
"""


def videos_to_str2(videos: List[Video]):
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
            videos_to_str2(videos) + "的[[VOCALOID]]日文原创歌曲。" +
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
    groups: List[Staff] = sorted(song.creators.staff_list(),
                                 key=lambda staff: role_priority(staff[0]))
    groups: List[str] = [f"|group{index + 1} = {g[0]}\n"
                         f"|list{index + 1} = {join_string(person_list_to_str(g[1]), deliminator='<br/>', mapper=auto_lj)}\n"
                         for index, g in enumerate(groups)]
    if song.colors:
        color_scheme = song.colors
        color = f"|lbgcolor={color_scheme.background.to_hex()}\n" \
                f"|ltcolor={color_scheme.text.to_hex()}\n"
    else:
        color = "|lbgcolor=#000\n|ltcolor=white\n"
    return (f"== 歌曲 ==\n"
            "{{VOCALOID Songbox Introduction\n"
            + color +
            f"{''.join(groups)}"
            f"}}}}\n\n{video_player}")


def create_lyrics(song: Song):
    lyrics_chs = song.lyrics_chs
    chs_exist = True if lyrics_chs.lyrics is not None else False
    if chs_exist:
        translation_notice = f"*翻译：{assert_str_exists(lyrics_chs.translator)}"
        if not is_empty(lyrics_chs.source_name) or not is_empty(lyrics_chs.source_url):
            translation_notice += f"<ref>翻译转载自[{assert_str_exists(lyrics_chs.source_url)} " \
                                  f"{assert_str_exists(lyrics_chs.source_name)}]</ref>"
    else:
        translation_notice = "{{求翻译}}"

    return f"""== 歌词 ==
{translation_notice}
{{{{LyricsKai
|lstyle=color:;
|rstyle=color:;
|containerstyle=background:;
|original={assert_str_exists(song.lyrics_jap)}
{f'|translated={song.lyrics_chs.lyrics}' if chs_exist else ''}
}}}}
"""


def create_end(song: Song):
    if get_config().wikitext.producer_template_and_cat:
        list_templates, list_cats = asyncio.run(get_producer_info(song.creators.producers))
        producer_templates = join_string(list_templates, deliminator="",
                                         outer_wrapper=("{{Template:", "}}\n"))
        producer_cats = join_string(list_cats, deliminator="",
                                    outer_wrapper=("[[Category:", "作品]]\n"))
    else:
        producer_templates, producer_cats = "", ""
    vocalist_cat = join_string(song.creators.vocalists_str(),
                               deliminator="", mapper=name_to_cat,
                               outer_wrapper=('[[分类:', '歌曲]]\n'))
    return (producer_templates + """== 注释与外部链接 ==
<references/>
[[分类:日本音乐作品]]
[[分类:使用VOCALOID的歌曲]]\n""" + vocalist_cat + producer_cats)


def setup_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('logs.txt', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(name)s :: %(asctime)s :: %(levelname)-8s :: %(message)s',
                                                '%Y-%m-%d %H:%M:%S'))
    root.addHandler(file_handler)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    root.addHandler(stdout_handler)


def create_uploader_note(song: Song) -> str:
    if not get_config().wikitext.uploader_note:
        return ""
    response = prompt_choices("Uploader note?", choices=["Yes", "No"])
    if response == 2:
        return ""
    japanese = prompt_multiline("Input Japanese version. End input with empty line.",
                                terminator=is_empty)
    japanese = "<br/>".join(japanese)
    chinese = prompt_multiline("Input Chinese version. End input with empty line",
                               terminator=is_empty)
    chinese = "<br/>".join(chinese)
    return f"""{{{{Cquote|{{{{lj|{japanese}}}}}
----
{chinese}
|{auto_lj(song.creators.producers[0].name)}投稿文
}}}}
"""


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    setup_logger()
    load_config(application_path.joinpath("config.yaml"))
    setup_save_input(get_config().save_to_file)
    if get_config().image.auto_upload:
        login.main()
    output_path.mkdir(exist_ok=True)
    data.name_japanese = prompt_response("Japanese name?")
    name_chinese = prompt_response("Chinese name?")
    if is_empty(name_chinese):
        name_chinese = data.name_japanese
    song = get_song_by_name(data.name_japanese, name_chinese)
    if not song:
        raise NotImplementedError("No source of information exists besides VOCADB.")
    for job, name in song.lyrics_chs.staff:
        if job == "翻譯" or job == "翻译":
            song.lyrics_chs.translator = name
            break
    header = create_header(song)
    uploader_note = create_uploader_note(song)
    intro = create_intro(song)
    song_body = create_song(song)
    lyrics = create_lyrics(song)
    end = create_end(song)
    wikitext_dir = output_path.joinpath(f"{song.name_chs}.wikitext")
    write_to_file("\n".join([header, uploader_note, intro, song_body, lyrics, end]),
                  wikitext_dir)
    if song.image.path and get_config().image.auto_upload:
        response = prompt_choices("Upload image to commons?", ["Yes", "No"])
        if response == 1:
            image = song.image
            upload_image(image.path, filename=image.file_name, song_name=name_chinese,
                         authors=image.creators, source_url=image.source_url)
    print("Program ended. Go to output folder for result.")
    webbrowser.open("file://" + str(wikitext_dir.absolute()))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        main()
    except NotImplementedError as e:
        logging.error("NotImplementedError")
        logging.error(str(e))
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(str(e))
        logging.error("This error is unexpected. "
                      "Please go to https://github.com/syccxcc/MGP-VJ-tool/issues to report this issue.")
    input("Press Enter to exit...")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
