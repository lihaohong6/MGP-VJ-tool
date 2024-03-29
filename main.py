import asyncio
import logging
import os
import sys
import traceback
import webbrowser
from typing import List

from config import data
from config.config import load_config, get_config, application_path, get_output_path
from models.creators import Person, person_list_to_str, Staff, role_priority
from models.song import Song, Lyrics
from models.video import VideoSite, Video, view_count_from_site, get_video, only_canonical_videos
from utils import login
from utils.helpers import prompt_choices, prompt_response, prompt_multiline
from utils.image import write_to_file
from utils.mgp import get_producer_info
from utils.name_converter import name_to_cat, name_to_chinese, vocaloid_names, UTAU_CHARACTERS, CEVIO_CHARACTERS
from utils.save_input import setup_save_input
from utils.string import auto_lj, is_empty, datetime_to_ymd, assert_str_exists, join_string
from utils.upload import upload_image
from utils.vocadb import get_song_by_name

from i18n.i18n import _


def get_song_names(song: Song) -> List[str]:
    # FIXME: disable name_other?
    names = [auto_lj(song.name_jap), song.name_chs if song.name_chs != song.name_jap else None, *song.name_other]
    return [name for name in names if not is_empty(name)]


def videos_to_str(videos: List[Video]) -> List[str]:
    videos = only_canonical_videos(videos)
    result = []
    for i in range(len(videos)):
        if i == 0 or videos[i].uploaded != videos[i - 1].uploaded:
            date = "于" + datetime_to_ymd(videos[i].uploaded)
        else:
            date = "同日"
        s = f"{date}投稿至{videos[i].site.value}，再生数为{view_count_from_site(videos[i])}"
        result.append(s)
    return result


def create_header(song: Song) -> str:
    videos = sorted(song.videos, key=lambda v: v.uploaded)
    nico = get_video(videos, VideoSite.NICO_NICO)
    top = ""
    if nico and nico.views >= 100000:
        if nico.views >= 1000000:
            top = "{{VOCALOID传说曲题头}}\n"
        else:
            top = "{{VOCALOID殿堂曲题头}}\n"
    if song.name_chs != song.name_jap:
        top += "{{标题替换|" + auto_lj(song.name_jap) + "}}\n"
    sites = {
        VideoSite.NICO_NICO: "nnd_id",
        VideoSite.BILIBILI: "bb_id",
        VideoSite.YOUTUBE: "yt_id"
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
            videos_to_str2(videos) + "的[[VOCALOID]]日语原创歌曲。" +
            f"""由{join_string(song.creators.vocalists_str(),
                              outer_wrapper=('[[', ']]'),
                              mapper=name_to_chinese)}演唱。""" +
            albums)


def create_song(song: Song):
    video_player = ""
    v = get_video(song.videos, VideoSite.BILIBILI)
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
        color = f"|lbgcolor = {color_scheme.background.to_hex()}\n" \
                f"|ltcolor = {color_scheme.text.to_hex()}\n"
    else:
        color = "|lbgcolor = #000\n|ltcolor = white\n"
    return (f"== 歌曲 ==\n"
            "{{VOCALOID Songbox Introduction\n"
            + color +
            f"{''.join(groups)}"
            f"}}}}\n\n{video_player}")


def create_lyrics(lyrics: Lyrics):
    lyrics_chs = lyrics.lyrics_chs
    chs_exist = lyrics_chs is not None
    if chs_exist:
        translation_notice = f"*翻译：{assert_str_exists(lyrics.translator)}"
        if not is_empty(lyrics.source_name) or not is_empty(lyrics.source_url):
            translation_notice += f"<ref>翻译转载自[{assert_str_exists(lyrics.source_url)} " \
                                  f"{assert_str_exists(lyrics.source_name)}]</ref>"
    else:
        translation_notice = ""
    has_roma = not is_empty(lyrics.lyrics_roma)
    return f"""== 歌词 ==
{translation_notice}
{"{{LyricsKai/Roma/button}}" if has_roma else ""}
{{{{LyricsKai{'/Roma' if has_roma else ''}
|lstyle=color:;
|rstyle=color:;
|containerstyle=background:;
|original=
{assert_str_exists(lyrics.lyrics_jap).strip()}
|translated=
{lyrics_chs.strip() if chs_exist else ''}
{("|photrans=" + lyrics.lyrics_roma) if has_roma else ''}}}}}
"""


