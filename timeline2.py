events = []
print("--- Timeline Builder ---")
print("Type 'done' as the title to finish.\n")

while True:
    title = input("\n\nEvent title: ")
    if title == "done":
        break
    year = int(input("Year: "))
    desc = input("Description: ")
    event = {"title": title, "year": year, "desc": desc}
    events.append(event)

print("\n--- Your Timeline ---")
for e in events:
    print(f"{e['year']} — {e['title']}: {e['desc']}")