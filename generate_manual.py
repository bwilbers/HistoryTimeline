"""
Generate the Historical Timeline Builder user manual as a PDF.
Run:  python generate_manual.py
Output: HistoryTimeline_UserManual.pdf (same folder)
"""

from fpdf import FPDF
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "HistoryTimeline_UserManual.pdf")

# ── colour palette ────────────────────────────────────────────────────────────
BLUE_DARK  = (44,  62,  80)   # #2c3e50
BLUE_MID   = (74, 111, 165)   # #4a6fa5
BLUE_LIGHT = (224, 235, 247)  # light header fill
GOLD       = (240, 192,  64)   # #f0c040
GREY_TEXT  = (60,  60,  60)
WHITE      = (255, 255, 255)
CREAM      = (245, 242, 238)  # canvas bg

# ── FPDF subclass with custom helpers ────────────────────────────────────────

class Manual(FPDF):

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*BLUE_DARK)
        self.rect(0, 0, 210, 12, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(10, 2)
        self.cell(0, 8, "Historical Timeline Builder - User Manual", align="L")
        self.set_xy(-40, 2)
        self.cell(30, 8, f"Page {self.page_no()}", align="R")
        self.set_text_color(*GREY_TEXT)
        self.ln(10)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, "Historical Timeline Builder", align="C")

    # ── helpers ───────────────────────────────────────────────────────────────

    def cover_page(self):
        self.add_page()
        # Dark background band
        self.set_fill_color(*BLUE_DARK)
        self.rect(0, 0, 210, 297, "F")

        # Gold accent bar
        self.set_fill_color(*GOLD)
        self.rect(0, 85, 210, 6, "F")

        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 36)
        self.set_xy(0, 50)
        self.cell(210, 20, "Historical Timeline", align="C")
        self.set_font("Helvetica", "B", 28)
        self.set_xy(0, 74)
        self.cell(210, 12, "Builder", align="C")

        self.set_font("Helvetica", "", 14)
        self.set_xy(0, 100)
        self.cell(210, 10, "User Manual", align="C")

        self.set_font("Helvetica", "", 10)
        self.set_text_color(180, 200, 220)
        self.set_xy(0, 120)
        self.multi_cell(210, 6,
            "A desktop application for creating, editing, and visualising\n"
            "historical timelines across any time scale.",
            align="C")

        self.set_text_color(*GOLD)
        self.set_font("Helvetica", "B", 9)
        self.set_xy(0, 265)
        self.cell(210, 8, "Version 1.0", align="C")

    def toc_entry(self, num, title, page):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*GREY_TEXT)
        dots = "." * max(2, 65 - len(f"{num}  {title}"))
        self.cell(0, 7, f"  {num}  {title}  {dots}  {page}", ln=True)

    def chapter_title(self, num, title):
        self.set_fill_color(*BLUE_DARK)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, f"  {num}.  {title}", fill=True, ln=True)
        self.ln(3)
        self.set_text_color(*GREY_TEXT)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*BLUE_MID)
        self.cell(0, 8, title, ln=True)
        self.set_draw_color(*BLUE_MID)
        self.set_line_width(0.4)
        x = self.get_x()
        y = self.get_y()
        self.line(x, y, x + 190, y)
        self.ln(3)
        self.set_text_color(*GREY_TEXT)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GREY_TEXT)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, items, indent=8):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GREY_TEXT)
        for item in items:
            self.set_x(self.l_margin + indent)
            self.multi_cell(0, 6, f"*  {item}")
        self.ln(2)

    def note(self, text):
        """Highlighted tip/note box."""
        self.set_fill_color(*BLUE_LIGHT)
        self.set_draw_color(*BLUE_MID)
        self.set_line_width(0.3)
        x = self.get_x()
        y = self.get_y()
        # Measure height needed
        self.set_font("Helvetica", "I", 9)
        lines = self.multi_cell(0, 5, text, dry_run=True, output="LINES")
        h = len(lines) * 5 + 6
        self.rect(x, y, 190, h, "DF")
        self.set_xy(x + 4, y + 3)
        self.multi_cell(182, 5, text)
        self.ln(4)
        self.set_text_color(*GREY_TEXT)

    def field_row(self, field, description):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*BLUE_DARK)
        self.cell(45, 6, field, ln=False)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GREY_TEXT)
        self.multi_cell(0, 6, description)

    def page_break_if_needed(self, space=30):
        if self.get_y() > 265 - space:
            self.add_page()


