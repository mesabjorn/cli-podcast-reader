import argparse
import sys
import urllib
import webbrowser
from enum import Enum
from pathlib import Path


from app.exit_commands import EXIT_COMMANDS, exit_commands
from app.podcasts import Episode, Podcast, PodcastReader
from app import LOGGER
from app.user_input import await_user_input


class EPISODE_ACTION(Enum):
    PLAY = 1
    DOWNLOAD = 2


class MAIN_MENU(Enum):
    LIST_EPISODES = 1
    BROWSE_PODCAST = 2
    ADD_PODCAST = 3
    FIND_PODCAST = 4


class PodcastMenu:
    """CLI Menu for browsing, playing, and downloading podcast episodes."""

    def __init__(self, feeds_file: Path, max_age: int = 30):
        if not feeds_file.exists():
            self._init_feeds(feeds_file)

        self.reader = PodcastReader(feeds_file, max_age=max_age)

    # ----------------------------
    # Menu control
    # ----------------------------

    def run(self):
        """Main menu loop."""
        while True:
            action = await_user_input(
                MAIN_MENU,
                prompt="What do you want to do?",
                exit_values=EXIT_COMMANDS,
            )

            if action is None:
                break

            match action:
                case MAIN_MENU.LIST_EPISODES:
                    self._list_all_episodes()
                case MAIN_MENU.BROWSE_PODCAST:
                    self._browse_podcasts()
                case MAIN_MENU.ADD_PODCAST:
                    self._add_podcast()
                case MAIN_MENU.FIND_PODCAST:
                    self._search_podbean()
                case _:
                    LOGGER.error("Invalid command.")

    # ----------------------------
    # Menu actions
    # ----------------------------

    def _list_all_episodes(self):
        """Display all episodes from all podcasts."""
        episodes = []
        for podcast in self.reader.podcasts:
            episodes.extend(podcast.episodes)

        episodes.sort(key=lambda ep: ep.date, reverse=True)

        while True:
            print("\n--- Episodes ---")
            for i, ep in enumerate(episodes, start=1):
                print(f"{i}. {ep}")

            selection = (
                input(f"Episode number to open {exit_commands()}: ").strip().lower()
            )

            if selection in EXIT_COMMANDS:
                break

            if not selection.isdigit():
                print("Please enter a valid number.")
                continue

            idx = int(selection) - 1
            if idx < 0 or idx >= len(episodes):
                print("Invalid episode number.")
                continue

            episode = episodes[idx]
            self._handle_episode_action(episode)

    def _browse_podcasts(self):
        """Select a podcast and browse its episodes."""
        podcasts = self.reader.podcasts
        while True:
            print("\n--- Podcasts ---")
            for i, p in enumerate(podcasts, start=1):
                print(f"{i}. {p}")

            selection = input(f"Select podcast {exit_commands()}: ").strip().lower()
            if selection in EXIT_COMMANDS:
                break

            if not selection.isdigit():
                print("Please enter a valid number.")
                continue

            idx = int(selection) - 1
            if idx < 0 or idx >= len(podcasts):
                print("Invalid podcast number.")
                continue

            podcast = podcasts[idx]
            self._list_podcast_episodes(podcast)

    def _list_podcast_episodes(self, podcast: Podcast):
        """List episodes for a single podcast."""
        while True:
            print(f"\n--- {podcast.title} ---")
            for i, ep in enumerate(podcast.episodes, start=1):
                print(f"{i}. {ep}")

            selection = (
                input(f"Episode number to open {exit_commands()}: ").strip().lower()
            )
            if selection in EXIT_COMMANDS:
                break

            if not selection.isdigit():
                print("Please enter a valid number.")
                continue

            idx = int(selection) - 1
            if idx < 0 or idx >= len(podcast.episodes):
                print("Invalid episode number.")
                continue

            episode = podcast.episodes[idx]
            self._handle_episode_action(episode)

    def _handle_episode_action(self, episode: Episode):
        """Ask the user what to do with the selected episode."""

        action = await_user_input(
            EPISODE_ACTION,
            prompt="What do you want to do with this episode?",
            exit_values=EXIT_COMMANDS,
        )

        if action is None:
            return

        match action:
            case EPISODE_ACTION.PLAY:
                if not episode.link:
                    LOGGER.warning("Episode has no playable link.")
                    return
                LOGGER.info(f"Opening {episode.link}")
                webbrowser.open(episode.link)
            case EPISODE_ACTION.DOWNLOAD:
                self._download_episode(episode)

    def _download_episode(self, episode: Episode):
        """Download the given episode."""
        download_dir = Path("./download")
        download_dir.mkdir(exist_ok=True)

        if not episode.link:
            LOGGER.warning("Cannot download — episode has no link.")
            return

        LOGGER.info(f"Downloading {episode.link}")
        downloaded_file = episode.download(to=download_dir)
        LOGGER.info(f"Downloaded episode to '{downloaded_file}'")

    def _add_podcast(self):
        """Add a new podcast feed."""
        name = input("Podcast name: ").strip()
        url = input("Feed URL: ").strip()

        if not name or not url:
            LOGGER.warning("Both name and URL are required.")
            return

        self.reader.add_feed(name, url)
        LOGGER.info(f"Added new feed: {name}")

    def _search_podbean(self):
        """Search for a podcast on Podbean."""
        name = input("Search term: ").strip()
        if not name:
            LOGGER.warning("Search term cannot be empty.")
            return

        query = urllib.parse.quote(name)
        url = f"https://www.podbean.com/site/search/index?v={query}"
        LOGGER.info(f"Opening Podbean search for '{name}'")
        webbrowser.open(url)

    # ----------------------------
    # Helpers
    # ----------------------------

    def _init_feeds(self, path: Path):
        """Initialize a new feeds file with a template."""
        with path.open("wt") as f:
            f.write("# Enter your podcasts here in name, url format\n")
        LOGGER.info(f"Initialized new feeds file at {path}")


# ----------------------------
# Entry point
# ----------------------------


def parse_args():
    parser = argparse.ArgumentParser("CLI-Podcast browser")
    parser.add_argument(
        "feeds",
        type=Path,
        default=Path("./feeds.txt"),
        nargs="?",
        help="Path to the feeds file (default: ./feeds.txt)",
    )
    parser.add_argument(
        "--max-age",
        metavar="m",
        dest="max_age",
        type=int,
        default=30,
        help="Maximum age in days (default: 30)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    menu = PodcastMenu(args.feeds, args.max_age)
    menu.run()


if __name__ == "__main__":
    main()