VOCALOID_TEMPLATES = {'歌爱雪', 'v flower', 'SeeU', '夏语遥', '重音Teto',
                      '爱莲娜·芙缇', '艾可', '赤羽', '诗岸', '苍穹', '海伊',
                      '牧心', 'Minus', '岸晓', 'Infinity', '默辰', '可不', '星界'}
vocaloid_template_mapper = {'鸣花': '鸣花姬·尊'}


def get_vocaloid_templates(vocaloids: List[str]) -> List[str]:
    result = []
    for v in vocaloids:
        name = vocaloid_names[v] if v in vocaloid_names else v
        if name in VOCALOID_TEMPLATES:
            result.append(name)
        for key, value in vocaloid_template_mapper.items():
            if key in name:
                result.append(value)
                break
    return result


def create_end(song: Song):
    vocaloid_templates = []
    if get_config().wikitext.producer_template_and_cat:
        list_templates, list_cats = asyncio.run(get_producer_info(song.creators.producers))
        vocaloid_templates = get_vocaloid_templates(song.creators.vocalists_str())
        list_templates.extend(vocaloid_templates)
        # FIXME: duplicates reported here
        producer_templates = join_string(list_templates, deliminator="",
                                         outer_wrapper=("{{", "}}\n"))
        producer_cats = join_string(list_cats, deliminator="",
                                    outer_wrapper=("[[Category:", "作品]]\n"))
    else:
        producer_templates, producer_cats = "", ""
    vocalist_cat = join_string([vocalist for vocalist in song.creators.vocalists_str()
                                if len(get_vocaloid_templates([vocalist])) == 0],
                               deliminator="", mapper=name_to_cat,
                               outer_wrapper=('[[分类:', '歌曲]]\n'))
    if len(vocaloid_templates) == 0:
        engine_cats = set()
        for vocalist in song.creators.vocalists:
            if vocalist.name in UTAU_CHARACTERS:
                engine_cats.add("UTAU")
            elif vocalist.name in CEVIO_CHARACTERS:
                engine_cats.add("CeVIO")
            else:
                engine_cats.add("VOCALOID")
        engine_cat = "".join(f"[[分类:使用{cat}的歌曲]]\n" for cat in engine_cats)
    else:
        engine_cat = ""
    return (producer_templates + """== 注释 ==
<references/>
[[分类:日本音乐作品]]
""" + engine_cat + vocalist_cat + producer_cats)


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
    response = prompt_choices(_("uploader_note"), choices=["Yes", "No"])
    if response == 2:
        return ""
    japanese = prompt_multiline(_("uploader_note_jap"),
                                terminator=is_empty)
    japanese = "<br/>".join(japanese)
    chinese = prompt_multiline(_("uploader_note_chs"),
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
    data.name_japanese = prompt_response(_("name_original"))
    name_chinese = prompt_response(_("name_trans"))
    if is_empty(name_chinese):
        name_chinese = data.name_japanese
    song = get_song_by_name(data.name_japanese, name_chinese)
    if not song:
        raise NotImplementedError(_("only_vocadb"))
    header = create_header(song)
    uploader_note = create_uploader_note(song)
    intro = create_intro(song)
    song_body = create_song(song)
    lyrics = create_lyrics(song.lyrics)
    end = create_end(song)
    wikitext_dir = get_output_path().joinpath(f"{song.name_chs}.wikitext")
    write_to_file("\n".join([header, uploader_note, intro, song_body, lyrics, end]),
                  wikitext_dir)
    if song.image.path and get_config().image.auto_upload:
        response = prompt_choices("Upload image to commons?", ["Yes", "No"])
        if response == 1:
            image = song.image
            upload_image(image.path, filename=image.file_name, song_name=name_chinese,
                         authors=image.creators, source_url=image.source_url)
    print(_("prog_end"))
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
        logging.error(_("err_unexpected"))
    input(_("enter_exit"))
