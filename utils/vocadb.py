import json
import logging
import urllib
from datetime import datetime
from pathlib import Path
from typing import Union, List, Dict, Optional

import requests

import utils.string
from config.config import get_config, get_output_path
from i18n.i18n import _
from models.color import ColorScheme
from models.creators import Person, Creators, role_transform
from models.song import Song, Image, get_manual_lyrics, Lyrics
from models.video import Video, VideoSite, video_from_site, get_video_bilibili, str_to_date
from utils import string, japanese
from utils.at_wiki import get_chinese_lyrics, get_japanese_lyrics
from utils.helpers import prompt_choices, http_get
from utils.image import download_thumbnail, pick_color
from utils.name_converter import name_shorten
from utils.string import split, is_empty

VOCADB_SONG_QUERY_URL = "https://vocadb.net/api/songs"

PARAMS_BROAD = {
    'start': 0,
    'maxResults': 50,
    'fields': 'None',
    'lang': 'Default',
    'nameMatchMode': 'Exact',
    'sort': 'PublishDate',
    'childTags': 'false',
    'artistParticipationStatus': 'Everything',
    'onlyWithPvs': 'false',
    'getTotalCount': 'true'
}

PARAMS_NARROW = {**PARAMS_BROAD,
                 'songTypes': 'Original'}


def parse_creators(artists: list, artist_string: str) -> Creators:
    mapping: Dict[str, List[Person]] = dict()
    for artist in artists:
        if 'artist' in artist:
            name = artist['artist']['name']
            if artist['artist']['artistType'] == 'Vocaloid':
                # shorten names like 初音ミク V4X
                name = name_shorten(name)
            names_other = split(artist['artist']['additionalNames'])
        else:
            name = artist['name']
            names_other = []
        roles = artist['roles']
        if roles == 'Default':
            roles = artist['categories']
        if roles == 'Other':
            continue
        roles = split(roles)
        person = Person(name.strip(), names_other)
        for role in roles:
            role = role.strip()
            if role in mapping:
                mapping[role].append(person)
            else:
                mapping[role] = [person]
    if "Vocalist" in mapping:
        vocalists: List[Person] = mapping.get("Vocalist")
    else:
        names = split(artist_string.split("feat.")[1])
        vocalists: List[Person] = [Person(name_shorten(n)) for n in names]
    if "Producer" in mapping:
        producers = mapping.pop("Producer")
    else:
        names = split(artist_string.split("feat.")[0])
        producers = [Person(n) for n in names if not is_empty(n)]
    staffs: dict = dict()
    for role in mapping:
        staffs[role_transform(role)] = mapping[role]
    if "作词" not in staffs and "作曲" not in staffs:
        staffs['词曲'] = producers
    elif "作词" not in staffs:
        staffs['作词'] = producers
    elif "作曲" not in staffs:
        staffs['作曲'] = producers
    if "曲绘" not in staffs and "PV制作" in staffs:
        staffs["曲绘"] = staffs["PV制作"]
    return Creators(producers, vocalists, staffs)


def parse_videos(videos: list, date_fallback: datetime = datetime.fromtimestamp(0)) -> List[Video]:
    service_to_site: dict = {
        'NicoNicoDouga': VideoSite.NICO_NICO,
        'Youtube': VideoSite.YOUTUBE
    }
    result = []
    for v in videos:
        service = v['service']
        if v['pvType'] == 'Original' and service in service_to_site.keys():
            url = v['url']
            # FIXME: only one video per site allowed for now
            video = video_from_site(service_to_site.pop(service), url)
            if video:
                if video.uploaded and video.uploaded.year < 2000:
                    video.uploaded = date_fallback
                result.append(video)
    return result


def parse_albums(albums: list) -> List[str]:
    return [a['defaultName'] for a in albums]


def process_image(image_in: Path, image_out: Path) -> Optional[ColorScheme]:
    try:
        if image_in is not None and image_in.exists():
            if get_config().color.color_from_image or get_config().image.crop:
                return pick_color(image_in, image_out)
            image_out.unlink(missing_ok=True)
            image_in.rename(image_out)
    except Exception as e:
        logging.error("Can't get color from image", exc_info=e)
    return None


