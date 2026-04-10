events = [
(476, "Fall of Rome", "Western Roman Empire ends"),
(1066, "Battle of Hastings", "Normans conquer England"),
(1776, "US Independence", "Declaration signed"),
(1969, "Moon landing", "Apollo 11 lands on Moon"),
]

print("--- My Timeline ---")
for event in events:
    year, title, desc = event
    print(f"{year} — {title}: {desc}")
