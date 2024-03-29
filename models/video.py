import json
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Union, List

import requests
from bs4 import BeautifulSoup

from i18n.i18n import _
from utils.helpers import prompt_response, prompt_choices, http_get
from utils.string import split_number


class VideoSite(Enum):
    NICO_NICO = "niconico"
    BILIBILI = "bilibili"
    YOUTUBE = "YouTube"


class Video:
    def __init__(self, site: VideoSite, identifier: str, url: str, views: int, uploaded: datetime,
                 thumb_url: str = None, canonical: bool = True):
        self.site: VideoSite = site
        self.identifier: str = identifier
        self.url = url
        self.views: int = views
        self.uploaded: datetime = uploaded
        self.thumb_url: str = thumb_url
        self.canonical = canonical

    def __str__(self) -> str:
        return f"VideoSite: {self.site}\n" \
               f"Id: {self.identifier}\n" \
               f"Views: {self.views}\n" \
               f"Uploaded: {self.uploaded}\n" \
               f"Thumb: {self.thumb_url}\n\n"


table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
tr = {}
for index in range(58):
    tr[table[index]] = index
s = [11, 10, 3, 8, 4, 6]
xor = 177451812
add = 8728348608


def av_to_bv(av: str) -> str:
    x = int(av[2:])
    x = (x ^ xor) + add
    r = list('BV1  4 1 7  ')
    for i in range(6):
        r[s[i]] = table[x // 58 ** i % 58]
    return ''.join(r)


def parse_nc_url(vid: str) -> str:
    if vid.find("nicovideo") != -1:
        vid = vid[vid.rfind("/") + 1:]
    return vid


def get_nc_info(vid: str) -> Video:
    vid = parse_nc_url(vid)
    url = f"https://www.nicovideo.jp/watch/{vid}"
    result = http_get(url, use_proxy=True).text
    soup = BeautifulSoup(result, "html.parser")
    date = datetime.fromtimestamp(0)
    views = 0
    for script in soup.find_all('script'):
        t: str = script.get_text()
        index_start = t.find("uploadDate")
        if index_start != -1:
            index_start += len("uploadDate") + 3
            date = t[index_start:index_start + 10]
            date = str_to_date(date)
        index_start = t.find("userInteractionCount")
        if index_start != -1:
            index_start += len("userInteractionCount") + 2
            index_end = t.find("}", index_start)
            views = int(t[index_start:index_end])
    thumb = soup.find("meta", {"name": "thumbnail"})['content']
    return Video(VideoSite.NICO_NICO, vid, url, views, date, thumb)


def get_bv(vid: str) -> str:
    search_bv = re.search("BV[0-9a-zA-Z]+", vid, re.IGNORECASE)
    if search_bv is not None:
        return search_bv.group(0)
    search_av = re.search("av[0-9]+", vid, re.IGNORECASE)
    if search_av is not None:
        return av_to_bv(search_av.group(0))
    return vid


def get_bb_info(vid: str) -> Video:
    vid = get_bv(vid)
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={vid}"
    response = json.loads(http_get(url, use_proxy=False).text)
    epoch_time = int(response['data']['pubdate'])
    date = datetime.fromtimestamp(epoch_time)
    # remove extra information to be in sync with YT and Nico
    date = datetime(year=date.year, month=date.month, day=date.day)
    pic = response['data']['pic']
    views = response['data']['stat']['view']
    return Video(VideoSite.BILIBILI, vid, url, views, date, pic)


def parse_yt_url(vid: str) -> str:
    if vid.find("youtube.") != -1:
        return vid[vid.find("=") + 1:]
    elif vid.find("youtu.be") != -1:
        return vid[vid.rfind("/") + 1:]


def get_yt_info(vid: str) -> Union[Video, None]:
    vid = parse_yt_url(vid)
    url = 'https://www.youtube.com/watch?v=' + vid
    text = http_get(url, use_proxy=True).text
    soup = BeautifulSoup(text, "html.parser")
    interaction = soup.select_one('meta[itemprop="interactionCount"][content]')
    views = int(interaction['content'])
    date = str_to_date(soup.select_one('meta[itemprop="datePublished"][content]')['content'])
    return Video(VideoSite.YOUTUBE, vid, url, views, date,
                 thumb_url="https://img.youtube.com/vi/{}/maxresdefault.jpg".format(vid))


info_func = {
    VideoSite.NICO_NICO: get_nc_info,
    VideoSite.BILIBILI: get_bb_info,
    VideoSite.YOUTUBE: get_yt_info
}


def view_count_from_site(video: Video) -> str:
    # requires Python 3.10; too many compatibility issues
    # match video.site:
    #     case VideoSite.NICO_NICO:
    #         return f"{{{{NiconicoCount|id={video.identifier}}}}}"
    #     case VideoSite.YOUTUBE:
    #         return f"{{{{YoutubeCount|id={video.identifier}|fallback={video.views}+}}}}"
    #     case VideoSite.BILIBILI:
    #         return f"{{{{BilibiliCount|id={video.identifier}}}}}"
    #     case _:
    #         return "ERROR"
    if video.site == VideoSite.NICO_NICO:
        return f"{{{{NiconicoCount|id={video.identifier}}}}}"
    if video.site == VideoSite.YOUTUBE:
        return f"{{{{YoutubeCount|id={video.identifier}}}}}"
    if video.site == VideoSite.BILIBILI:
        return f"{{{{BilibiliCount|id={video.identifier}}}}}"
    return "ERROR"


def video_from_site(site: VideoSite, identifier: str, canonical: bool = True) -> Union[Video, None]:
    logging.info('Fetching video from ' + site.value)
    logging.debug(f"Video identifier: {identifier}")
    try:
        v = info_func[site](identifier)
    except Exception as e:
        logging.warning(_("fail_fetch") + site.value)
        logging.debug("Detailed exception info: ", exc_info=e)
        v = None
    if not v:
        identifier = parse_yt_url(identifier) if site == VideoSite.YOUTUBE else parse_nc_url(identifier)
        return Video(site, identifier, "", 0, datetime.fromtimestamp(0))
    v.canonical = canonical
    return v


def str_to_date(date: str) -> datetime:
    if 'T' in date:
        date = date[:date.find('T')]
    date = date.split("-")
    if len(date) != 3:
        logging.warning(_("invalid_date"))
        return datetime.fromtimestamp(0)
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    return datetime(year=year, month=month, day=day)


def get_video_bilibili() -> Union[Video, None]:
    bv = prompt_response(_("bilibili_link"))
    if bv.isspace() or len(bv) == 0:
        return None
    if bv:
        bv_canonical = prompt_choices(_("bv_canonical"), ["Yes", "No"])
        bv_canonical = bv_canonical == 1
        return video_from_site(VideoSite.BILIBILI, bv, bv_canonical)


def get_video(videos: List[Video], site: VideoSite):
    for v in videos:
        if v.site == site:
            return v
    return None


def only_canonical_videos(videos: List[Video]) -> List[Video]:
    return [v for v in videos if v.canonical]
