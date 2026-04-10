import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
import os
import io
import webbrowser
import plotly.express as px
from PIL import Image, ImageTk


class TimelineDB:

    def __init__(self, db_file="timeline.db"):
        self.db_file = db_file
        self.events = []
        self.categories = []
        self._init_db()

    def load_categories(self):
        with sqlite3.connect(self.db_file) as conn:
            rows = conn.execute("SELECT Title FROM Category ORDER BY CategoryID").fetchall()
        self.categories = [row[0] for row in rows]

    def _init_db(self):

        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS Category (
                    CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Title      TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    title      TEXT NOT NULL,
                    year       INTEGER NOT NULL,
                    desc       TEXT,
                    categoryid INTEGER REFERENCES Category(CategoryID)
                )
            """)
            # Seed categories if empty
            count = conn.execute("SELECT COUNT(*) FROM Category").fetchone()[0]
            if count == 0:
                for cat in ["War", "Science", "Politics", "Exploration", "Culture", "Religion", "General"]:
                    conn.execute("INSERT INTO Category (Title) VALUES (?)", (cat,))
            # Add categoryid column if missing (schema migration)
            cols = [row[1] for row in conn.execute("PRAGMA table_info(events)")]
            if "categoryid" not in cols:
                conn.execute("ALTER TABLE events ADD COLUMN categoryid INTEGER REFERENCES Category(CategoryID)")
            if "url" not in cols:
                conn.execute("ALTER TABLE events ADD COLUMN url TEXT")
            if "image" not in cols:
                conn.execute("ALTER TABLE events ADD COLUMN image BLOB")
                conn.execute("ALTER TABLE events ADD COLUMN image_name TEXT")
                conn.execute("ALTER TABLE events ADD COLUMN image_type TEXT")
        self._migrate_from_json()

    def _migrate_from_json(self, json_file="timeline.json"):
        if not os.path.exists(json_file):
            return
        with sqlite3.connect(self.db_file) as conn:
            count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            if count > 0:
                return
            with open(json_file, "r") as f:
                events = json.load(f)
            for e in events:
                row = conn.execute(
                    "SELECT CategoryID FROM Category WHERE LOWER(Title)=LOWER(?)",
                    (e.get("category", "general"),)
                ).fetchone()
                cat_id = row[0] if row else 7
                conn.execute(
                    "INSERT INTO events (title, year, desc, categoryid) VALUES (?, ?, ?, ?)",
                    (e["title"], e["year"], e.get("desc", ""), cat_id)
                )

    def _category_id(self, conn, category_name):
        row = conn.execute(
            "SELECT CategoryID FROM Category WHERE LOWER(Title)=LOWER(?)", (category_name,)
        ).fetchone()
        return row[0] if row else 7

    def load(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT e.id, e.title, e.year, e.desc, e.categoryid,
                       c.Title as category, e.url,
                       e.image, e.image_name, e.image_type
                FROM events e
                LEFT JOIN Category c ON e.categoryid = c.CategoryID
                ORDER BY e.year
            """).fetchall()
        self.events = [dict(row) for row in rows]

    def save(self):
        with sqlite3.connect(self.db_file) as conn:
            for e in self.events:
                if "id" in e:
                    cat_id = self._category_id(conn, e.get("category", "general"))
                    conn.execute(
                        "UPDATE events SET title=?, year=?, desc=?, categoryid=?, url=?, "
                        "image=?, image_name=?, image_type=? WHERE id=?",
                        (e["title"], e["year"], e["desc"], cat_id, e.get("url", ""),
                         e.get("image"), e.get("image_name"), e.get("image_type"), e["id"])
                    )

    def add(self, title, year, desc, category="general", url="",
            image=None, image_name=None, image_type=None):
        with sqlite3.connect(self.db_file) as conn:
            cat_id = self._category_id(conn, category)
            cursor = conn.execute(
                "INSERT INTO events (title, year, desc, categoryid, url, image, image_name, image_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, year, desc, cat_id, url, image, image_name, image_type)
            )
            new_id = cursor.lastrowid
        self.events.append({"id": new_id, "title": title, "year": year, "desc": desc,
                            "category": category, "categoryid": cat_id, "url": url,
                            "image": image, "image_name": image_name, "image_type": image_type})

    @staticmethod
    def image_to_blob(path, max_size=(200, 200)):
        """Open an image, thumbnail it, and return (blob_bytes, name, fmt)."""
        img = Image.open(path)
        img.thumbnail(max_size, Image.LANCZOS)
        fmt = img.format or "PNG"
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue(), os.path.basename(path), fmt

    def delete_event(self, event):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM events WHERE id=?", (event["id"],))
        self.events[:] = [e for e in self.events if e["id"] != event["id"]]

    def plot(self):
        if not self.events:
            return
        sorted_events = sorted(self.events, key=lambda e: e["year"])
        df = {
            "Year":     [e["year"]                    for e in sorted_events],
            "Event":    [e["title"]                   for e in sorted_events],
            "Desc":     [e["desc"]                    for e in sorted_events],
            "Category": [e.get("category", "general") for e in sorted_events],
        }
        fig = px.scatter(df, x="Year", y=[0] * len(sorted_events), color="Category",
                        hover_name="Event",
                        hover_data={"Desc": True, "Year": True, "Category": True},
                        title="My Historical Timeline", labels={"y": ""})
        fig.update_traces(marker=dict(size=14))
        fig.update_yaxes(visible=False)
        fig.update_layout(legend_title_text="Category")
        fig.write_html("timeline_plot.html")
        webbrowser.open("timeline_plot.html")

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
        fig = px.scatter(df, x="Year", y=[0] * len(sorted_events), color="Category",
                        hover_name="Event",
                        hover_data={"Desc": True, "Year": True, "Category": True},
                        title="My Historical Timeline", labels={"y": ""})
        fig.update_traces(marker=dict(size=14))
        fig.update_yaxes(visible=False)
        fig.update_layout(legend_title_text="Category")
        fig.write_html(filename)
        return True

class TimelineApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Timeline Builder")
        self.root.state("zoomed")
        self.timeline = TimelineDB()
        self.timeline.load()
        self.timeline.load_categories()
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
        input_frame = tk.LabelFrame(content_frame, text="Event", padx=10, pady=10, width=600, height=600)
        input_frame.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 10), pady=5)
        input_frame.grid_propagate(False)

        # ID field (read-only)
        tk.Label(input_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.id_var, width=10, state="readonly").grid(row=0, column=1, padx=5, sticky=tk.W)

        # Title field
        tk.Label(input_frame, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.title_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.title_var, width=40).grid(row=1, column=1, padx=5, sticky=tk.W)

        # Year field
        tk.Label(input_frame, text="Year:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.year_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.year_var, width=40).grid(row=2, column=1, padx=5, sticky=tk.W)

        # Description field
        tk.Label(input_frame, text="Desc:").grid(row=3, column=0, sticky=tk.NW, pady=3)
        desc_frame = tk.Frame(input_frame)
        desc_frame.grid(row=3, column=1, padx=5, pady=3, sticky=tk.W)
        self.desc_text = tk.Text(desc_frame, width=38, height=5, wrap=tk.WORD)
        desc_scroll = tk.Scrollbar(desc_frame, command=self.desc_text.yview)
        self.desc_text.config(yscrollcommand=desc_scroll.set)
        self.desc_text.pack(side=tk.LEFT)
        desc_scroll.pack(side=tk.LEFT, fill=tk.Y)

        # URL field
        tk.Label(input_frame, text="URL:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.url_var = tk.StringVar()
        url_frame = tk.Frame(input_frame)
        url_frame.grid(row=4, column=1, padx=5, sticky=tk.W)
        tk.Entry(url_frame, textvariable=self.url_var, width=35).pack(side=tk.LEFT)
        self.test_url_btn = tk.Button(url_frame, text="Test", command=self.open_link, width=6)
        self.search_url_btn = tk.Button(url_frame, text="Search",
                                        command=lambda: webbrowser.open("https://www.wikipedia.org"), width=6)
        self.search_url_btn.pack(side=tk.LEFT, padx=(4, 0))
        self.url_var.trace("w", lambda *args: self._update_url_buttons())

        # Category dropdown
        tk.Label(input_frame, text="Category:").grid(row=5, column=0, sticky=tk.W, pady=3)
        self.cat_var = tk.StringVar(value=self.timeline.categories[0])
        ttk.Combobox(input_frame, textvariable=self.cat_var,
                    values=self.timeline.categories, width=37).grid(row=5, column=1, padx=5, sticky=tk.W)

        # Image field
        tk.Label(input_frame, text="Image:").grid(row=6, column=0, sticky=tk.NW, pady=3)
        img_ctrl_frame = tk.Frame(input_frame)
        img_ctrl_frame.grid(row=6, column=1, padx=5, sticky=tk.W)
        self.image_name_var = tk.StringVar(value="")
        tk.Label(img_ctrl_frame, textvariable=self.image_name_var,
                 font=("Arial", 8), fg="gray").pack(side=tk.TOP, anchor=tk.W)
        img_btn_frame = tk.Frame(img_ctrl_frame)
        img_btn_frame.pack(side=tk.TOP, anchor=tk.W)
        tk.Button(img_btn_frame, text="Browse...",
                  command=self.browse_image, width=10).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(img_btn_frame, text="Clear",
                  command=self.clear_image, width=6).pack(side=tk.LEFT, padx=(0, 4))
        self._blank_photo = ImageTk.PhotoImage(Image.new("RGB", (200, 200), "#f0f0f0"))
        self.image_preview = tk.Label(input_frame, relief=tk.SUNKEN,
                                      image=self._blank_photo, bg="#f0f0f0")
        self.image_preview.grid(row=7, column=1, padx=5, pady=4, sticky=tk.W)
        self._current_image_blob = None
        self._current_image_name = None
        self._current_image_type = None
        self._preview_photo = None  # keep reference to prevent GC

        # Buttons
        ttk.Separator(input_frame, orient=tk.HORIZONTAL).grid(
            row=8, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=(10, 0))

        btn_frame = tk.Frame(input_frame, pady=10)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=10)

        for text, cmd in [("Save", self.add_event), ("New", self.clear_fields), ("Delete", self.delete_selected)]:
            tk.Button(btn_frame, text=text, command=cmd, width=12).pack(side=tk.LEFT, padx=6)

        # --- Middle column: Events list (with search and filter inside) ---
        list_frame = tk.LabelFrame(content_frame, text="Event List", padx=10, pady=10, width=600, height=600)
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
        filter_options = ["all"] + self.timeline.categories
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
        listbox_frame = tk.Frame(list_frame, height=540)
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
        self.id_var.set(evt.get("id", ""))
        self.title_var.set(evt["title"])
        self.year_var.set(evt["year"])
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", evt.get("desc") or "")
        self.url_var.set(evt.get("url") or "")
        self.cat_var.set(evt.get("category", "general"))
        self._update_url_buttons()
        self._current_image_blob = evt.get("image")
        self._current_image_name = evt.get("image_name")
        self._current_image_type = evt.get("image_type")
        self.image_name_var.set(evt.get("image_name") or "")
        self._show_preview(evt.get("image"))

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
            self.timeline.delete_event(event)
            self.clear_fields()
            self.refresh_list()
            self.set_status(f"Deleted: {event['title']}")

    def add_event(self):
        title = self.title_var.get().strip()
        desc  = self.desc_text.get("1.0", tk.END).strip()
        url   = self.url_var.get().strip()
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
            self.editing_event["title"]      = title
            self.editing_event["year"]       = year
            self.editing_event["desc"]       = desc
            self.editing_event["url"]        = url
            self.editing_event["category"]   = cat
            self.editing_event["image"]      = self._current_image_blob
            self.editing_event["image_name"] = self._current_image_name
            self.editing_event["image_type"] = self._current_image_type
            self.timeline.save()
            self.clear_fields()
            self.refresh_list()
            self.set_status(f"Updated: {title} ({year})")
        else:
            self.timeline.add(title, year, desc, cat, url,
                              self._current_image_blob,
                              self._current_image_name,
                              self._current_image_type)
            self.clear_fields()
            self.refresh_list()
            self.set_status(f"Added: {title} ({year})")

    def _update_url_buttons(self):
        if self.url_var.get().strip():
            self.search_url_btn.pack_forget()
            self.test_url_btn.pack(side=tk.LEFT, padx=(4, 0))
        else:
            self.test_url_btn.pack_forget()
            self.search_url_btn.pack(side=tk.LEFT, padx=(4, 0))

    def open_link(self):
        url = self.url_var.get().strip()
        if url:
            webbrowser.open(url)

    def browse_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            blob, name, fmt = TimelineDB.image_to_blob(path)
            self._current_image_blob = blob
            self._current_image_name = name
            self._current_image_type = fmt
            self.image_name_var.set(name)
            self._show_preview(blob)
            self.set_status(f"Image loaded: {name}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

    def clear_image(self):
        self._current_image_blob = None
        self._current_image_name = None
        self._current_image_type = None
        self._preview_photo = None
        self.image_name_var.set("")
        self.image_preview.config(image=self._blank_photo)

    def _show_preview(self, blob):
        if not blob:
            self.image_preview.config(image=self._blank_photo)
            return
        img = Image.open(io.BytesIO(blob))
        self._preview_photo = ImageTk.PhotoImage(img)
        self.image_preview.config(image=self._preview_photo, width=img.width, height=img.height)

    def clear_fields(self):
        self.id_var.set("")
        self.title_var.set("")
        self.year_var.set("")
        self.desc_text.delete("1.0", tk.END)
        self.url_var.set("")
        self.cat_var.set(self.timeline.categories[0])
        self.editing_event = None
        self.listbox.selection_clear(0, tk.END)
        self._update_url_buttons()
        self.clear_image()

    def plot(self):
        self.timeline.plot()

if __name__ == "__main__":
    root = tk.Tk()
    app = TimelineApp(root)
    root.mainloop()
