import json
import logging
import urllib
from pathlib import Path
from typing import Union, List, Dict, Optional

import requests

import utils.string
from config.config import get_config, get_output_path
from models.color import ColorScheme
from models.creators import Person, Creators, role_transform
from models.song import Song, Image, get_manual_lyrics, Lyrics
from models.video import Video, Site, video_from_site, get_video_bilibili
from utils import string, japanese
from utils.at_wiki import get_chinese_lyrics, get_japanese_lyrics
from utils.helpers import prompt_choices
from utils.image import download_thumbnail, pick_color
from utils.name_converter import name_shorten
from utils.string import split, is_empty

VOCADB_NARROW = "vocadb.net/api/songs?start=0&getTotalCount=true&maxResults=100" \
                "&query={}&fields=AdditionalNames%2CThumbUrl&lang=Default&nameMatchMode=Auto" \
                "&sort=PublishDate" \
                "&songTypes=Original&childTags=false&artistParticipationStatus=Everything&onlyWithPvs=false"

VOCADB_BROAD = "vocadb.net/api/songs?start=0&getTotalCount=true&maxResults=100" \
               "&query={}&fields=AdditionalNames%2CThumbUrl&lang=Default&nameMatchMode=Auto" \
               "&sort=PublishDate" \
               "&childTags=false&artistParticipationStatus=Everything&onlyWithPvs=false"


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


def parse_videos(videos: list) -> List[Video]:
    service_to_site: dict = {
        'NicoNicoDouga': Site.NICO_NICO,
        'Youtube': Site.YOUTUBE
    }
    result = []
    for v in videos:
        service = v['service']
        if v['pvType'] == 'Original' and service in service_to_site.keys():
            url = v['url']
            # FIXME: only one video per site allowed for now
            video = video_from_site(service_to_site.pop(service), url)
            if video:
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
    response = json.loads(requests.get(url).text)
    name_ja = song_name
    name_other = [n.strip() for n in utils.string.split(",")]
    creators: Creators = parse_creators(response['artists'], response['artistString'])
    lyricsList = response['lyricsFromParents']
    producer_temp = creators.producers[0].name if len(creators.producers) > 0 else ""
    if len(lyricsList) > 0:
        lyrics_ja = get_lyrics(response['lyricsFromParents'][0]['id'])
    else:
        logging.warning("Lyrics not found on vocadb.")
        lyrics_ja = get_japanese_lyrics(name_ja, producer_temp)
    lyrics = get_chinese_lyrics(song_name, producer_temp)
    if lyrics is None:
        lyrics = Lyrics()
        if not get_config().wikitext.lyrics_chs_fail_fast:
            choice = prompt_choices("Supply Chinese translation manually?",
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
    videos = parse_videos(response['pvs'])
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
    response = json.loads(requests.get(url).text)
    return response['value']


def search_with_url(url: str, name: str) -> list:
    logging.debug("Search url " + url)
    try:
        response = json.loads(requests.get(url).text)['items']
    except Exception as e:
        logging.error("An error occurred while searching on atwiki with url " + url)
        logging.debug("Detailed error: ", exc_info=e)
        return []
    response = [song for song in response if song['defaultName'] == name]
    return response


def search_narrow(name: str) -> list:
    url = VOCADB_NARROW.format(urllib.parse.quote(name))
    return search_with_url("https://" + url, name)


def search_broad(name: str) -> list:
    url = VOCADB_BROAD.format(urllib.parse.quote(name))
    return search_with_url("https://" + url, name)


def search_song_id(name: str) -> Union[str, None]:
    logging.info(f"Searching for song named {name} on Vocadb")
    response = search_narrow(name)
    narrow: bool = True
    if len(response) == 0:
        narrow = False
        logging.info("No result for narrow searching. Now trying broad search.")
        response = search_broad(name)
    if len(response) == 0:
        logging.error("No entry found in VOCADB.")
        return None
    while len(response) > 1 or (len(response) == 1 and get_config().vocadb_manual):
        options = [f"{song['defaultName']} by {song['artistString']}"
                   for song in response]
        options.append("None of the above.")
        result = prompt_choices("Multiple results found. Choose the correct one.", options)
        if result == len(options):
            if narrow:
                narrow = False
                logging.info("Performing a broader search...")
                response = search_broad(name)
                continue
            else:
                logging.error("No entry found in VOCADB.")
                return None
        return response[result - 1]['id']
    r = response[0]['id']
    logging.info(f"Using {response[0]['defaultName']} by {response[0]['artistString']}")
    return r
