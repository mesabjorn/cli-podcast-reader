import hashlib
import os
from pathlib import Path
import re
from dataclasses import dataclass
import datetime
from dateutil import parser

import requests
import xml.etree.ElementTree as ET
import pytz

from app import LOGGER, CacheManager

dateformats = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S %Z",
]


@dataclass
class Episode:
    title: str
    date: str
    link: str
    channel: str
    description: str = ""
    author: str = ""

    def __post_init__(self):
        question_mark_idx = self.link.find("?")
        if question_mark_idx > -1:
            self.link = self.link[0:question_mark_idx]

        try:
            self.date = parser.parse(self.date)
        except ValueError:
            LOGGER.error(f"Cannot parse: {self.date}.")
        except Exception as e:
            print(e)

    def __str__(self):
        return f"{datetime.datetime.strftime(self.date, '%d-%b-%Y %H:%M')}. {self.channel}: {self.title}"

    @property
    def safe_file_out_name(self):
        name = f"{datetime.datetime.strftime(self.date, '%Y-%m-%d')}-{self.channel}-{self.title}"
        return re.sub(r"[!@#$%^&*?|:\\/]", "", name)

    def download(self, to: Path) -> Path:
        to.mkdir(exist_ok=True, parents=True)
        safe_title = self.safe_file_out_name
        file_out = (to / safe_title).with_suffix(".mp3")
        if file_out.exists():
            return file_out

        r = requests.get(
            self.link,
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"
            },
        )
        if r.status_code == 200:
            with file_out.open("wb") as f:
                f.write(r.content)
            return file_out

        raise Exception(
            f"Error while dowloading {self.title}: ({self.link}). Error: '{r.status_code}':{r.content}"
        )


@dataclass
class Podcast:
    title: str
    episodes: list[Episode]
    description: str = ""
    link: str = ""

    def __str__(self):
        return f"{self.title}; {len(self.episodes)} episode(s)."

    def list_last(self, n=5):
        for i in range(n):
            print(f"{i} {self.episodes[i]}")


@dataclass
class Line:
    # Line from feeds file
    name: str
    url: str


class PodcastReader:
    cache: CacheManager

    def __init__(self, feedsfile: str, max_age=30, cache_path=Path(".cache")):
        self.max_age = max_age
        self.feedsfile = feedsfile
        self.podcasts = []
        self.cache = CacheManager.CacheManager(cache_path)
        self.read_feeds()

    def read_feeds(self):
        linedata = []
        with open(self.feedsfile) as f:
            lines = filter(
                lambda x: not x.startswith("#") and len(x) > 1, f.readlines()
            )
            for line in lines:
                data = [x.strip() for x in line.split(";")]
                linedata.append(Line(name=data[0], url=data[1]))
        if len(linedata) == 0:
            print("Warning: no podcasts in feeds file")
            return

        self.parse_rssdata(linedata)

    def parse_rssdata(self, entries: list[Line]):
        results = []
        for entry in entries:
            try:
                LOGGER.info(f"Getting eps for '{entry.name}' ({entry.url}).")

                xml_data = self.get_xml_data(entry.url)
                podcast = self.read_xml_data(xml_data)
                results.append(podcast)
            except Exception as e:
                clean_feed = re.sub(r"[\/\\:\-\.=?]", "", entry.name)
                LOGGER.error(
                    f"Error obtaining episodes for {entry.name}: '{entry.url}'. Dumping contents to './dump/{clean_feed}'."
                )
                os.makedirs("./dump", exist_ok=True)
                with open(f"./dump/{clean_feed}.txt", "w", encoding="utf16") as f:
                    f.write(f"---{e}---\nResponse:\n")
                    if xml_data:
                        f.write(xml_data)
                    else:
                        f.write("no data")
        self.podcasts = results

    def read_xml_data(self, xmldata) -> Podcast:
        data = ET.fromstring(xmldata)
        channel = data.find("channel")
        channel_title = channel.find("title").text
        channel_description = channel.find("description").text
        channel_url = channel.find("link").text

        episodes = self.read_episodes(channel.findall("item"), channel_title)
        return Podcast(channel_title, episodes, channel_description, channel_url)

    def get_xml_data(self, url: str) -> bytes:
        filename = hashlib.sha256(bytes(url, encoding="utf-8")).hexdigest()
        cached_data = self.cache.read(filename)
        if cached_data:
            LOGGER.info(f"Got episode data from cachefile '{filename}'.")
            return cached_data.data.decode()

        content = self.download_xml(url)
        if content:
            self.cache.write(filename, content)
            LOGGER.info(f"Cached episode data in '{filename}'.")
            return content.decode()
        LOGGER.warning(f"No data obtained for url '{url}'.")
        return bytes()

    def download_xml(self, url) -> bytes | None:
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"
            },
        )
        if r.status_code == 200:
            return r.content
        return None

    def get_field(self, item, fieldname, default=""):
        field = item.find(fieldname)
        return field.text if field else default

    def read_episodes(self, items, channel):
        episodes = []
        cutoff = datetime.datetime.now(
            pytz.timezone("Europe/Amsterdam")
        ) - datetime.timedelta(days=self.max_age)

        for item in items:
            title = item.find("title").text
            date = item.find("pubDate").text
            url = item.find("enclosure").attrib["url"]
            description = self.get_field(item, "description")
            author = self.get_field(item, "author")
            episode = Episode(title, date, url, channel, description, author)
            if episode.date < cutoff:
                break
            episodes.append(episode)
        return episodes

    def add_feed(self, name, url):
        with open(self.feedsfile, "a+") as f:
            f.write(f"{name};{url}\n")
        self.read_feeds()
