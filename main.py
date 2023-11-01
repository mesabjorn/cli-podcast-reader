import sys
import webbrowser

from podcasts import PodcastReader

MAX_AGE = 14 # episodes older than MAX_AGE days, are hidden
    
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
    feeds = sys.argv[1] if len(sys.argv)>1 else "feeds.txt"
    pr = PodcastReader(feeds, max_age=MAX_AGE)

    # select_cast(podcasts)
    select_eps(pr.podcasts)