# ── build document ────────────────────────────────────────────────────────────

pdf = Manual()
pdf.set_auto_page_break(auto=True, margin=18)
pdf.set_margins(15, 20, 15)

# ── Cover ─────────────────────────────────────────────────────────────────────
pdf.cover_page()

# ── Table of Contents ─────────────────────────────────────────────────────────
pdf.add_page()
pdf.set_font("Helvetica", "B", 16)
pdf.set_text_color(*BLUE_DARK)
pdf.cell(0, 12, "Table of Contents", ln=True)
pdf.set_draw_color(*BLUE_DARK)
pdf.set_line_width(0.6)
pdf.line(15, pdf.get_y(), 195, pdf.get_y())
pdf.ln(5)

toc = [
    ("1", "Overview",                       3),
    ("2", "Getting Started",                3),
    ("3", "Main Editor Window",             4),
    ("4", "Event Fields Reference",         5),
    ("5", "Managing Timelines",             7),
    ("6", "Managing Categories",            8),
    ("7", "The Timeline View",              9),
    ("8", "Navigation Panel",              11),
    ("9", "Toolbar Controls",              12),
    ("10","Working with Images",           13),
    ("11","Tooltips",                      14),
    ("12","Import and Export",             15),
    ("13","Saving the Timeline as a PDF",  16),
    ("14","Keyboard and Mouse Shortcuts",  17),
    ("15","Tips and Best Practices",       17),
]
for num, title, pg in toc:
    pdf.toc_entry(num, title, pg)

# ── Chapter 1: Overview ───────────────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("1", "Overview")
pdf.body(
    "Historical Timeline Builder is a desktop application for creating rich, interactive "
    "timelines that can span any period of history -- from billions of years ago to the "
    "present day. Events are organised into colour-coded categories, can carry images and "
    "hyperlinks, and are displayed on a zoomable, scrollable canvas."
)
pdf.body(
    "All data is stored locally in a SQLite database file (timeline.db). Multiple "
    "independent timelines can coexist in the same file and are switched between instantly."
)

pdf.section_title("Key Features")
pdf.bullet([
    "Multiple timelines in one file -- switch without restarting the app.",
    "Flexible date entry: CE, BCE, MYA (millions of years ago), BYA (billions of years ago), "
    "or 'Present' (auto-updates to today).",
    "Month and day precision for CE/BCE dates.",
    "Hierarchical categories with colour coding and show/hide control.",
    "Per-event images displayed Left, Center, Right of the event bar, or replacing it entirely.",
    "Overlapping event title staggering with leader lines for readability.",
    "Optional date-line guide marks from event dates to the top of the canvas.",
    "Full-canvas PDF export including the category label column.",
    "Excel (.xlsx) import and export for bulk editing outside the app.",
    "Drag-to-reorder events within the navigation panel.",
])

# ── Chapter 2: Getting Started ────────────────────────────────────────────────
pdf.chapter_title("2", "Getting Started")
pdf.section_title("Starting the Application")
pdf.body(
    "Run the application by executing timeline_db.py with Python 3.10 or later. "
    "Required packages: tkinter (bundled with Python), Pillow, and openpyxl. "
    "Install them with:"
)
pdf.set_font("Courier", "", 9)
pdf.set_fill_color(235, 235, 235)
pdf.set_text_color(40, 40, 40)
pdf.cell(0, 7, "   pip install Pillow openpyxl", fill=True, ln=True)
pdf.ln(3)
pdf.set_text_color(*GREY_TEXT)

