import tkinter as tk
from tkinter import PhotoImage

# Create main application window
root = tk.Tk()
root.title("Entry Terminal")
root.geometry("900x600")
root.state("zoomed")  # Make window start maximized

# Load background image (replace 'background.png' with the actual file)
try:
    bg_image = PhotoImage(file="src/background.png")
    canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bg_image, anchor="nw")
except Exception as e:
    print("Background image not found, using default background.")
    root.configure(bg="black")

# Create frames for Red and Green teams
red_frame = tk.Frame(root, bg="darkred", padx=10, pady=10)
red_frame.place(relx=0.1, rely=0.1)

green_frame = tk.Frame(root, bg="darkgreen", padx=10, pady=10)
green_frame.place(relx=0.6, rely=0.1)

# Create labels for team names
tk.Label(red_frame, text="RED TEAM", bg="darkred", fg="white", font=("Arial", 14, "bold"), width=20).grid(row=0, column=0, columnspan=3)
tk.Label(green_frame, text="GREEN TEAM", bg="darkgreen", fg="white", font=("Arial", 14, "bold"), width=20).grid(row=0, column=0, columnspan=3)

# Create player entry fields for both teams
player_entries = []
for i in range(15):  # 15 Players per team
    tk.Label(red_frame, text=f"{i+1}", font=("Arial", 10), bg="darkred", fg="white").grid(row=i+1, column=0, padx=5, pady=2)
    entry_red_name = tk.Entry(red_frame, width=12)
    entry_red_name.grid(row=i+1, column=1, padx=5, pady=2)
    entry_red_id = tk.Entry(red_frame, width=12)
    entry_red_id.grid(row=i+1, column=2, padx=5, pady=2)
    player_entries.append((entry_red_name, entry_red_id))

    tk.Label(green_frame, text=f"{i+1}", font=("Arial", 10), bg="darkgreen", fg="white").grid(row=i+1, column=0, padx=5, pady=2)
    entry_green_name = tk.Entry(green_frame, width=12)
    entry_green_name.grid(row=i+1, column=1, padx=5, pady=2)
    entry_green_id = tk.Entry(green_frame, width=12)
    entry_green_id.grid(row=i+1, column=2, padx=5, pady=2)
    player_entries.append((entry_green_name, entry_green_id))

# Create function buttons
button_frame = tk.Frame(root, bg="black")
button_frame.place(relx=0.1, rely=0.8)

buttons = [
    ("F1 Edit Game", "F1"),
    ("F2 Game Parameters", "F2"),
    ("F3 Start Game", "F3"),
    ("F5 PreEntered Games", "F5"),
    ("F7", "F7"),
    ("F8 View Game", "F8"),
    ("F10 Flick Sync", "F10"),
    ("F12 Clear Game", "F12")
]

for i, (text, key) in enumerate(buttons):
    tk.Button(button_frame, text=text, font=("Arial", 10), width=15, bg="gray", fg="white").grid(row=0, column=i, padx=5, pady=5)

# Run Tkinter loop
root.mainloop()
