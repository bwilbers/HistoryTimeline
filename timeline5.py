import json
FILENAME = "timeline.json"

def save_timeline(events):
    with open(FILENAME, "w") as f:
        json.dump(events, f)
        print("Timeline saved.")

def load_timeline():
    try:
        with open(FILENAME, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def create_event(title, year, desc):
    return {"title": title, "year": year, "desc": desc}

def delete_event(events):
    show_timeline(events)
    year = int(input("Enter the year of the event to delete: "))
    original_length = len(events)
    events[:] = [e for e in events if e["year"] != year]
    if len(events) < original_length:
        print("Event deleted.")
        save_timeline(events)
    else:
        print("No event found for that year.")
        
def add_event(events):
    title = input("Event title: ")
    year  = int(input("Year: "))
    desc  = input("Description: ")
    events.append(create_event(title, year, desc))
    print("Event added!")

def sort_timeline(events):
    return sorted(events, key=lambda e: e["year"])

def show_timeline(events):
    if len(events) == 0:
        print("No events yet.")
        return
    print("\n--- Your Timeline ---")
    for e in sort_timeline(events):
        print(f"{e['year']} — {e['title']}: {e['desc']}")

def show_menu():
    print("\nWhat would you like to do?")
    print("  1 — Add an event")
    print("  2 — View timeline")
    print("  3 - Save")
    print("  4 — Delete")
    print("  5 — Quit")

events = []

events = load_timeline()
print(f"Loaded {len(events)} events from disk.")

while True:
    show_menu()
    choice = input("Enter 1-5: ")
    if choice == "1":
        add_event(events)
    elif choice == "2":
        show_timeline(events)
    elif choice == "3":
        save_timeline(events)
    elif choice == "4":
        delete_event(events)
    elif choice == "5":
        print("Goodbye!")
        break
    else:
        print("\nInvalid choice — please enter 1-5.")