pdf.body(
    "On first launch a 'Practice Timeline' is created automatically with seven starter "
    "categories (War, Science, Politics, Exploration, Culture, Religion, General). "
    "If a timeline.json file exists in the same folder its events are migrated once into "
    "the database."
)

pdf.section_title("Startup Selector")
pdf.body(
    "Each time the application starts, a small dialog asks which timeline to open. "
    "Use the dropdown to choose an existing timeline or click New Timeline to create one. "
    "The application remembers the last-used timeline and pre-selects it automatically."
)

# ── Chapter 3: Main Editor Window ─────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("3", "Main Editor Window")
pdf.body(
    "The main window is divided into three areas:"
)
pdf.bullet([
    "Top bar -- shows the active timeline name and a dropdown to switch timelines. "
    "An Edit button opens the Manage Timelines dialog.",
    "Event panel (left) -- form for creating and editing a single event.",
    "Event list panel (right) -- table listing all events with search, filter, and sort controls.",
])
pdf.body(
    "A status bar at the bottom shows the currently selected event and any action messages."
)

pdf.section_title("Switching Timelines from the Main Window")
pdf.body(
    "The dropdown in the top bar lists all timelines in the database. Selecting a different "
    "name immediately loads that timeline into the event form and list. The Edit button "
    "opens the full Manage Timelines dialog where you can create, rename, delete, import, "
    "and export timelines."
)

pdf.section_title("Event List Controls")
pdf.bullet([
    "Search -- type any text to filter events by title, description, URL, or category in real time.",
    "Filter -- narrow the list to a single category.",
    "Sort by -- order events by date, title, category, or custom (user-defined drag order).",
    "Click a row to load the event into the editor panel for editing.",
    "Up / Down buttons (if visible) reorder the selected event within its category.",
])

pdf.section_title("Saving Changes")
pdf.body(
    "Click Save in the Event panel to write the current form contents to the database. "
    "The list refreshes automatically. Use New to clear the form ready for a new event, "
    "and Delete to permanently remove the selected event after confirmation."
)

# ── Chapter 4: Event Fields Reference ─────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("4", "Event Fields Reference")
pdf.body("Each event has the following fields:")
pdf.ln(2)

fields = [
    ("ID",             "Auto-assigned database identifier. Read-only."),
    ("Title",          "Short label displayed on the timeline bar or beside the event marker. "
                       "Required."),
    ("Start",          "The event's start date. Enter a number in the Year box, then choose a "
                       "unit from the dropdown: CE, BCE, MYA, BYA, or Present. For CE/BCE dates "
                       "you may optionally select a Month and Day for extra precision."),
    ("End",            "Optional end date for span events. Leave blank for a point event (shown "
                       "as a diamond). Same controls as Start. If End equals Start the event is "
                       "treated as a point."),
    ("Description",    "Free-form multi-line text describing the event. Shown in full in the "
                       "hover tooltip on the timeline canvas."),
    ("URL",            "Optional hyperlink. A Test button opens the URL in your default browser "
                       "to verify it; Search opens Wikipedia in a browser. The link is "
                       "accessible from the tooltip on the canvas."),
    ("Category",       "Which category group the event belongs to. Type or choose from the "
                       "dropdown. The Edit button next to the dropdown opens the Manage "
                       "Categories dialog without leaving the event form."),
    ("Own row",        "When checked the event is always placed on its own horizontal row "
                       "in the timeline and is never packed alongside other events, even if "
                       "their date ranges do not overlap."),
    ("Image",          "An optional image stored inside the database. Use Browse to pick any "
                       "PNG, JPG, or similar file. The image is thumbnail-scaled to 200x200 px "
                       "on import. Clear removes the stored image. A preview is shown in the "
                       "form."),
    ("Show on Timeline","Controls where the image is displayed on the timeline canvas:\n"
                       "  * (blank) -- image stored but not shown on canvas.\n"
                       "  * Left of Event -- image to the left of the event bar.\n"
                       "  * Center of Event -- image centred above the event bar.\n"
                       "  * Right of Event -- image to the right of the event bar.\n"
                       "  * Replace Event -- bar is hidden; image is centred where the "
                       "bar would be."),
]
for f, d in fields:
    pdf.field_row(f, d)
    pdf.ln(1)

