from dataclasses import dataclass
import json


@dataclass
class Feed:
    id: int
    originalUrl: str
    title: str


@dataclass
class SearchResult:
    feeds: list[Feed]
    count: int
    description: str

    def list_feeds(self):
        i = 1
        for f in self.feeds:
            print(f"{i}: '{f.title}' - ({f.originalUrl})")
            i += 1


def parse_rss_search(content: bytes) -> SearchResult:
    data = json.loads(content)
    feeds = [
        Feed(id=f["id"], originalUrl=f["originalUrl"], title=f["title"])
        for f in data["feeds"]
    ]
    count = data["count"]
    description = data["description"]
    return SearchResult(feeds, count=count, description=description)
