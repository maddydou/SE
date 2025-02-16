import tkinter as tk
from PIL import Image, ImageTk
from tkinter import PhotoImage, messagebox
import psycopg2
import os
from functools import partial  # Import partial to fix lambda scope issue

# Database credentials
DB_NAME = "photon"
DB_USER = "student"
DB_PASSWORD = "student"  # Replace with your actual password
DB_HOST = "localhost"
DB_PORT = "5432"

# Function to fetch player codename by ID
def get_player_codename(player_id):
    """Fetch the player's codename from the database based on player ID."""
    try:
        print(f"Connecting to database for player ID: {player_id}")  # Debugging print
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT codename FROM players WHERE id = %s;", (player_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            print(f"Database result found: {result[0]}")  # Debugging print
            return result[0]  # Return the codename
        else:
            print("No matching ID found in database.")  # Debugging print
            return None
    except psycopg2.Error as e:
        messagebox.showerror("Database Error", f"Error connecting to database:\n{e}")
        return None

# Function to autofill name when ID is entered
def autofill_name(entry_id, entry_name, event=None):
    print("Autofill function triggered!")  # Debugging print
    player_id = entry_id.get().strip()
    if player_id.isdigit():
        print(f"Checking database for player ID: {player_id}")  # Debugging print
        codename = get_player_codename(int(player_id))
        if codename:
            print(f"Found codename: {codename}")  # Debugging print
            entry_name.delete(0, tk.END)
            entry_name.insert(0, codename)
        else:
            print("No codename found for this ID.")  # Debugging print
            messagebox.showwarning("Player Not Found", "No player found for the entered ID.")
    
    if event is not None and event.keysym == "Tab":
        event.widget.tk_focusNext().focus()  # Move to the next field manually


def showPlayerEntry():
    splash.destroy()
    

#create splash screen
splash = tk.Tk()
splash.title("Splash Screen")
splash.geometry("600x400")
splash.configure(bg="black")

#display logo
logo = Image.open("logo.jpg")
logo = logo.resize((300,200))
logo = ImageTk.PhotoImage(logo)

label = tk.Label(splash, image=logo, bg="black")
label.pack(pady=50)

splash.after(4000, showPlayerEntry)

splash.mainloop()







# Window control functions
def minimize_window():
    root.iconify()

def toggle_fullscreen():
    state = root.attributes('-fullscreen')
    root.attributes('-fullscreen', not state)

def close_window():
    root.destroy()

# -------------------------------
# New functions for F3, F12, and F7
# -------------------------------

def start_game(event=None):
    """F3 functionality: Ensure each team has at least one player before moving to play action screen."""
    print("F3: Starting game!")
    # Check that each team has at least one player.
    # In our layout, red team entries are at even indices (0,2,4,...)
    # and green team entries are at odd indices (1,3,5,...)
    red_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 0)
    green_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 1)
    
    if not red_has_player or not green_has_player:
        messagebox.showwarning("Incomplete Team", "Each team must have at least one player before starting the game.")
        return

    # If both teams have at least one player, create the Play Action Screen.
    game_window = tk.Toplevel(root)
    game_window.title("Play Action Screen")
    tk.Label(game_window, text="Play Action Screen", font=("Arial", 20)).pack(padx=20, pady=20)
    # Optionally add more controls for the play action screen here
    tk.Button(game_window, text="Close", command=game_window.destroy, font=("Arial", 12)).pack(pady=10)

def clear_fields(event=None):
    """F12 functionality: Clear all player entry fields."""
    print("F12: Clearing all fields!")
    for entry_id, entry_name in player_entries:
        entry_id.delete(0, tk.END)
        entry_name.delete(0, tk.END)

def quit_game(event=None):
    """F7 functionality: Quit the game."""
    print("F7: Quitting game!")
    root.destroy()

# -------------------------------
# Create main application window
root = tk.Tk()
root.title("Entry Terminal")
root.geometry("900x600")
root.attributes('-fullscreen', False)

