import json
from datetime import datetime
from enum import Enum

import requests
from bs4 import BeautifulSoup


class Site(Enum):
    NICO_NICO = "niconico"
    BILIBILI = "Bilibili"
    YOUTUBE = "YouTube"


class Video:
    def __init__(self, site: Site, identifier: str, views: int, uploaded: datetime, thumb_url: str = None, canonical: bool = True):
        self.site: Site = site
        self.identifier: str = identifier
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


def get_nc_info(vid: str) -> Video:
    if vid.find("nicovideo") != -1:
        vid = vid[vid.rfind("/") + 1:]
    url = f"https://www.nicovideo.jp/watch/{vid}"
    result = requests.get(url).text
    soup = BeautifulSoup(result, "html.parser")
    date = datetime.fromtimestamp(0)
    views = 0
    for s in soup.find_all('script'):
        t: str = s.get_text()
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
    return Video(Site.NICO_NICO, vid, views, date, thumb)


def get_bb_info(vid: str) -> Video:
    if vid.find("bilibili") != -1:
        vid = vid[vid.rfind("/") + 1:]
        if vid.find("?") != -1:
            vid = vid[:vid.find("?")]
    url = f"http://api.bilibili.com/x/web-interface/view?bvid={vid}"
    response = json.loads(requests.get(url).text)
    epoch_time = int(response['data']['pubdate'])
    pic = response['data']['pic']
    views = response['data']['stat']['view']
    return Video(Site.BILIBILI, vid, views, datetime.fromtimestamp(epoch_time), pic)


def get_yt_info(vid: str) -> Video:
    if vid.find("youtube.") != -1:
        vid = vid[vid.find("=") + 1:]
    url = 'https://www.youtube.com/watch?v=' + vid
    text = requests.get(url).text
    soup = BeautifulSoup(text, "html.parser")
    views = int(soup.select_one('meta[itemprop="interactionCount"][content]')['content'])
    date = str_to_date(soup.select_one('meta[itemprop="datePublished"][content]')['content'])
    return Video(Site.YOUTUBE, vid, views, date)


info_func = {
    Site.NICO_NICO: get_nc_info,
    Site.BILIBILI: get_bb_info,
    Site.YOUTUBE: get_yt_info
}


def view_count_from_site(video: Video) -> str:
    match video.site:
        case Site.NICO_NICO:
            return f"{{{{NiconicoCount|id={video.identifier}}}}}"
        case Site.YOUTUBE:
            return f"{{{{YoutubeCount|id={video.identifier}|fallback={video.views}+}}}}"
        case Site.BILIBILI:
            return f"{{{{BilibiliCount|id={video.identifier}}}}}"
        case _:
            return "ERROR"


def video_from_site(site: Site, identifier: str, canonical: bool = True) -> Video:
    v = info_func[site](identifier)
    v.canonical = canonical
    return v


def str_to_date(date: str) -> datetime:
    date = date.split("-")
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    return datetime(year=year, month=month, day=day)
