from dataclasses import dataclass,field
import datetime
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