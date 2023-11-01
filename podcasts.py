import os
import re
from dataclasses import dataclass,field
import datetime

import requests
import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import pytz


dateformats = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S %Z",
]

@dataclass
class Episode:
    title:str
    date:str
    link:str
    channel:str
    description:str = ""
    author:str = ""

    def __post_init__(self):
        question_mark_idx = self.link.find("?")
        if question_mark_idx>-1:
            self.link=self.link[0:question_mark_idx]
        
        if self.date.find("PDT")>-1 or self.date.find("PST")>-1:
            self.date = self.date.replace("PDT","-0700")
            self.date = self.date.replace("PST","-0700")

        for f in dateformats:
            try:
                self.date = datetime.datetime.strptime(self.date,f)
                if not isinstance(self.date.tzinfo,datetime.timezone):
                    self.date = pytz.utc.localize(self.date)
                break
            except Exception as e:
                pass

    def __str__(self):
        return f"{datetime.datetime.strftime(self.date,'%d-%b-%Y %H:%M')}. {self.channel}: {self.title}"

@dataclass
class Podcast:
    title:str
    episodes:list
    description:str=""
    link:str=""

    def __str__(self):
        return f"{self.title}; {len(self.episodes)} episode(s)."

    def list_last(self, n=5):
        for i in range(n):
            print(f"{i} {self.episodes[i]}")


class PodcastReader:
    def __init__(self, feedsfile:str, max_age=30):
        self.max_age = max_age
        with open(feedsfile) as f:
            lines = filter(lambda x: not x.startswith("#"), f.readlines())
            rssdata =  [line.split(";")[1].strip() for line in lines]
            self.parse_rssdata(rssdata)
        

    def parse_rssdata(self,rssdata):
        results = []
        for url in rssdata:
            try:
                xml_data = self.download_xml(url)
                podcast = self.read_xml_data(xml_data)
                results.append(podcast)
            except Exception as e:
                clean_feed = re.sub(r"[\/\\:\-\.=?]","",url)
                print(f"Error obtaining podcast: '{url}'. Dumping contents to './dump/{clean_feed}'.")
                os.makedirs("./dump",exist_ok=True)
                with open(f"./dump/{clean_feed}.txt","w",encoding="utf16") as f:
                    f.write(f"{e}\n")
                    f.write(xml_data)
        self.podcasts = results
        
    def read_xml_data(self,xmldata)->Podcast:
        data = ET.fromstring(xmldata)
        channel = data.find("channel")
        channel_title  = channel.find("title").text
        channel_description = channel.find("description").text
        channel_url = channel.find("link").text

        episodes = self.read_episodes(channel.findall("item"),channel_title)
        return Podcast(channel_title,episodes,channel_description,channel_url)
    
    def download_xml(self,url)->str|None:
        r =  requests.get(url)
        if(r.status_code == 200):
            return r.content.decode()
        return None

    def get_field(self, item,fieldname,default=""):
        field = item.find(fieldname)
        return field.text if field else default

    def read_episodes(self, items, channel):
        episodes = []
        cutoff = datetime.datetime.now(pytz.timezone('Europe/Amsterdam'))-datetime.timedelta(days=self.max_age)

        for item in items:
            title = item.find("title").text
            date = item.find("pubDate").text
            url = item.find("enclosure").attrib["url"]
            description = self.get_field(item,"description")
            author = self.get_field(item,"author")
            episode = Episode(title,date,url,channel,description,author)
            if episode.date < cutoff: break
            episodes.append(episode)
        return episodes

