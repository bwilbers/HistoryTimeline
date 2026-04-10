def create_event(title, year, desc):
    return {"title": title, "year": year, "desc": desc}

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
    print("  3 — Quit")

events = []

while True:
    show_menu()
    choice = input("Enter 1, 2 or 3: ")
    if choice == "1":
        add_event(events)
    elif choice == "2":
        show_timeline(events)
    elif choice == "3":
        print("Goodbye!")
        break
    else:
        print("Invalid choice — please enter 1, 2 or 3.")