pdf.page_break_if_needed(40)
pdf.section_title("Date Units Explained")
rows = [
    ("CE",      "Common Era (AD). Year 1 to present. Month and Day selectors are available."),
    ("BCE",     "Before Common Era (BC). Enter the number of years before year 1. "
                "Month and Day selectors are available."),
    ("MYA",     "Millions of years ago. Enter a decimal number (e.g. 65.5 for 65.5 MYA). "
                "Month and Day selectors are hidden."),
    ("BYA",     "Billions of years ago. Enter a decimal number (e.g. 4.6 for 4.6 BYA). "
                "Month and Day selectors are hidden."),
    ("Present", "Automatically resolves to today's date each time the timeline is loaded. "
                "Useful for ongoing events. The number box is hidden when Present is selected."),
]
for unit, desc in rows:
    pdf.field_row(unit, desc)
    pdf.ln(1)

pdf.note(
    "Tip: to represent the entire known universe use a Start of 13.8 BYA and an End of Present. "
    "The timeline will automatically scale to show the full span."
)

# ── Chapter 5: Managing Timelines ─────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("5", "Managing Timelines")
pdf.body(
    "The Manage Timelines dialog is opened with the Edit button in the main window toolbar "
    "or via the Manage Timelines button in the Timeline View navigation panel."
)

pdf.section_title("Creating a Timeline")
pdf.bullet([
    "Click New to clear the name field.",
    "Type a name and click Save.",
    "The new timeline becomes active immediately.",
])

pdf.section_title("Renaming a Timeline")
pdf.bullet([
    "Select the timeline in the list.",
    "Edit the Name field.",
    "Click Save.",
])

pdf.section_title("Deleting a Timeline")
pdf.bullet([
    "Select the timeline in the list.",
    "Click Delete.",
    "Confirm the prompt -- this permanently deletes all events and categories in that timeline.",
    "The Delete button is disabled when only one timeline exists (cannot delete the last one).",
])

pdf.section_title("Import and Export")
pdf.body(
    "Each timeline can be exported to an Excel workbook (.xlsx) for backup or bulk editing, "
    "and imported back. See Chapter 12 for the full column specification."
)

# ── Chapter 6: Managing Categories ────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("6", "Managing Categories")
pdf.body(
    "Categories organise events into groups on the timeline. Each category is assigned a "
    "colour automatically, which is also used for the event bars and markers. Categories "
    "support a parent-child hierarchy of any depth."
)
pdf.body(
    "Open the dialog with the Manage Categories button in the Timeline View navigation "
    "panel, or the Edit button next to the Category field in the event form."
)

pdf.section_title("Adding a Category")
pdf.bullet([
    "Click New to clear the form.",
    "Type a name.",
    "Optionally select a Parent category to create a sub-category.",
    "Click Save.",
])

pdf.section_title("Renaming and Deleting")
pdf.bullet([
    "Select the category in the tree, edit the name, and click Save to rename.",
    "Click Delete to remove it. Its direct child categories and events are re-parented "
    "one level up (or to root if it was a root category).",
])

pdf.section_title("Reordering")
pdf.bullet([
    "Use the Up and Down buttons to move the selected category among its siblings.",
    "This order is reflected in the navigation panel and on the canvas.",
])

pdf.section_title("Hiding a Category")
pdf.body(
    "Checking Hidden on a category removes it from the timeline canvas but keeps all its "
    "events in the database. Hidden categories are shown in red with a [hidden] symbol in the "
    "navigation panel so they are easy to identify and restore."
)

pdf.note(
    "Individual events can also be hidden using the Hidden checkbox in the Edit Event dialog "
    "(accessible by right-clicking an event in the navigation panel or canvas)."
)

# ── Chapter 7: The Timeline View ──────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("7", "The Timeline View")
pdf.body(
    "Click the Timeline View button at the bottom of the main window to open the visual "
    "canvas. The window opens maximised and remains open while you continue to use the "
    "main editor. Changes saved in the editor are reflected in the canvas immediately "
    "after a reload."
)

