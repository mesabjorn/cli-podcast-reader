import os
import re
import webbrowser
import datetime

import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import pytz

from podcasts import Podcast,Episode

MAX_AGE = 14 # episodes older than MAX_AGE days, are hidden

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


def get_field(item,fieldname,default=""):
    field = item.find(fieldname)
    return field.text if field else default

def read_episodes(items, channel):
    episodes = []
    cutoff = datetime.datetime.now(pytz.timezone('Europe/Amsterdam'))-datetime.timedelta(days=MAX_AGE)

    for item in items:
        title = item.find("title").text
        date = item.find("pubDate").text
        url = item.find("enclosure").attrib["url"]
        description = get_field(item,"description")
        author = get_field(item,"author")
        episode = Episode(title,date,url,channel,description,author)
        if episode.date < cutoff: break
        episodes.append(episode)
    return episodes

def read_xml_data(xmldata)->Podcast:
    data = ET.fromstring(xmldata)
    channel = data.find("channel")
    channel_title  = channel.find("title").text
    channel_description = channel.find("description").text
    channel_url = channel.find("link").text

    episodes = read_episodes(channel.findall("item"),channel_title)
    return Podcast(channel_title,episodes,channel_description,channel_url)

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
    urls = read_feeds_file("feeds.txt")
    podcasts = get_podcasts(urls)
    # [print(p) for p in podcasts]
    # select_cast(podcasts)
    select_eps(podcasts)
