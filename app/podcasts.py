import os
import re
from dataclasses import dataclass
import datetime
from dateutil import parser

import requests
import xml.etree.ElementTree as ET
import pytz

from app import LOGGER

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


@dataclass
class Podcast:
    title: str
    episodes: list
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
    def __init__(self, feedsfile: str, max_age=30):
        self.max_age = max_age
        self.feedsfile = feedsfile
        self.podcasts = []
        self.read_feeds()

    def read_feeds(self):
        with open(self.feedsfile) as f:
            lines = filter(
                lambda x: not x.startswith("#") and len(x) > 1, f.readlines()
            )
            linedata = []
            for line in lines:
                data = [x.strip() for x in line.split(";")]
                linedata.append(Line(name=data[0], url=data[1]))

            self.parse_rssdata(linedata)

    def parse_rssdata(self, entries: list[Line]):
        results = []
        for entry in entries:
            try:
                LOGGER.info(f"Getting eps for '{entry.name}' ({entry.url}).")
                xml_data = self.download_xml(entry.url)
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

    def download_xml(self, url) -> str | None:
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"
            },
        )
        if r.status_code == 200:
            return r.content.decode()
        if len(r.content) > 0:
            return r.content.decode()
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
