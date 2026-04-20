"""
Publish to TimelineHub — dialog and publisher for the HistoryTimeline desktop app.

Requires:  pip install supabase
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import tempfile
import os
import json

SUPABASE_URL    = "https://tbpjthbywlgbxokfhhji.supabase.co"
SUPABASE_KEY    = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                   ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRicGp0aGJ5d2xnYnhva2ZoaGppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2Mzc2NDUsImV4cCI6MjA5MjIxMzY0NX0"
                   ".GGsTxHqnuCtmCWyTZB0aDKhHiqbTR9ooiqzQY-DjZYo")
PLATFORM_URL    = "https://project-549x3.vercel.app"
CATEGORIES      = ["History", "Science", "Biography", "Technology", "Geography", "Politics"]
_CREDS_FILE     = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".timelinehub_creds.json")


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


class TimelineHubPublisher:
    """Handles auth and publishing to TimelineHub via Supabase."""

    def __init__(self):
        self._client = None
        self._user_id = None

    def sign_in(self, email: str, password: str):
        from supabase import create_client
        self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
        resp = self._client.auth.sign_in_with_password({"email": email, "password": password})
        self._user_id = resp.user.id

    def publish(self, pdf_path: str, title: str, description: str, category: str) -> str:
        """Upload PDF and insert/update timelines row. Returns the live page URL."""
        c = self._client
        uid = self._user_id

        # Insert row (pdf_url placeholder)
        row = c.table("timelines").insert({
            "user_id":     uid,
            "title":       title,
            "description": description,
            "category":    category,
            "pdf_url":     "",
        }).execute()
        timeline_id = row.data[0]["id"]

        # Upload PDF to Storage
        storage_path = f"{uid}/{timeline_id}.pdf"
        with open(pdf_path, "rb") as fh:
            pdf_bytes = fh.read()
        c.storage.from_("timelines").upload(
            storage_path,
            pdf_bytes,
            {"content-type": "application/pdf"},
        )

        # Get public URL and patch the row
        public_url = c.storage.from_("timelines").get_public_url(storage_path)
        c.table("timelines").update({"pdf_url": public_url}).eq("id", timeline_id).execute()

        return f"{PLATFORM_URL}/timelines/{timeline_id}"


class PublishDialog:
    """
    Modal dialog that collects credentials + metadata, generates the PDF,
    and publishes it to TimelineHub.

    Parameters
    ----------
    parent           : tk widget (owner window)
    timeline_title   : pre-filled title string
    generate_pdf_fn  : callable(path: str) -> None
                       Called with a file path where the PDF should be written.
                       Must block until the PDF is fully written.
    """

    def __init__(self, parent, timeline_title: str, generate_pdf_fn):
        self._parent          = parent
        self._timeline_title  = timeline_title
        self._generate_pdf_fn = generate_pdf_fn
        self._publisher       = TimelineHubPublisher()
        self._build()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build(self):
        win = tk.Toplevel(self._parent)
        win.title("Publish to TimelineHub")
        win.resizable(False, False)
        win.grab_set()
        self._win = win

        pad = {"padx": 10, "pady": 4}

        # ── Sign-in section ──────────────────────────────────────────────────
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

        # ── Metadata section ─────────────────────────────────────────────────
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

        # ── Status / progress ────────────────────────────────────────────────
        self._status_var = tk.StringVar()
        self._status_lbl = ttk.Label(win, textvariable=self._status_var,
                                     foreground="#555", font=("Arial", 8))
        self._status_lbl.pack(padx=12, pady=(4, 0), anchor=tk.W)

        self._progress = ttk.Progressbar(win, mode="indeterminate", length=340)
        self._progress.pack(padx=12, pady=(2, 6), fill=tk.X)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        self._publish_btn = ttk.Button(btn_frame, text="Publish",
                                       command=self._on_publish)
        self._publish_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(btn_frame, text="Cancel",
                   command=win.destroy).pack(side=tk.RIGHT)

        win.update_idletasks()
        # Centre over parent
        px = self._parent.winfo_rootx() + self._parent.winfo_width()  // 2
        py = self._parent.winfo_rooty() + self._parent.winfo_height() // 2
        w, h = win.winfo_width(), win.winfo_height()
        win.geometry(f"+{px - w // 2}+{py - h // 2}")

    # ── Publish flow ──────────────────────────────────────────────────────────

    def _set_busy(self, busy: bool):
        state = tk.DISABLED if busy else tk.NORMAL
        self._publish_btn.config(state=state)
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
        tmp_path = None
        try:
            # Step 1: sign in
            self._status_var.set("Signing in…")
            self._publisher.sign_in(email, password)

            # Step 2: generate PDF to a temp file
            self._status_var.set("Generating PDF…")
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
            os.close(tmp_fd)
            # generate_pdf_fn must run on the main thread (Tkinter / ImageGrab)
            done_event = threading.Event()
            error_box  = [None]

            def _gen():
                try:
                    self._generate_pdf_fn(tmp_path)
                except Exception as exc:
                    error_box[0] = exc
                finally:
                    done_event.set()

            self._win.after(0, _gen)
            done_event.wait()
            if error_box[0]:
                raise error_box[0]

            # Step 3: upload
            self._status_var.set("Uploading to TimelineHub…")
            live_url = self._publisher.publish(tmp_path, title, desc, category)

            # Step 4: done
            self._win.after(0, self._on_success, live_url)

        except Exception as exc:
            self._win.after(0, self._on_error, exc)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _on_success(self, live_url: str):
        self._set_busy(False)
        self._status_var.set("")
        self._win.destroy()
        _SuccessDialog(self._parent, live_url)

    def _on_error(self, exc: Exception):
        self._set_busy(False)
        self._status_var.set("")
        msg = str(exc)
        # Surface a friendly message for common auth failures
        if "invalid" in msg.lower() or "credentials" in msg.lower() or "401" in msg:
            msg = "Invalid email or password. Please try again."
        messagebox.showerror("Publish Failed", msg, parent=self._win)


class _SuccessDialog:
    """Small dialog showing the live URL with a 'Open in browser' button."""

    def __init__(self, parent, url: str):
        import webbrowser
        win = tk.Toplevel(parent)
        win.title("Published!")
        win.resizable(False, False)
        win.grab_set()

        ttk.Label(win, text="Your timeline is live at:", font=("Arial", 10)).pack(
            padx=16, pady=(14, 4))

        url_var = tk.StringVar(value=url)
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


def check_supabase_installed() -> bool:
    """Return True if the supabase package is importable."""
    try:
        import supabase  # noqa: F401
        return True
    except ImportError:
        return False
