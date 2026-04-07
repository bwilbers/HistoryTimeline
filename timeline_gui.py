import tkinter as tk
from tkinter import ttk, messagebox
from timeline_class import Timeline, CATEGORIES

class TimelineApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Timeline Builder")
        self.root.state("zoomed")
        self.timeline = Timeline()
        self.timeline.load()
        self.editing_event = None
        self.build_ui()

    def export_html(self):
        if self.timeline.export_html():
            self.set_status("Exported to timeline_export.html")
            messagebox.showinfo("Exported",
                "Timeline saved as timeline_export.html\n"
                "Open it in any browser to view.")
        else:
            self.set_status("No events to export.")

    def build_ui(self):
        main = tk.Frame(self.root, padx=10, pady=10)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="Historical Timeline Builder",
                font=("Arial", 16, "bold")).pack(pady=5)

        # Status bar at bottom (packed before expanding content)
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(main, textvariable=self.status_var,
                            anchor=tk.W, relief=tk.SUNKEN,
                            font=("Arial", 9), padx=5)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)

        # Two-column content frame
        content_frame = tk.Frame(main)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Left column: Add Event ---
        input_frame = tk.LabelFrame(content_frame, text="Event", padx=10, pady=10, width=600, height=400)
        input_frame.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 10), pady=5)
        input_frame.grid_propagate(False)

        # Title field
        tk.Label(input_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.title_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.title_var, width=40).grid(row=0, column=1, padx=5, sticky=tk.W)

        # Year field
        tk.Label(input_frame, text="Year:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.year_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.year_var, width=40).grid(row=1, column=1, padx=5, sticky=tk.W)

        # Description field
        tk.Label(input_frame, text="Desc:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.desc_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.desc_var, width=40).grid(row=2, column=1, padx=5, sticky=tk.W)

        # Category dropdown
        tk.Label(input_frame, text="Category:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.cat_var = tk.StringVar(value=CATEGORIES[0])
        ttk.Combobox(input_frame, textvariable=self.cat_var,
                    values=CATEGORIES, width=37).grid(row=3, column=1, padx=5, sticky=tk.W)

        # Buttons
        btn_frame = tk.Frame(input_frame, pady=10)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="Save",
                command=self.add_event,
                width=12).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="New",
                command=self.clear_fields,
                width=8).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Delete",
                command=self.delete_selected,
                width=14).pack(side=tk.LEFT, padx=6)

        # --- Middle column: Events list (with search and filter inside) ---
        list_frame = tk.LabelFrame(content_frame, text="Event List", padx=10, pady=10, width=600, height=400)
        list_frame.pack(side=tk.LEFT, anchor=tk.N, pady=5)
        list_frame.pack_propagate(False)

        # Search, filter and sort on one line
        search_frame = tk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=5)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.refresh_list())
        tk.Entry(search_frame, textvariable=self.search_var,
                width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Clear Search",
                command=lambda: self.search_var.set("")).pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="Filter:").pack(side=tk.LEFT, padx=(10, 5))
        self.active_filter = tk.StringVar(value="all")
        filter_options = ["all"] + CATEGORIES
        ttk.Combobox(search_frame, textvariable=self.active_filter,
                    values=filter_options, width=15,
                    state="readonly").pack(side=tk.LEFT, padx=5)
        self.active_filter.trace("w", lambda *args: self.refresh_list())

        tk.Label(search_frame, text="Sort by:").pack(side=tk.LEFT, padx=(10, 5))
        self.sort_var = tk.StringVar(value="year")
        ttk.Combobox(search_frame, textvariable=self.sort_var,
                    values=["year", "title", "category"],
                    width=10, state="readonly").pack(side=tk.LEFT, padx=5)
        self.sort_var.trace("w", lambda *args: self.refresh_list())

        # Scrollable listbox fixed at 400px height
        listbox_frame = tk.Frame(list_frame, height=400)
        listbox_frame.pack(fill=tk.X, expand=False)
        listbox_frame.pack_propagate(False)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set,
                                font=("Courier", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # --- Third column: Actions ---
        actions_frame = tk.LabelFrame(content_frame, text="Actions", padx=10, pady=10)
        actions_frame.pack(side=tk.LEFT, anchor=tk.N, padx=(10, 0), pady=5)

        tk.Button(actions_frame, text="Plot Timeline",
                command=self.plot,
                width=14).pack(pady=6)
        tk.Button(actions_frame, text="Export HTML",
                command=self.export_html,
                width=14).pack(pady=6)

        self.refresh_list()

    def set_status(self, message, duration=3000):
        self.status_var.set(message)
        self.root.after(duration, lambda: self.status_var.set("Ready"))

    def _visible_events(self):
        keyword = self.search_var.get().lower().strip()
        active = self.active_filter.get()
        sorted_events = sorted(self.timeline.events, key=lambda e: e["year"])
        result = []
        for e in sorted_events:
            cat = e.get("category", "general")
            if active != "all" and cat != active:
                continue
            if keyword and keyword not in e["title"].lower() \
                    and keyword not in e["desc"].lower() \
                    and keyword not in str(e["year"]) \
                    and keyword not in cat.lower():
                continue
            result.append(e)
        return result

    def on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        evt = self._visible_events()[selection[0]]
        self.editing_event = evt
        self.title_var.set(evt["title"])
        self.year_var.set(evt["year"])
        self.desc_var.set(evt["desc"])
        self.cat_var.set(evt.get("category", "general"))

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        keyword = self.search_var.get().lower().strip()
        active  = self.active_filter.get()
        sort_key = self.sort_var.get()
        if sort_key == "year":
            sorted_events = sorted(self.timeline.events,
                                key=lambda e: e["year"])
        elif sort_key == "title":
            sorted_events = sorted(self.timeline.events,
                                key=lambda e: e["title"].lower())
        else:
            sorted_events = sorted(self.timeline.events,
                                key=lambda e: e.get("category", "general"))
        count = 0
        for e in sorted_events:
            cat = e.get("category", "general")
            if active != "all" and cat != active:
                continue
            if keyword and keyword not in e["title"].lower() \
                    and keyword not in e["desc"].lower() \
                    and keyword not in str(e["year"]) \
                    and keyword not in cat.lower():
                continue
            self.listbox.insert(tk.END,
                f"{e['year']:>6}  {e['title']:<30} [{cat}]")
            count += 1
        total = len(self.timeline.events)
        if count == total:
            self.root.title(f"Timeline Builder — {total} events")
        else:
            self.root.title(f"Timeline Builder — {count} of {total} events")

        if count == 0 and (keyword or active != "all"):
                self.set_status("No events match the current filter.")
        else:
            self.status_var.set("Ready")
                
    def delete_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an event to delete.")
            return
        index = selection[0]
        event = self._visible_events()[index]
        confirm = messagebox.askyesno("Confirm",
                    f"Delete '{event['title']}'?")
        if confirm:
            self.timeline.events[:] = [e for e in self.timeline.events
                                    if e["title"] != event["title"]]
            self.timeline.save()
            self.clear_fields()
            self.refresh_list()
            self.set_status(f"Deleted: {event['title']}")

    def add_event(self):
        title = self.title_var.get().strip()
        desc  = self.desc_var.get().strip()
        cat   = self.cat_var.get()
        try:
            year = int(self.year_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return
        if not title:
            messagebox.showerror("Error", "Please enter a title.")
            return
        if self.editing_event is not None:
            self.editing_event["title"]    = title
            self.editing_event["year"]     = year
            self.editing_event["desc"]     = desc
            self.editing_event["category"] = cat
            self.timeline.save()
            self.clear_fields()
            self.refresh_list()
            self.set_status(f"Updated: {title} ({year})")
        else:
            self.timeline.add(title, year, desc, cat)
            self.clear_fields()
            self.refresh_list()
            self.set_status(f"Added: {title} ({year})")
        
    def clear_fields(self):
        self.title_var.set("")
        self.year_var.set("")
        self.desc_var.set("")
        self.cat_var.set(CATEGORIES[0])
        self.editing_event = None
        self.listbox.selection_clear(0, tk.END)

    def plot(self):
        self.timeline.plot()

if __name__ == "__main__":
    root = tk.Tk()
    app = TimelineApp(root)
    root.mainloop()
