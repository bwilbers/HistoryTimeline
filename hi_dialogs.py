import tkinter as tk
import random
import time
import threading


def show_hi_dialog(root, screen_width, screen_height):
    win = tk.Toplevel(root)
    win.overrideredirect(True)  # no title bar

    text = random.choice(["hi", "hello"])
    label = tk.Label(win, text=text, font=("Arial", 36, "bold"), padx=20, pady=10)
    label.pack()

    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()

    x = random.randint(0, max(0, screen_width - w))
    y = random.randint(0, max(0, screen_height - h))
    win.geometry(f"+{x}+{y}")

    win.after(10000, win.destroy)


def show_big_hi(root, screen_width, screen_height):
    win = tk.Toplevel(root)
    win.overrideredirect(True)

    label = tk.Label(win, text="HI", font=("Arial", 1000, "bold"), padx=60, pady=40)
    label.pack()

    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()

    x = (screen_width - w) // 2
    y = (screen_height - h) // 2
    win.geometry(f"+{x}+{y}")

    win.after(5000, win.destroy)
    win.after(5100, root.destroy)


def launch_dialogs():
    root = tk.Tk()
    root.withdraw()  # hide main window

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    count = 300  # how many dialogs to spawn

    for i in range(count):
        root.after(i * 1, lambda: show_hi_dialog(root, screen_width, screen_height))

    # after small dialogs close, show the big one
    root.after(count * 1 + 10500, lambda: show_big_hi(root, screen_width, screen_height))
    root.mainloop()


if __name__ == "__main__":
    launch_dialogs()
