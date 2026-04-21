"""
Publish to TimelineHub — dialog and publisher for the HistoryTimeline desktop app.

Requires:  pip install supabase
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import io
import json
import tempfile

SUPABASE_URL    = "https://tbpjthbywlgbxokfhhji.supabase.co"
SUPABASE_KEY    = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                   ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRicGp0aGJ5d2xnYnhva2ZoaGppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2Mzc2NDUsImV4cCI6MjA5MjIxMzY0NX0"
                   ".GGsTxHqnuCtmCWyTZB0aDKhHiqbTR9ooiqzQY-DjZYo")
PLATFORM_URL    = "https://project-549x3.vercel.app"
CATEGORIES      = ["History", "Science", "Biography", "Technology", "Geography", "Politics"]
_CREDS_FILE     = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".timelinehub_creds.json")
_STORAGE_BUCKET = "timeline-images"


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_saved_email():
    try:
        with open(_CREDS_FILE) as f:
            return json.load(f).get("email", "")
    except Exception:
        return ""


def _save_email(email):
    try:
        with open(_CREDS_FILE, "w") as f:
            json.dump({"email": email}, f)
    except Exception:
        pass


def _content_type(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    return {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif":  "image/gif",
        ".bmp":  "image/bmp",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def _upload_image(storage, path: str, blob, filename: str):
    """Upload (or overwrite) blob in storage and return its public URL.

    Writes to a temp file so the SDK receives a file path, which
    works across all supabase-py/storage3 versions.
    Returns None and skips silently if blob is not valid binary data.
    """
    # Guard: SQLite occasionally returns BLOB columns as str when the
    # value was inserted without explicit bytes type. Skip rather than crash.
    if isinstance(blob, str):
        return None
    if blob is None:
        return None

    suffix = os.path.splitext(filename or ".png")[1] or ".png"
    fd, tmp_path = None, None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        data = blob if isinstance(blob, (bytes, bytearray)) else bytes(blob)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        fd = None  # fdopen took ownership
        storage.from_(_STORAGE_BUCKET).upload(
            path, tmp_path,
            {"content-type": _content_type(filename), "upsert": "true"},
        )
    finally:
        if fd is not None:
            os.close(fd)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return storage.from_(_STORAGE_BUCKET).get_public_url(path)


# ── publisher ─────────────────────────────────────────────────────────────────

class TimelineHubPublisher:
    """Handles auth and publishing to TimelineHub via Supabase."""

    def __init__(self):
        self._client  = None
        self._user_id = None

    def sign_in(self, email: str, password: str):
        from supabase import create_client
        self._client  = create_client(SUPABASE_URL, SUPABASE_KEY)
        resp = self._client.auth.sign_in_with_password({"email": email, "password": password})
        self._user_id = resp.user.id
        # Explicitly apply the session so all subsequent table/storage calls
        # carry the user's JWT and satisfy RLS policies.
        self._client.auth.set_session(
            resp.session.access_token, resp.session.refresh_token
        )

    def publish(self, db, title: str, description: str, browse_category: str,
                status_cb=None) -> str:
        """
        Publish (or re-publish) structured timeline data to the four Supabase tables.
        Returns the live page URL.

        On first publish: inserts a new timeline row and saves the UUID locally.
        On re-publish:    deletes the old categories/events/breaks and updates the
                          existing timeline row so the URL stays the same.

        Storage paths use local SQLite IDs so images are overwritten cleanly on
        re-publish rather than accumulating orphaned files.
        """
        c     = self._client
        uid   = self._user_id
        tl_id = db.active_timeline_id

        def _status(msg):
            if status_cb:
                status_cb(msg)

        # ── load all data from the local database ─────────────────────────────
        _status("Loading timeline data…")
        db.load()
        db.load_categories()
        ruler_min, ruler_max, ruler_max_is_present = db.load_timeline_ruler(tl_id)
        view_state           = db.load_timeline_view_state(tl_id)
        cat_header_style     = db.load_timeline_cat_header_style(tl_id)
        cat_header_title_pos = db.load_timeline_cat_header_title_pos(tl_id)
        canvas_bg_color      = db.load_timeline_canvas_bg(tl_id)
        bg_image, bg_image_name, bg_image_pos = db.load_timeline_bg_image(tl_id)
        breaks               = db.load_timeline_breaks(tl_id)

        tl_payload = {
            "title":                title,
            "user_id":              uid,
            "description":          description,
            "browse_category":      browse_category,
            "px_per_year":          view_state["px_per_year"] if view_state else None,
            "ruler_min":            ruler_min,
            "ruler_max":            ruler_max,
            "ruler_max_is_present": bool(ruler_max_is_present),
            "cat_header_style":     cat_header_style or "Left",
            "cat_header_title_pos": cat_header_title_pos or "Center (View)",
            "canvas_bg_color":      canvas_bg_color,
            "bg_image_pos":         bg_image_pos or "Top",
        }

        # ── step 1: insert or update the timeline row ─────────────────────────
        existing_uuid = db.get_published_id(tl_id)

        if existing_uuid:
            # Re-publish: wipe old child records, keep the same UUID and URL
            _status("Updating existing timeline record…")
            c.table("timeline_break").delete().eq("timeline_id", existing_uuid).execute()
            c.table("event").delete().eq("timeline_id", existing_uuid).execute()
            c.table("category").delete().eq("timeline_id", existing_uuid).execute()
            c.table("timeline").update(tl_payload).eq("id", existing_uuid).execute()
            new_tl_id = existing_uuid
        else:
            # First publish: insert and remember the generated UUID
            _status("Creating timeline record…")
            row = c.table("timeline").insert(tl_payload).execute()
            new_tl_id = row.data[0]["id"]
            db.save_published_id(tl_id, new_tl_id)

        # ── step 2: insert categories ─────────────────────────────────────────
        # cat_nodes is depth-first so parents always appear before children.
        # Storage paths use the stable local SQLite ID so images overwrite cleanly.
        cat_id_map = {}   # local SQLite CategoryID → Supabase bigint id
        total_cats = len(db.cat_nodes)
        for i, node in enumerate(db.cat_nodes):
            _status(f"Publishing categories… ({i + 1}/{total_cats})")
            new_parent_id = cat_id_map.get(node["parent_id"]) if node["parent_id"] else None
            cat_row = c.table("category").insert({
                "timeline_id":    new_tl_id,
                "parent_id":      new_parent_id,
                "title":          node["title"],
                "sort_order":     node.get("sort_order") or i,
                "hidden":         bool(node.get("hidden")),
                "color":          node.get("color"),
                "row_bg_color":   node.get("row_bg_color"),
                "show_row_guide": bool(node.get("show_row_guide", True)),
                "cat_image_pos":  node.get("cat_image_pos") or "Row",
                "cat_pad_top":    int(node.get("cat_pad_top") or 0),
                "cat_pad_bottom": int(node.get("cat_pad_bottom") or 0),
            }).execute()
            new_cat_id = cat_row.data[0]["id"]
            cat_id_map[node["id"]] = new_cat_id

            if node.get("cat_image"):
                img_name     = node.get("cat_image_name") or "image.png"
                storage_path = f"categories/{node['id']}/{img_name}"
                img_url = _upload_image(c.storage, storage_path,
                                        node["cat_image"], img_name)
                if img_url:
                    c.table("category").update(
                        {"cat_image_url": img_url}
                    ).eq("id", new_cat_id).execute()

        # ── step 3: insert events ─────────────────────────────────────────────
        total_evts = len(db.events)
        for i, evt in enumerate(db.events):
            _status(f"Publishing events… ({i + 1}/{total_evts})")
            new_cat_id = cat_id_map.get(evt.get("categoryid"))
            evt_row = c.table("event").insert({
                "timeline_id":        new_tl_id,
                "category_id":        new_cat_id,
                "title":              evt["title"],
                "desc":               evt.get("desc"),
                "url":                evt.get("url"),
                "citation":           evt.get("citation"),
                "start_value":        evt.get("start_value"),
                "start_display":      evt.get("start_display"),
                "start_unit":         evt.get("start_unit"),
                "start_month":        int(evt.get("start_month") or 0),
                "start_day":          int(evt.get("start_day") or 0),
                "end_value":          evt.get("end_value"),
                "end_display":        evt.get("end_display"),
                "end_unit":           evt.get("end_unit"),
                "end_month":          int(evt.get("end_month") or 0),
                "end_day":            int(evt.get("end_day") or 0),
                "sort_order":         evt.get("sort_order"),
                "standalone":         bool(evt.get("standalone")),
                "hidden":             bool(evt.get("hidden")),
                "picture_position":   evt.get("picture_position") or "",
                "image_name":         evt.get("image_name"),
                "linked_category_id": cat_id_map.get(evt.get("linked_categoryid")),
                # linked_timeline_id requires the linked timeline to have been
                # published first; left null and can be wired up in a later pass
                "linked_timeline_id": None,
            }).execute()
            new_evt_id = evt_row.data[0]["id"]

            if evt.get("image"):
                img_name     = evt.get("image_name") or "image.png"
                storage_path = f"events/{evt['id']}/{img_name}"
                img_url = _upload_image(c.storage, storage_path,
                                        evt["image"], img_name)
                if img_url:
                    c.table("event").update(
                        {"image_url": img_url}
                    ).eq("id", new_evt_id).execute()

        # ── step 4: insert timeline breaks ────────────────────────────────────
        if breaks:
            _status("Publishing timeline breaks…")
        for b in breaks:
            c.table("timeline_break").insert({
                "timeline_id": new_tl_id,
                "break_start": b["start"],
                "break_end":   b["end"],
            }).execute()

        # ── step 5: upload background image and patch timeline row ────────────
        if bg_image:
            _status("Uploading background image…")
            bg_name      = bg_image_name or "bg_image.png"
            storage_path = f"timelines/{new_tl_id}/{bg_name}"
            bg_url = _upload_image(c.storage, storage_path, bg_image, bg_name)
            c.table("timeline").update(
                {"bg_image_url": bg_url}
            ).eq("id", new_tl_id).execute()

        return f"{PLATFORM_URL}/timelines/{new_tl_id}"


# ── dialog ────────────────────────────────────────────────────────────────────

class PublishDialog:
    """
    Modal dialog that collects credentials + metadata then publishes
    structured timeline data to TimelineHub.

    Parameters
    ----------
    parent          : tk widget (owner window)
    timeline_title  : pre-filled title string
    db              : TimelineDB instance
    """

    def __init__(self, parent, timeline_title: str, db):
        self._parent         = parent
        self._timeline_title = timeline_title
        self._db             = db
        self._publisher      = TimelineHubPublisher()
        self._build()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        win = tk.Toplevel(self._parent)
        win.title("Publish to TimelineHub")
        win.resizable(False, False)
        win.grab_set()
        self._win = win

        pad = {"padx": 10, "pady": 4}

        # ── sign-in section ──────────────────────────────────────────────────
        sign_frame = ttk.LabelFrame(win, text="TimelineHub Account", padding=8)
        sign_frame.pack(fill=tk.X, padx=12, pady=(12, 4))

        ttk.Label(sign_frame, text="Email:").grid(row=0, column=0, sticky=tk.E, **pad)
        self._email_var = tk.StringVar(value=_load_saved_email())
        ttk.Entry(sign_frame, textvariable=self._email_var, width=32).grid(
            row=0, column=1, sticky=tk.W, **pad)

        ttk.Label(sign_frame, text="Password:").grid(row=1, column=0, sticky=tk.E, **pad)
        self._pw_var = tk.StringVar()
        ttk.Entry(sign_frame, textvariable=self._pw_var, show="•", width=32).grid(
            row=1, column=1, sticky=tk.W, **pad)

        self._remember_var = tk.BooleanVar(value=bool(_load_saved_email()))
        ttk.Checkbutton(sign_frame, text="Remember email",
                        variable=self._remember_var).grid(
            row=2, column=1, sticky=tk.W, padx=10)

        # ── metadata section ─────────────────────────────────────────────────
        meta_frame = ttk.LabelFrame(win, text="Timeline Details", padding=8)
        meta_frame.pack(fill=tk.X, padx=12, pady=4)

        ttk.Label(meta_frame, text="Title:").grid(row=0, column=0, sticky=tk.E, **pad)
        self._title_var = tk.StringVar(value=self._timeline_title)
        ttk.Entry(meta_frame, textvariable=self._title_var, width=32).grid(
            row=0, column=1, sticky=tk.W, **pad)

        ttk.Label(meta_frame, text="Description:").grid(row=1, column=0, sticky=tk.E, **pad)
        self._desc_var = tk.StringVar()
        ttk.Entry(meta_frame, textvariable=self._desc_var, width=32).grid(
            row=1, column=1, sticky=tk.W, **pad)

        ttk.Label(meta_frame, text="Category:").grid(row=2, column=0, sticky=tk.E, **pad)
        self._cat_var = tk.StringVar(value=CATEGORIES[0])
        ttk.Combobox(meta_frame, textvariable=self._cat_var,
                     values=CATEGORIES, state="readonly", width=20).grid(
            row=2, column=1, sticky=tk.W, **pad)

        # ── status / progress ────────────────────────────────────────────────
        self._status_var = tk.StringVar()
        ttk.Label(win, textvariable=self._status_var,
                  foreground="#555", font=("Arial", 8)).pack(
            padx=12, pady=(4, 0), anchor=tk.W)

        self._progress = ttk.Progressbar(win, mode="indeterminate", length=340)
        self._progress.pack(padx=12, pady=(2, 6), fill=tk.X)

        # ── buttons ──────────────────────────────────────────────────────────
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        self._publish_btn = ttk.Button(btn_frame, text="Publish",
                                       command=self._on_publish)
        self._publish_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(btn_frame, text="Cancel",
                   command=win.destroy).pack(side=tk.RIGHT)

        win.update_idletasks()
        px = self._parent.winfo_rootx() + self._parent.winfo_width()  // 2
        py = self._parent.winfo_rooty() + self._parent.winfo_height() // 2
        w, h = win.winfo_width(), win.winfo_height()
        win.geometry(f"+{px - w // 2}+{py - h // 2}")

    # ── publish flow ──────────────────────────────────────────────────────────

    def _set_busy(self, busy: bool):
        self._publish_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
        if busy:
            self._progress.start(12)
        else:
            self._progress.stop()
            self._progress["value"] = 0

    def _on_publish(self):
        email    = self._email_var.get().strip()
        password = self._pw_var.get()
        title    = self._title_var.get().strip()
        desc     = self._desc_var.get().strip()
        category = self._cat_var.get()

        if not email or not password:
            messagebox.showwarning("Missing credentials",
                                   "Please enter your TimelineHub email and password.",
                                   parent=self._win)
            return
        if not title:
            messagebox.showwarning("Missing title",
                                   "Please enter a title for the timeline.",
                                   parent=self._win)
            return

        if self._remember_var.get():
            _save_email(email)
        else:
            _save_email("")

        self._set_busy(True)
        threading.Thread(target=self._run_publish,
                         args=(email, password, title, desc, category),
                         daemon=True).start()

    def _run_publish(self, email, password, title, desc, category):
        try:
            self._set_status("Signing in…")
            self._publisher.sign_in(email, password)

            live_url = self._publisher.publish(
                self._db, title, desc, category,
                status_cb=self._set_status,
            )

            self._win.after(0, self._on_success, live_url)

        except Exception as exc:
            self._win.after(0, self._on_error, exc)

    def _set_status(self, msg: str):
        self._win.after(0, lambda: self._status_var.set(msg))

    def _on_success(self, live_url: str):
        self._set_busy(False)
        self._status_var.set("")
        self._win.destroy()
        _SuccessDialog(self._parent, live_url)

    def _on_error(self, exc: Exception):
        self._set_busy(False)
        self._status_var.set("")
        msg = str(exc)
        if "invalid" in msg.lower() or "credentials" in msg.lower() or "401" in msg:
            msg = "Invalid email or password. Please try again."
        messagebox.showerror("Publish Failed", msg, parent=self._win)


# ── success dialog ────────────────────────────────────────────────────────────

class _SuccessDialog:
    """Small dialog showing the live URL with an 'Open in browser' button."""

    def __init__(self, parent, url: str):
        import webbrowser
        win = tk.Toplevel(parent)
        win.title("Published!")
        win.resizable(False, False)
        win.grab_set()

        ttk.Label(win, text="Your timeline is live at:", font=("Arial", 10)).pack(
            padx=16, pady=(14, 4))

        url_var   = tk.StringVar(value=url)
        url_entry = ttk.Entry(win, textvariable=url_var, width=54, state="readonly")
        url_entry.pack(padx=16, pady=4)
        url_entry.bind("<Button-1>", lambda _: (url_entry.config(state="normal"),
                                                 url_entry.select_range(0, "end"),
                                                 url_entry.config(state="readonly")))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(padx=16, pady=(6, 14))
        ttk.Button(btn_frame, text="Open in Browser",
                   command=lambda: webbrowser.open(url)).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frame, text="Close",
                   command=win.destroy).pack(side=tk.LEFT)

        win.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = win.winfo_width(), win.winfo_height()
        win.geometry(f"+{px - w // 2}+{py - h // 2}")


# ── package check ─────────────────────────────────────────────────────────────

def check_supabase_installed() -> bool:
    try:
        import supabase  # noqa: F401
        return True
    except ImportError:
        return False
