import json
import webbrowser
import plotly.express as px
import pandas as pd

CATEGORIES = ["war", "science", "politics", "exploration", "culture", "religion", "general"]    

def get_category():
    print("Categories:", ", ".join(CATEGORIES))
    category = input("Choose a category: ").lower().strip()
    if category not in CATEGORIES:
        print("Unknown category, using 'general'")
        return "general"
    return category

class Timeline:
    
    ERAS = {
        "ancient":  (0,    500),
        "medieval": (500,  1500),
        "modern":   (1500, 2100),
        "sixties":  (1960, 1970),
    }

    def __init__(self):
        self.events = []

    
    def add(self, title, year, desc, category="general"):
        self.events.append({
            "title":    title,
            "year":     year,
            "desc":     desc,
            "category": category
        })
        self.save()

    def show(self):
        if not self.events:
            print("No events yet.")
            return
        for e in sorted(self.events, key=lambda e: e["year"]):
            print(f"{e['year']} — {e['title']}: {e['desc']}")

    def load(self, filename="timeline.json"):
        try:
            with open(filename, "r") as f:
                self.events = json.load(f)
        except FileNotFoundError:
            self.events = []

    def save(self, filename="timeline.json"):
        with open(filename, "w") as f:
            json.dump(self.events, f)
        print("Timeline saved.")

    def delete(self, year):
        original_length = len(self.events)
        self.events[:] = [e for e in self.events if e["year"] != year]
        if len(self.events) < original_length:
            print("Event deleted.")
            self.save()
        else:
            print("No event found for that year.")

    def delete_by_title(self, title):
        original_length = len(self.events)
        self.events[:] = [e for e in self.events if e["title"].lower() != title.lower()]
        if len(self.events) < original_length:
            print("Event deleted.")
            self.save()
        else:
            print("No event found with that title.")

    def search(self, keyword):
        keyword = keyword.lower()
        results = [e for e in self.events
        if keyword in e["title"].lower()
        or keyword in e["desc"].lower()
        or keyword in str(e["year"])]
        return results

    def plot(self):
        if not self.events:
            print("No events to plot.")
            return
        sorted_events = sorted(self.events, key=lambda e: e["year"])
        df = {
            "Year":     [e["year"]                          for e in sorted_events],
            "Event":    [e["title"]                         for e in sorted_events],
            "Desc":     [e["desc"]                          for e in sorted_events],
            "Category": [e.get("category", "general")       for e in sorted_events],
        }
        fig = px.scatter(
            df,
            x="Year",
            y=[0] * len(sorted_events),
            color="Category",
            hover_name="Event",
            hover_data={"Desc": True, "Year": True, "Category": True},
            title="My Historical Timeline",
            labels={"y": ""},
        )
        fig.update_traces(marker=dict(size=14))
        fig.update_yaxes(visible=False)
        fig.update_layout(legend_title_text="Category")
        fig.write_html("timeline_plot.html")
        webbrowser.open("timeline_plot.html")

    def get_plot_html(self):
        if not self.events:
            return "<html><body><p>No events to plot.</p></body></html>"
        sorted_events = sorted(self.events, key=lambda e: e["year"])
        df = {
            "Year":     [e["year"]                          for e in sorted_events],
            "Event":    [e["title"]                         for e in sorted_events],
            "Desc":     [e["desc"]                          for e in sorted_events],
            "Category": [e.get("category", "general")       for e in sorted_events],
        }
        fig = px.scatter(
            df,
            x="Year",
            y=[0] * len(sorted_events),
            color="Category",
            hover_name="Event",
            hover_data={"Desc": True, "Year": True, "Category": True},
            title="My Historical Timeline",
            labels={"y": ""},
        )
        fig.update_traces(marker=dict(size=14))
        fig.update_yaxes(visible=False)
        fig.update_layout(legend_title_text="Category")
        return fig.to_html(include_plotlyjs=True, full_html=True)

    def export_html(self, filename="timeline_export.html"):
        if not self.events:
            return False
        sorted_events = sorted(self.events, key=lambda e: e["year"])
        df = {
            "Year":     [e["year"]                    for e in sorted_events],
            "Event":    [e["title"]                   for e in sorted_events],
            "Desc":     [e["desc"]                    for e in sorted_events],
            "Category": [e.get("category", "general") for e in sorted_events],
        }
        fig = px.scatter(
            df,
            x="Year",
            y=[0] * len(sorted_events),
            color="Category",
            hover_name="Event",
            hover_data={"Desc": True, "Year": True, "Category": True},
            title="My Historical Timeline",
            labels={"y": ""},
        )
        fig.update_traces(marker=dict(size=14))
        fig.update_yaxes(visible=False)
        fig.update_layout(legend_title_text="Category")
        fig.write_html(filename)
        return True

    def filter_by_era(self, era_name):
        if era_name not in self.ERAS:
            print(f"Unknown era. Try: {list(self.ERAS.keys())}")
            return []

        start, end = self.ERAS[era_name]
        return [e for e in self.events if start <= e["year"] < end]

# Main program
if __name__ == "__main__":
    t = Timeline()
    t.load()
    print(f"Loaded {len(t.events)} events from disk.")

    while True:
        print("\nWhat would you like to do?")
        print("  1 — Add an event")
        print("  2 — View timeline")
        print("  3 — Delete by year")
        print("  4 — Delete by title")
        print("  5 — Save")
        print("  6 — Search")
        print("  7 — Search by era")
        print("  8 — Plot timeline")        
        print("  9 — Quit")

        choice = input("Enter choice: ")

        if choice == "1":
            title    = input("Event title: ")
            try:
                year = int(input("Year: "))
            except ValueError:
                print("Please enter a valid number.")
                continue
            desc     = input("Description: ")
            category = get_category()
            t.add(title, year, desc, category)
        elif choice == "2":
            t.show()
        elif choice == "3":
            t.show()
            try:
                year = int(input("Enter year to delete: "))
            except ValueError:
                print("Please enter a valid number.")
                continue
            t.delete(year)
        elif choice == "4":
            t.show()
            title = input("Enter title to delete: ")
            t.delete_by_title(title)
        elif choice == "5":
            t.save()
        elif choice == "6":
            keyword = input("Search for: ")
            results = t.search(keyword)
            if not results:
                print("No events found.")
            else:
                print(f"\n{len(results)} result(s) found:")
                for e in results:
                    print(f"{e['year']} — {e['title']}: {e['desc']}")
        elif choice == "7":
            print(f"Available eras: {list(Timeline.ERAS.keys())}")
            era = input("Enter era: ").lower()
            results = t.filter_by_era(era)
            if not results:
                print("No events found for that era.")
            else:
                print(f"\n{len(results)} event(s) in the {era} era:")
                for e in results:
                    print(f"{e['year']} — {e['title']}: {e['desc']}")
        elif choice == "8":
            t.plot()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid choice — please enter 1 to 8.")