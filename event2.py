title = input("Event Title: ")
year = int(input("Year: "))
desc = input("Short Description: ")

if year < 1000:
    era = "ancient"
else:
    era = "modern"

print(f"\n{year} - {title} - ({era})")
print(f"{desc}\n\n")