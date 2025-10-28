import argparse

import sys
import webbrowser

import urllib

from app.podcasts import Podcast, PodcastReader

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
        toplay = all_eps[int(selected_ep) - 1]
        LOGGER.info(f"Opening {toplay.link}")
        webbrowser.open(toplay.link)


def parse_args():
    argparser = argparse.ArgumentParser("CLI-Podcast browser")
    argparser.add_argument("feeds", type=str, default="feeds.txt")
    argparser.add_argument(
        "--maxage", metavar="m", dest="max_age", type=int, default=30
    )

    return argparser.parse_args()


def main():
    args = parse_args()

    max_age = args.max_age
    pr = PodcastReader(args.feeds, max_age=max_age)
    while True:
        choice = input(
            "1. List episodes, 2. browse podcast 3. Add new cast (q to quit). 4. Find new cast on podbean.\n"
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
