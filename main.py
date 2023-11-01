import sys
import webbrowser

from podcasts import PodcastReader

MAX_AGE = 30 # episodes older than MAX_AGE days, are hidden
    
def select_cast(podcasts):
    command = None    
    while command != "q":
        print("Select cast: (q to quit)")
        for i,p in enumerate(podcasts):
            print(f"{i+1}. {p}")
        selected_cast = input("")
        try:
            if selected_cast == "q": break
            select_eps([podcasts[int(selected_cast)-1]])
        except Exception as e:
            print(f"Invalid command: {e}.")

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
    feeds = sys.argv[1] if len(sys.argv)>1 else "feeds.txt"
    pr = PodcastReader(feeds, max_age=MAX_AGE)
    while True:
        choice = input("1. List episodes, 2. browse podcast (q to quit).\n")
        try:
            choice = int(choice)
        except Exception as e:
            print("Invalid command.")
            sys.exit()
        if choice == 1:
            select_eps(pr.podcasts)
        elif choice == 2:
            select_cast(pr.podcasts)
