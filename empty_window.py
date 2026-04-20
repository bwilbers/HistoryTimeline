import tkinter as tk

root = tk.Tk()
root.title("Ball Hoop Game")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda event: root.destroy())

canvas = tk.Canvas(root, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
ball_radius = 20
hoop_radius = 40

# Score tracking
score = 0
high_score = 0

# Create hoop at bottom center
hoop_x = screen_width // 2
hoop_y = screen_height - 100
hoop = canvas.create_oval(
    hoop_x - hoop_radius,
    hoop_y - hoop_radius,
    hoop_x + hoop_radius,
    hoop_y + hoop_radius,
    fill="yellow",
    outline="orange",
    width=3
)

# Create score and high score display
score_text = canvas.create_text(50, 50, font=("Arial", 24), fill="black", anchor="nw")
high_score_text = canvas.create_text(50, 100, font=("Arial", 24), fill="black", anchor="nw")

red_ball = canvas.create_oval(
    screen_width // 2 - ball_radius,
    screen_height // 2 - ball_radius,
    screen_width // 2 + ball_radius,
    screen_height // 2 + ball_radius,
    fill="red",
    outline=""
)
blue_ball = canvas.create_oval(60, 60, 60 + ball_radius * 2, 60 + ball_radius * 2, fill="blue", outline="")

red_start = (screen_width // 2 - ball_radius, screen_height // 2 - ball_radius)
blue_start = (60, 60)

drag_data = {"item": None, "x": 0, "y": 0}


def update_score_display():
    canvas.itemconfig(score_text, text=f"Score: {score}")
    canvas.itemconfig(high_score_text, text=f"High Score: {high_score}")


def is_colliding(item1, item2):
    x1, y1, x2, y2 = canvas.bbox(item1)
    x3, y3, x4, y4 = canvas.bbox(item2)
    return not (x2 <= x3 or x4 <= x1 or y2 <= y3 or y4 <= y1)


def check_hoop(ball):
    global score, high_score
    if is_colliding(ball, hoop):
        score += 1
        if score > high_score:
            high_score = score
        update_score_display()
        # Reset ball to start position
        if ball == red_ball:
            canvas.coords(ball, red_start[0], red_start[1], red_start[0] + ball_radius * 2, red_start[1] + ball_radius * 2)
        else:
            canvas.coords(ball, blue_start[0], blue_start[1], blue_start[0] + ball_radius * 2, blue_start[1] + ball_radius * 2)


def on_press(event):
    item = canvas.find_closest(event.x, event.y)
    if item:
        drag_data["item"] = item[0]
        drag_data["x"] = event.x
        drag_data["y"] = event.y


def on_drag(event):
    item = drag_data["item"]
    if not item:
        return

    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]

    # Attempt move and undo if it would collide
    canvas.move(item, dx, dy)
    other = red_ball if item == blue_ball else blue_ball

    if is_colliding(item, other):
        canvas.move(item, -dx, -dy)
    else:
        drag_data["x"] = event.x
        drag_data["y"] = event.y
        check_hoop(item)


def on_release(event):
    drag_data["item"] = None

canvas.tag_bind(red_ball, "<ButtonPress-1>", on_press)
canvas.tag_bind(red_ball, "<B1-Motion>", on_drag)
canvas.tag_bind(red_ball, "<ButtonRelease-1>", on_release)
canvas.tag_bind(blue_ball, "<ButtonPress-1>", on_press)
canvas.tag_bind(blue_ball, "<B1-Motion>", on_drag)
canvas.tag_bind(blue_ball, "<ButtonRelease-1>", on_release)

update_score_display()

root.mainloop()
