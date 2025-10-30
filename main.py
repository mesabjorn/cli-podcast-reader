import argparse

from enum import Enum
from pathlib import Path
import sys
import webbrowser

import urllib

from app.podcasts import Episode, Podcast, PodcastReader

from app import LOGGER


def select_cast(podcasts):
    command = None
    while command not in ["q", "quit", "exit"]:
        print("Select cast: (q to quit)")
        for i, p in enumerate(podcasts):
            print(f"{i + 1}. {p}")
        selected_cast = input("")
        try:
            if selected_cast == "q":
                break
            select_eps([podcasts[int(selected_cast) - 1]])
        except Exception as e:
            LOGGER.error(f"Invalid command: {e}.")


from enum import Enum


class EPISODE_ACTION(Enum):
    PLAY = 1
    DOWNLOAD = 2


def episode_action() -> EPISODE_ACTION | None:
    while True:
        act = (
            input(
                "What do you want to do?\n"
                "1. Play episode\n"
                "2. Download episode\n"
                "(q to quit): "
            )
            .strip()
            .lower()
        )

        if act in ["q", "quit", "exit"]:
            break

        if act == "1":
            return EPISODE_ACTION.PLAY
        elif act == "2":
            return EPISODE_ACTION.DOWNLOAD
        else:
            print("Invalid option. Please enter 1, 2, or q.")


def select_eps(podcasts: list[Podcast]):
    all_eps = []
    for p in podcasts:
        all_eps.extend(p.episodes)
    command = None
    all_eps.sort(key=lambda x: x.date, reverse=True)

    while command not in ["q", "quit", "exit"]:
        for i, ep in enumerate(all_eps):
            print(f"{i + 1}. {ep}")
        selected_ep = input("Episode nr to open (q to quit): ")

        if selected_ep == "q":
            break

        toplay: Episode = all_eps[int(selected_ep) - 1]
        a = episode_action()
        if a == EPISODE_ACTION.PLAY:
            webbrowser.open(toplay.link)
            LOGGER.info(f"Opening {toplay.link}")
        elif a == EPISODE_ACTION.DOWNLOAD:
            LOGGER.info(f"Downloading {toplay.link}")
            downloaded_file = toplay.download(to=Path("./download/"))
            LOGGER.info(f"downloaded episode to '{downloaded_file}'")


def parse_args():
    argparser = argparse.ArgumentParser("CLI-Podcast browser")
    argparser.add_argument(
        "feeds",
        type=Path,
        default=Path("./feeds.txt"),
        nargs="?",
        help="Path to the feeds file (default: ./feeds.txt)",
    )
    argparser.add_argument(
        "--max-age",
        metavar="m",
        dest="max_age",
        type=int,
        default=30,
        help="Maximum age in days (default: 30)",
    )

    return argparser.parse_args()


def init_feeds(p: Path):
    with p.open("wt") as f:
        f.write("# Enter your podcasts here in name, url format\n")


def main():
    args = parse_args()

    if not args.feeds.exists():
        init_feeds(args.feeds)

    max_age = args.max_age
    pr = PodcastReader(args.feeds, max_age=max_age)
    while True:
        choice = input(
            ">1. List episodes, \n>2. browse podcast \n>3. Add new podcast. \n>4. Find new cast on podbean.\nEnter q/quit/exit to stop\n"
        )
        try:
            if choice in ["q", "quit", "exit"]:
                sys.exit()
            choice = int(choice)
        except ValueError:
            LOGGER.error("Invalid command.")
        if choice == 1:
            select_eps(pr.podcasts)
        elif choice == 2:
            select_cast(pr.podcasts)
        elif choice == 3:
            name = input("Name: ")
            url = input("Url: ")
            pr.add_feed(name, url)
        elif choice == 4:
            name = input("Name: ")
            query = urllib.parse.quote(name)
            url = f"https://www.podbean.com/site/search/index?v={query}"
            webbrowser.open(url)


if __name__ == "__main__":
    main()