pdf.section_title("Canvas Layout")
pdf.body(
    "The canvas has three zones:"
)
pdf.bullet([
    "Dark ruler at the top -- shows date tick marks. Scrolls horizontally in sync with the "
    "event area. Click-and-drag on the ruler to pan the view left or right.",
    "Category label column (left, fixed) -- shows the name of each category group. "
    "The column does not scroll horizontally but moves vertically with the main canvas.",
    "Event area (main) -- coloured bars and diamond markers representing events. "
    "Scrolls both horizontally and vertically.",
])

pdf.section_title("Event Shapes")
pdf.bullet([
    "Rectangle bar -- a span event with a distinct start and end date. The bar width "
    "is proportional to its duration.",
    "Diamond marker -- a point event (no end date, or start equals end). The diamond "
    "is centred on the start date.",
    "When a picture position of Left of Event or Right of Event is selected, the bar "
    "or diamond spans the full row height so the event and image are vertically centred together.",
])

pdf.section_title("Rows and Lane Packing")
pdf.body(
    "Events in the same category are packed greedily into horizontal lanes. Non-overlapping "
    "events share a lane to save vertical space; overlapping events are placed on separate "
    "lanes. Events with Own Row checked always occupy a private lane regardless of overlap."
)

pdf.section_title("Overlapping Titles")
pdf.body(
    "When event titles within the same lane would overlap, the row height is automatically "
    "increased and the titles are staggered vertically. A short horizontal underline and a "
    "vertical connector line link each title back to its event, drawn in the event's colour."
)

pdf.section_title("Collapsed Categories")
pdf.body(
    "A category can be collapsed in the navigation panel by clicking the triangle next to "
    "its name. The canvas replaces all lanes for that category with a single summary lane "
    "showing how many events are grouped inside. Expand All and Collapse All buttons act "
    "on every category at once."
)

# ── Chapter 8: Navigation Panel ───────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("8", "Navigation Panel")
pdf.body(
    "The dark panel on the left side of the Timeline View lists every category and event "
    "in the active timeline. It mirrors the sort order used on the canvas."
)

pdf.section_title("Selecting an Item")
pdf.body(
    "Click any event row in the navigation tree to highlight that event's lane on the "
    "canvas with a gold outline, making it easy to locate even when the canvas is zoomed out."
)

pdf.section_title("Expanding and Collapsing")
pdf.bullet([
    "Click the triangle (arrow) beside a category name to expand or collapse it.",
    "Collapsing a category on the nav panel collapses the corresponding rows on the canvas.",
    "Expand All and Collapse All buttons act on the entire tree at once.",
])

pdf.section_title("Drag to Reorder")
pdf.body(
    "Events within the same category can be reordered by clicking and dragging them in the "
    "navigation tree. A green indicator line shows where the event will be dropped. "
    "The new order is immediately persisted to the database and the canvas redraws."
)
pdf.note(
    "Drag reorder only works within the same category. "
    "To move an event to a different category, edit the event and change its Category field."
)

pdf.section_title("Right-Click Menu")
pdf.bullet([
    "Right-click an event row to open the Edit Event dialog for that event.",
    "Right-click a category row to open the Manage Categories dialog with that category "
    "pre-selected.",
])

pdf.section_title("Hidden Items")
pdf.body(
    "Hidden categories and events are shown in red with a [hidden] symbol. "
    "They remain listed in the navigation panel so you can find and unhide them, "
    "but they do not appear on the canvas."
)

# ── Chapter 9: Toolbar Controls ───────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("9", "Toolbar Controls")
pdf.body(
    "The toolbar at the top of the Timeline View contains the following controls from "
    "left to right:"
)

