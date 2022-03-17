import json
import logging
from datetime import datetime
from enum import Enum
from typing import Union

import requests
from bs4 import BeautifulSoup

from utils.string import split_number


class Site(Enum):
    NICO_NICO = "niconico"
    BILIBILI = "bilibili"
    YOUTUBE = "YouTube"


class Video:
    def __init__(self, site: Site, identifier: str, url: str, views: int, uploaded: datetime,
                 thumb_url: str = None, canonical: bool = True):
        self.site: Site = site
        self.identifier: str = identifier
        self.url = url
        self.views: int = views
        self.uploaded: datetime = uploaded
        self.thumb_url: str = thumb_url
        self.canonical = canonical

    def __str__(self) -> str:
        return f"Site: {self.site}\n" \
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


def get_nc_info(vid: str) -> Video:
    if vid.find("nicovideo") != -1:
        vid = vid[vid.rfind("/") + 1:]
    url = f"https://www.nicovideo.jp/watch/{vid}"
    result = requests.get(url).text
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
    thumb = soup.find("meta", {"name": "twitter:image"})['content']
    return Video(Site.NICO_NICO, vid, url, views, date, thumb)


def get_bb_info(vid: str) -> Video:
    if vid.find("bilibili") != -1:
        vid = vid[vid.rfind("/") + 1:]
        if vid.find("?") != -1:
            vid = vid[:vid.find("?")]
    if "av" in vid:
        vid = av_to_bv(vid)
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={vid}"
    response = json.loads(requests.get(url).text)
    epoch_time = int(response['data']['pubdate'])
    date = datetime.fromtimestamp(epoch_time)
    # remove extra information to be in sync with YT and Nico
    date = datetime(year=date.year, month=date.month, day=date.day)
    pic = response['data']['pic']
    views = response['data']['stat']['view']
    return Video(Site.BILIBILI, vid, url, views, date, pic)


def get_yt_info(vid: str) -> Union[Video, None]:
    if vid.find("youtube.") != -1:
        vid = vid[vid.find("=") + 1:]
    elif vid.find("youtu.be") != -1:
        vid = vid[vid.rfind("/") + 1:]
    url = 'https://www.youtube.com/watch?v=' + vid
    text = requests.get(url).text
    logging.debug(text)
    soup = BeautifulSoup(text, "html.parser")
    interaction = soup.select_one('meta[itemprop="interactionCount"][content]')
    views = int(interaction['content'])
    date = str_to_date(soup.select_one('meta[itemprop="datePublished"][content]')['content'])
    return Video(Site.YOUTUBE, vid, url, views, date,
                 thumb_url="https://img.youtube.com/vi/{}/0.jpg".format(vid))


info_func = {
    Site.NICO_NICO: get_nc_info,
    Site.BILIBILI: get_bb_info,
    Site.YOUTUBE: get_yt_info
}


def view_count_from_site(video: Video) -> str:
    # requires Python 3.10; too many compatibility issues
    # match video.site:
    #     case Site.NICO_NICO:
    #         return f"{{{{NiconicoCount|id={video.identifier}}}}}"
    #     case Site.YOUTUBE:
    #         return f"{{{{YoutubeCount|id={video.identifier}|fallback={video.views}+}}}}"
    #     case Site.BILIBILI:
    #         return f"{{{{BilibiliCount|id={video.identifier}}}}}"
    #     case _:
    #         return "ERROR"
    if video.site == Site.NICO_NICO:
        return f"{{{{NiconicoCount|id={video.identifier}}}}}"
    if video.site == Site.YOUTUBE:
        return f"{{{{YoutubeCount|id={video.identifier}|fallback={split_number(video.views)}}}}}"
    if video.site == Site.BILIBILI:
        return f"{{{{BilibiliCount|id={video.identifier}}}}}"
    return "ERROR"


def video_from_site(site: Site, identifier: str, canonical: bool = True) -> Union[Video, None]:
    logging.info(f"Fetching video from {site.value}")
    logging.debug(f"Video identifier: {identifier}")
    try:
        v = info_func[site](identifier)
    except Exception as e:
        logging.warning("Failed to fetch info from " + site.value)
        logging.debug("Detailed exception info: ", exc_info=e)
        return None
    if not v:
        return None
    v.canonical = canonical
    return v


def str_to_date(date: str) -> datetime:
    date = date.split("-")
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    return datetime(year=year, month=month, day=day)