def get_song_by_name(song_name: str, name_chs: str) -> Union[Song, None]:
    song_id = search_song_id(song_name)
    if not song_id:
        return None
    logging.info(f"Fetching song details with id {song_id} from vocadb.")
    url = f"https://vocadb.net/api/songs/{song_id}/details"
    response = json.loads(http_get(url, use_proxy=True).text)
    name_ja = song_name
    name_other = [n.strip() for n in utils.string.split(",")]
    creators: Creators = parse_creators(response['artists'], response['artistString'])
    lyricsList = response['lyricsFromParents']
    producer_temp = creators.producers[0].name if len(creators.producers) > 0 else ""
    if get_config().wikitext.no_lyrics:
        lyrics = Lyrics(translator="", source_name="VOCALOID中文歌词wiki", source_url="",
                        lyrics_jap="", lyrics_chs="")
    else:
        if len(lyricsList) > 0:
            lyrics_ja = get_lyrics(response['lyricsFromParents'][0]['id'])
        else:
            logging.warning("Lyrics not found on vocadb.")
            lyrics_ja = get_japanese_lyrics(name_ja, producer_temp)
        lyrics = get_chinese_lyrics(song_name, producer_temp)
        if lyrics is None:
            lyrics = Lyrics()
            if not get_config().wikitext.lyrics_chs_fail_fast:
                choice = prompt_choices(_("manual_trans"),
                                        ["Sure.", "No."])
                if choice == 1:
                    lyrics = get_manual_lyrics()
        if not is_empty(lyrics.lyrics_jap):
            lyrics_ja = lyrics.lyrics_jap
        if get_config().wikitext.process_lyrics_jap:
            lyrics_ja = string.process_lyrics_jap(lyrics_ja)
        if get_config().wikitext.furigana_local:
            lyrics_ja = japanese.furigana_local(lyrics_ja)
        lyrics.lyrics_jap = lyrics_ja
    date_fallback = datetime.fromtimestamp(0)
    if 'song' in response:
        date_fallback = str_to_date(response['song']['publishDate'])
    videos = parse_videos(response['pvs'], date_fallback)
    video_bilibili = get_video_bilibili()
    if video_bilibili:
        videos.append(video_bilibili)
    albums = parse_albums(response['albums'])
    if get_config().image.download_cover:
        res = download_thumbnail(videos, "cover.jpg")
        if res is None:
            # FIXME: what if no video?
            image_path, video = None, videos[0]
        else:
            image_path, video = res
    else:
        image_path, video = None, videos[0]
    cover_name = f"{name_chs}封面.jpg"
    cover_path = get_output_path().joinpath(cover_name)
    colors = process_image(image_path, cover_path)
    illustrators = creators.staffs.get("曲绘", None)
    image: Image = Image(image_path, cover_name, video.url, illustrators)
    return Song(name_ja, name_chs, name_other, creators, lyrics, image, videos, albums, colors)


def get_lyrics(lyrics_id: str) -> str:
    logging.info("Getting Japanese lyrics from vocadb.")
    url = f"https://vocadb.net/api/songs/lyrics/{lyrics_id}?v=25"
    response = json.loads(http_get(url, use_proxy=True).text)
    return response['value']


def search_vocadb(name: str, params: dict) -> list:
    params = {**params,
              'query': name}
    try:
        response = json.loads(http_get(VOCADB_SONG_QUERY_URL, use_proxy=True, params=params).text)
        response = response['items']
    except Exception as e:
        logging.error("An error occurred while searching on Vocadb")
        logging.debug("Detailed error: ", exc_info=e)
        return []
    response = [song for song in response if song['defaultName'] == name]
    return response


def search_narrow(name: str) -> list:
    return search_vocadb(name, PARAMS_NARROW)


def search_broad(name: str) -> list:
    return search_vocadb(name, PARAMS_BROAD)


def search_song_id(name: str) -> Union[str, None]:
    logging.info(f"Searching for song named {name} on Vocadb")
    response = search_narrow(name)
    narrow: bool = True
    if len(response) == 0:
        narrow = False
        logging.info(_("narrow_to_broad"))
        response = search_broad(name)
    if len(response) == 0:
        logging.error(_("no_vocadb"))
        return None
    while len(response) > 1 or (len(response) == 1 and get_config().vocadb_manual):
        options = [f"{song['defaultName']} by {song['artistString']}"
                   for song in response]
        options.append("None of the above.")
        result = prompt_choices(_("multiple_vocadb_results"), options)
        if result == len(options):
            if narrow:
                narrow = False
                logging.info(_("broader_search"))
                response = search_broad(name)
                continue
            else:
                logging.error(_("no_vocadb"))
                return None
        return response[result - 1]['id']
    r = response[0]['id']
    logging.info(f"Using {response[0]['defaultName']} 'by' {response[0]['artistString']}")
    return r