toolbar = [
    ("Timeline dropdown",
     "Lists all timelines in the database. Choose a different name to switch timelines "
     "without closing the window. The active timeline name is also shown in large bold "
     "text to the right of the toolbar controls."),
    ("Zoom In",
     "Increases the pixels-per-year scale by 25%, making events wider and more spread out."),
    ("Zoom Out",
     "Decreases the pixels-per-year scale by 25%, fitting more time into the window."),
    ("Fit All",
     "Automatically calculates a zoom level and scroll position that shows every event "
     "with a small margin on each side."),
    ("Date Lines",
     "Checkbox that toggles muted dotted vertical lines drawn from each event's start "
     "(and end) date up to the top of the canvas. Lines are drawn in the event's colour "
     "at reduced opacity. Only visible rows are processed for performance. Off by default."),
    ("Save PDF",
     "Captures the entire timeline canvas (including off-screen portions) and saves it "
     "as a multi-page PDF. See Chapter 13 for details."),
    ("Close",
     "Closes the Timeline View and saves the active timeline ID to the configuration file "
     "so it is remembered on the next launch."),
    ("Manage Timelines",
     "Opens the full timeline management dialog (same as the Edit button in the main window)."),
    ("Manage Categories",
     "Opens the category management dialog for the active timeline."),
    ("Add Event",
     "Opens the Edit Event dialog pre-filled with a blank event."),
]
for ctrl, desc in toolbar:
    pdf.field_row(ctrl, desc)
    pdf.ln(2)

# ── Chapter 10: Working with Images ───────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("10", "Working with Images")

pdf.section_title("Attaching an Image")
pdf.bullet([
    "In the Event form (main window or Edit Event dialog), click Browse next to the Image field.",
    "Select any common image format (PNG, JPG, BMP, GIF, WEBP).",
    "The image is scaled to fit within 200x200 pixels and stored as a BLOB inside the database.",
    "A preview thumbnail appears immediately below the controls.",
    "Click Clear to remove the stored image from the event.",
])

pdf.section_title("Show on Timeline Options")
pdf.body(
    "Use the Show on Timeline dropdown to control how and where the image appears on "
    "the canvas. Leave it blank to store the image without displaying it."
)

positions = [
    ("Left of Event",
     "The image is placed to the left of the event bar, separated by 20 px of padding. "
     "The row height expands to equal the image height plus top and bottom padding. "
     "The event bar and diamond both extend the full row height so the event is "
     "visually centred alongside the image."),
    ("Center of Event",
     "The image is placed horizontally centred above the event bar with 20 px of "
     "vertical padding. The event title is drawn above the image in the normal style."),
    ("Right of Event",
     "Same as Left of Event but the image appears to the right of the bar."),
    ("Replace Event",
     "The event bar is hidden entirely. The image is centred at the event's date position. "
     "The event title is drawn above the image. Useful for photo-style markers."),
]
for pos, desc in positions:
    pdf.field_row(pos, desc)
    pdf.ln(2)

pdf.note(
    "Images are stored at reduced resolution (max 200x200 px) to keep the database "
    "file manageable. For best results use images that are already close to the size you "
    "want displayed on the timeline."
)

pdf.section_title("Image Tooltip")
pdf.body(
    "Hovering over an image on the canvas shows the same tooltip as hovering over the "
    "event bar -- title, date range, description, and a link button. "
    "The image is also shown as a thumbnail inside the tooltip itself."
)

# ── Chapter 11: Tooltips ──────────────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("11", "Tooltips")
pdf.body(
    "Moving the mouse over any event on the canvas (bar, diamond, or image) triggers "
    "a floating tooltip after a short hover delay."
)
pdf.body("The tooltip displays:")
pdf.bullet([
    "Event title (bold).",
    "Date range -- start date only for point events; 'start - end' for spans.",
    "Full description text (no truncation).",
    "An Open Link button if a URL is stored, which launches the URL in the default browser.",
    "A thumbnail of the event image (max 120x120 px) to the left of the text if one is attached.",
])
pdf.body(
    "The tooltip closes automatically when the mouse moves away. Moving the mouse onto "
    "the tooltip itself keeps it open so you can read long descriptions or click the link."
)
pdf.body(
    "The status bar at the bottom of the Timeline View also shows the event title, "
    "date range, and category when the mouse hovers over an event."
)

