def create_event(title, year, desc):
    return {"title": title, "year": year, "desc": desc}

def add_event(events):
    title = input("\nEvent title: ")
    year = int(input("Year: "))
    desc = input("Description: ")
    events.append(create_event(title, year, desc))

def show_timeline(events):
    print("\n--- Your Timeline ---")
    for e in sort_timeline(events):
        print(f"{e['year']} — {e['title']}: {e['desc']}")

def sort_timeline(events):
    return sorted(events, key=lambda e: e["year"])

events = []
add_event(events)
add_event(events)
add_event(events)

choice = input("Sort by (year/title): ")
sorted_events = sorted(events, key=lambda e: e[choice])

show_timeline(events)