# Bind F3, F12, and F7 keys to their respective functions
root.bind("<F3>", start_game)
root.bind("<F12>", clear_fields)
root.bind("<F7>", quit_game)

# Load background image
try:
    image_path = os.path.join(os.getcwd(), "background.png")  # Ensure correct path
    bg_image = PhotoImage(file=image_path)

    canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
    canvas.pack(fill="both", expand=True)
    canvas.create_image(root.winfo_screenwidth() // 2, root.winfo_screenheight() // 2, image=bg_image, anchor="center")
except Exception as e:
    print("Background image not found, using default background.")
    root.configure(bg="black")

# Create frames for Red and Green teams
red_frame = tk.Frame(root, bg="darkred", padx=10, pady=10)
red_frame.place(relx=0.25, rely=0.3, anchor="center")

green_frame = tk.Frame(root, bg="darkgreen", padx=10, pady=10)
green_frame.place(relx=0.75, rely=0.3, anchor="center")

# Create labels for team names
tk.Label(red_frame, text="RED TEAM", bg="darkred", fg="white", font=("Arial", 14, "bold"), width=20).grid(row=0, column=0, columnspan=3)
tk.Label(green_frame, text="GREEN TEAM", bg="darkgreen", fg="white", font=("Arial", 14, "bold"), width=20).grid(row=0, column=0, columnspan=3)

# Create player entry fields for both teams
player_entries = []
for i in range(15):  # 15 Players per team
    tk.Label(red_frame, text=f"{i+1}", font=("Arial", 10), bg="darkred", fg="white").grid(row=i+1, column=0, padx=5, pady=2)
    entry_red_id = tk.Entry(red_frame, width=5)
    entry_red_id.grid(row=i+1, column=1, padx=5, pady=2)
    entry_red_name = tk.Entry(red_frame, width=12)
    entry_red_name.grid(row=i+1, column=2, padx=5, pady=2)
    entry_red_id.bind("<Return>", partial(autofill_name, entry_red_id, entry_red_name))
    entry_red_id.bind("<Tab>", partial(autofill_name, entry_red_id, entry_red_name))
    player_entries.append((entry_red_id, entry_red_name))

    tk.Label(green_frame, text=f"{i+1}", font=("Arial", 10), bg="darkgreen", fg="white").grid(row=i+1, column=0, padx=5, pady=2)
    entry_green_id = tk.Entry(green_frame, width=5)
    entry_green_id.grid(row=i+1, column=1, padx=5, pady=2)
    entry_green_name = tk.Entry(green_frame, width=12)
    entry_green_name.grid(row=i+1, column=2, padx=5, pady=2)
    entry_green_id.bind("<Return>", partial(autofill_name, entry_green_id, entry_green_name))
    entry_green_id.bind("<Tab>", partial(autofill_name, entry_green_id, entry_green_name))
    player_entries.append((entry_green_id, entry_green_name))

# Restore function buttons
button_frame = tk.Frame(root, bg="black")
button_frame.place(relx=0.5, rely=0.85, anchor="center")

buttons = [
    ("F1 Edit Game", "F1"),
    ("F2 Game Parameters", "F2"),
    ("F3 Start Game", "F3"),
    ("F5 PreEntered Games", "F5"),
    ("F7 Quit Game", "F7"),
    ("F8 View Game", "F8"),
    ("F10 Flick Sync", "F10"),
    ("F12 Clear Game", "F12")
]

# Map specific keys to our new functions
key_action_map = {
    "F3": start_game,
    "F12": clear_fields,
    "F7": quit_game
}

for i, (text, key) in enumerate(buttons):
    if key in key_action_map:
        action_command = key_action_map[key]
    else:
        action_command = lambda text=text: print(f'Button {text} clicked!')
    tk.Button(button_frame, text=text, font=("Arial", 10), width=15,
              bg="gray", fg="white", command=action_command).grid(row=0, column=i, padx=5, pady=5)

# Run Tkinter loop
root.mainloop()