# ── Chapter 12: Import and Export ─────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("12", "Import and Export")
pdf.body(
    "Use the Import and Export buttons in the Manage Timelines dialog to exchange "
    "data with Excel workbooks (.xlsx)."
)

pdf.section_title("Exporting")
pdf.body(
    "The export creates a workbook with two sheets:"
)
pdf.bullet([
    "Events -- one row per event with columns: Category, Title, Start Date, End Date, "
    "Description, URL, Own Row.",
    "Categories -- one row per category with columns: Category (short name) and "
    "Full Path (the complete parent > child path).",
])
pdf.body(
    "Dates are written in the same human-readable format shown on screen "
    "(e.g. '1066 CE', '03/1815 CE', '07/04/1776 CE', '65.5 MYA', 'Present')."
)

pdf.section_title("Importing")
pdf.body(
    "Importing reads an Excel workbook in the same format and replaces all events and "
    "categories in the active timeline."
)
pdf.note(
    "Warning: importing clears the entire timeline before loading. "
    "Export first if you need a backup."
)
pdf.body("Import rules:")
pdf.bullet([
    "The workbook must have a sheet named 'Events'.",
    "A 'Categories' sheet is optional; if present its Full Path column is used to "
    "create the category hierarchy before events are read.",
    "Category paths use ' > ' as the separator (e.g. 'Science > Physics').",
    "Date formats accepted: '1969 CE', '07/1969 CE', '07/20/1969 CE', '1066 BCE', "
    "'65.5 MYA', '4.6 BYA', 'Present'.",
    "Own Row column: any non-empty, non-zero value is treated as true.",
    "Rows with a blank Title are silently skipped.",
])

pdf.section_title("Excel Column Reference")
headers = ["Column", "Name",        "Notes"]
rows_data = [
    ["A", "Category",    "Short category name or full path ('Parent > Child')."],
    ["B", "Title",       "Event title (required)."],
    ["C", "Start Date",  "Start date string (see formats above)."],
    ["D", "End Date",    "End date string. Leave blank for a point event."],
    ["E", "Description", "Multi-line description text."],
    ["F", "URL",         "Full URL including https://."],
    ["G", "Own Row",     "1 = own row, 0 or blank = pack with neighbours."],
]
pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(*BLUE_MID)
pdf.set_text_color(*WHITE)
for h in headers:
    w = 18 if h == "Column" else (25 if h == "Name" else 147)
    pdf.cell(w, 6, h, border=1, fill=True)
pdf.ln()
pdf.set_font("Helvetica", "", 9)
alt = False
for r in rows_data:
    pdf.set_fill_color(235, 240, 248) if alt else pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(*GREY_TEXT)
    pdf.cell(18, 6, r[0], border=1, fill=True)
    pdf.cell(25, 6, r[1], border=1, fill=True)
    # Description may wrap -- use multi_cell for last column
    x_save = pdf.get_x(); y_save = pdf.get_y()
    pdf.multi_cell(147, 6, r[2], border=1, fill=True)
    alt = not alt
pdf.ln(3)
pdf.set_text_color(*GREY_TEXT)

# ── Chapter 13: Saving as PDF ─────────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("13", "Saving the Timeline as a PDF")
pdf.body(
    "Click Save PDF in the Timeline View toolbar to capture the entire timeline -- "
    "including portions not currently visible on screen -- and save it as a PDF file."
)

pdf.section_title("How It Works")
pdf.body(
    "The application scrolls through the complete canvas in tiles, taking screenshots "
    "of each portion and stitching them into a single large image. The category label "
    "column is captured separately and placed at the left edge. The result is saved as "
    "a single-page PDF at 96 dpi and opened in the default PDF viewer automatically."
)

pdf.section_title("Tips for Best Results")
pdf.bullet([
    "Maximise the Timeline View window before saving -- a larger viewport means fewer "
    "tiles and faster capture.",
    "Use Fit All first to see the entire timeline, then zoom in or out to your preferred "
    "level of detail before saving.",
    "If Date Lines are enabled they are captured in the PDF.",
    "The PDF file name defaults to the active timeline name.",
    "On very long timelines the PDF image will be correspondingly wide. "
    "Most PDF viewers handle large single-page files well.",
])

