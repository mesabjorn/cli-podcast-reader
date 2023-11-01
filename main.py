import os
from dataclasses import dataclass,field
import re
import webbrowser
import datetime

import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import pytz

MAX_AGE = 30 # episodes older than MAX_AGE days, are hidden

dateformats = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S %Z",
]

@dataclass
class Episode:
    title:str = "" 
    date:str = ""
    description:str = ""
    link:str = ""
    channel:str=""

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

    def __str__(self):
        return f"{self.title}; {len(self.episodes)} episode(s)."
    

    def list_last(self, n=5):
        for i in range(n):
            print(f"{i} {self.episodes[i]}")

def download_xml(url)->str|None:
    r =  requests.get(url)
    if(r.status_code == 200):
        return r.content.decode()
    return None

def read_feeds_file(feeds_file="feeds.txt")->list[str]:
    with open(feeds_file) as f:
        lines = filter(lambda x: not x.startswith("#"), f.readlines())
        return [line.split(";")[1].strip() for line in lines]

def get_podcasts(rssdata)->list[Podcast]:
    result = []
    for url in rssdata:
        try:
            xml_data = download_xml(url)
            podcast = read_xml_data(xml_data)
            result.append(podcast)
        except Exception as e:
            clean_feed = re.sub(r"[\/\\:\-\.=?]","",url)
            print(f"Error obtaining podcast: '{url}'. Dumping contents to './dump/{clean_feed}'.")
            os.makedirs("./dump",exist_ok=True)
            with open(f"./dump/{clean_feed}.txt","w",encoding="utf16") as f:
                f.write(f"{e}\n")
                f.write(xml_data)
    return result


def read_xml_data(xmldata)->Podcast:
    data = ET.fromstring(xmldata)
    channel = data.find("channel")
    channel_title  = channel.find("title").text
    items = channel.findall("item")

    episodes = []
    cutoff = datetime.datetime.now(pytz.timezone('Europe/Amsterdam'))-datetime.timedelta(days=MAX_AGE)
    for item in items:        
        title = item.find("title").text
        description = item.find("description").text
        date = item.find("pubDate").text
        url = item.find("enclosure").attrib["url"]
        
        episode = Episode(title,date,description,url,channel=channel_title)
        if episode.date < cutoff:
            break
        episodes.append(episode)
    return Podcast(channel_title,episodes)

def select_cast(podcasts):
    command = None
    
    while command != "q":
        print("Select cast: (q to quit)")
        for i,p in enumerate(podcasts):
            print(f"{i}. {p}")
        selected_cast = input("")
        try:
            if selected_cast == "q": break
            print("Select episode: (b to go back)")
            podcasts[int(selected_cast)].list_last()
            selected_ep = input("")
            if selected_ep == "b":
                pass
            else:
                toplay = podcasts[int(selected_cast)].episodes[int(selected_ep)]
                print(f"Opening {toplay.link}")
                webbrowser.open(toplay.link)                
        except:
            print("Invalid command")


def select_eps(podcasts):
    all_eps = []
    for p in podcasts:
        all_eps.extend(p.episodes)
    command = None
    all_eps.sort(key=lambda x:x.date,reverse=True)
    
    while command != "q":
        print(f"Hiding {len(all_eps) - len(all_eps)} episode(s) aired over {MAX_AGE} days ago.")
        for i, ep in enumerate(all_eps):
            print(f"{i+1}. {ep}")
        selected_ep = input("Episode nr to open (q to quit): ")
        
        if(selected_ep == "q"):
            break
        toplay = all_eps[int(selected_ep)-1]
        print(f"Opening {toplay.link}")
        webbrowser.open(toplay.link)

if __name__ == "__main__":
    urls = read_feeds_file("feeds - Copy.txt")
    podcasts = get_podcasts(urls)
    # [print(p) for p in podcasts]
    # select_cast(podcasts)
    select_eps(podcasts)