pdf.note(
    "The Save PDF function uses screen capture (PIL ImageGrab). "
    "Ensure no other windows overlap the Timeline View during the save, "
    "as overlapping windows may appear in the PDF."
)

# ── Chapter 14: Shortcuts ─────────────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("14", "Keyboard and Mouse Shortcuts")

shortcuts = [
    ("Mouse wheel",         "Zoom in/out on the timeline canvas."),
    ("Click + drag (canvas)","Pan the event area horizontally and vertically."),
    ("Click + drag (ruler)", "Pan the timeline horizontally."),
    ("Left-click (event)",   "Opens the Edit Event dialog for that event."),
    ("Right-click (event)",  "Also opens the Edit Event dialog (same as left-click)."),
    ("Right-click (empty row)","Opens the Edit Event dialog pre-filled with the clicked date "
                              "and the owning category."),
    ("Right-click (nav panel -- event)","Opens the Edit Event dialog."),
    ("Right-click (nav panel -- category)","Opens the Manage Categories dialog."),
    ("Drag event (nav panel)","Reorder the event within its category."),
    ("Click category triangle","Expand or collapse a category on both the nav panel and canvas."),
]
for key, desc in shortcuts:
    pdf.field_row(key, desc)
    pdf.ln(2)

# ── Chapter 15: Tips ──────────────────────────────────────────────────────────
pdf.add_page()
pdf.chapter_title("15", "Tips and Best Practices")

pdf.section_title("Organising Long Timelines")
pdf.bullet([
    "Create a clear category hierarchy before adding events -- it is easy to rename and "
    "restructure categories later, but starting with a plan saves time.",
    "Use sub-categories to create visual groupings without cluttering the top level. "
    "For example: Technology > Computing > Artificial Intelligence.",
    "Hide categories you are not currently working on to reduce visual noise on the canvas.",
    "Use the Collapse All button to get a high-level overview, then expand individual "
    "categories to focus on a period.",
])

pdf.section_title("Date Entry Advice")
pdf.bullet([
    "For geological or cosmological timelines use BYA for the earliest events and "
    "switch to MYA, then BCE, then CE as appropriate -- the app handles mixed units on "
    "the same timeline automatically.",
    "Use the Present unit for any event that extends to today. The end date recalculates "
    "each time the file is opened.",
    "Add a month and day for events where exact timing matters (battles, discoveries, "
    "elections). The tooltip will display the full precision date.",
])

pdf.section_title("Images")
pdf.bullet([
    "Keep source images small (under 200 px on each side) before importing to maintain "
    "fast canvas rendering.",
    "Use Replace Event for portrait photos of historical figures -- the image appears "
    "directly on the timeline in place of a bar.",
    "Left of Event / Right of Event works well for diagrams, maps, or illustrations "
    "that are wider than they are tall.",
    "Center of Event is useful for icons or small symbols above the bar.",
])

pdf.section_title("Performance")
pdf.bullet([
    "The Date Lines feature redraws the canvas on every pan/zoom. For very large timelines "
    "turn Date Lines off when not needed.",
    "Hiding categories you are not actively working with reduces canvas rendering time.",
    "The Excel import replaces all events and categories; for partial updates edit "
    "the database directly or use the per-event edit dialogs.",
])

pdf.section_title("Backup and Portability")
pdf.bullet([
    "The entire database is stored in timeline.db in the application folder. "
    "Copy this file to back up all your timelines.",
    "The configuration file (timeline_config.json) stores only the last-opened timeline ID -- "
    "it is safe to delete if you want to reset the startup selection.",
    "Use File > Export from the Manage Timelines dialog to create an Excel backup "
    "before making large structural changes.",
])

# ── save ──────────────────────────────────────────────────────────────────────
pdf.output(OUTPUT)
print(f"Manual written to: {OUTPUT}")
