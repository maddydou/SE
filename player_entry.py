import tkinter as tk
from PIL import Image, ImageTk
from tkinter import PhotoImage, messagebox, simpledialog
import psycopg2
import os
from functools import partial  # Fix lambda scope issues

# Import our UDP client module
from udp_client import send_equipment_id

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
        print(f"Connecting to database for player ID: {player_id}")
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
            print(f"Database result found: {result[0]}")
            return result[0]
        else:
            print("No matching ID found in database.")
            return None
    except psycopg2.Error as e:
        messagebox.showerror("Database Error", f"Error connecting to database:\n{e}")
        return None

# Add a new player to the database
def add_new_player(player_id, codename):
    """Insert a new player into the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO players (id, codename) VALUES (%s, %s);", (player_id, codename))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False

# Update an existing player's codename
def update_player(player_id, new_codename):
    """Update the player's codename in the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("UPDATE players SET codename = %s WHERE id = %s;", (new_codename, player_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"Database error during update: {e}")
        return False

# Prompt user to update a player's codename
def update_player_ui(event=None):
    player_id_str = simpledialog.askstring("Update Player", "Enter the player ID to update:")
    if player_id_str and player_id_str.isdigit():
        player_id = int(player_id_str)
        current_codename = get_player_codename(player_id)
        if current_codename:
            new_codename = simpledialog.askstring("Update Player", f"Current codename is '{current_codename}'.\nEnter new codename:")
            if new_codename:
                if update_player(player_id, new_codename):
                    messagebox.showinfo("Success", "Player updated successfully!")
                else:
                    messagebox.showerror("Error", "Failed to update player.")
        else:
            messagebox.showwarning("Not Found", "Player not found. Cannot update a non-existent player.")
    else:
        messagebox.showwarning("Invalid Input", "Please enter a valid numeric player ID.")

# Prompt for equipment id and send it via UDP
def prompt_equipment_id(player_id):
    """
    Prompts the operator to enter the equipment ID for a given player,
    then sends the equipment ID via UDP.
    """
    equip_id = simpledialog.askstring("Equipment ID", f"Enter equipment ID for player {player_id}:")
    if equip_id and equip_id.isdigit():
        try:
            send_equipment_id(equip_id)
            messagebox.showinfo("Equipment ID Sent", f"Equipment ID {equip_id} sent to UDP server.")
        except Exception as e:
            messagebox.showerror("UDP Error", f"Failed to send equipment id: {e}")
    else:
        messagebox.showwarning("Invalid Input", "Please enter a valid numeric equipment ID.")

# Function to autofill name when ID is entered and prompt for equipment id on Enter or Tab
def autofill_name(entry_id, entry_name, event=None):
    print("Autofill function triggered!")
    player_id = entry_id.get().strip()
    if player_id.isdigit():
        print(f"Checking database for player ID: {player_id}")
        codename = get_player_codename(int(player_id))
        if codename:
            print(f"Found codename: {codename}")
            entry_name.delete(0, tk.END)
            entry_name.insert(0, codename)
        else:
            print("No codename found for this ID.")
            if messagebox.askyesno("Player Not Found", "No player found for the entered ID. Would you like to add a new player?"):
                new_codename = simpledialog.askstring("Add New Player", "Enter codename for the new player:")
                if new_codename:
                    if add_new_player(int(player_id), new_codename):
                        entry_name.delete(0, tk.END)
                        entry_name.insert(0, new_codename)
                        messagebox.showinfo("Player Added", "New player added successfully!")
                    else:
                        messagebox.showerror("Database Error", "Failed to add new player.")
    if event is not None:
        if event.keysym in ("Return", "Tab"):
            prompt_equipment_id(player_id)
        if event.keysym == "Tab":
            event.widget.tk_focusNext().focus()

# --- Splash screen and transition to player entry screen ---

def showPlayerEntry():
    splash.destroy()
    # Create entry screen
    entry_root = tk.Tk()
    entry_root.title("Player Entry Screen")
    try:
        entry_root.state('zoomed')
    except Exception as e:
        entry_root.attributes('-zoomed', True)
    entry_root.configure(bg="black")
    tk.Label(entry_root, text="Player Entry Screen", fg="white", bg="black", font=("Arial", 20)).pack(pady=20)
    tk.Button(entry_root, text="Start", command=entry_root.destroy, font=("Arial", 14)).pack(pady=10)
    entry_root.mainloop()

# Create splash screen
splash = tk.Tk()
splash.title("Splash Screen")
splash.geometry("600x400")
splash.configure(bg="black")
logo = Image.open("logo.jpg")
logo = logo.resize((300, 200))
logo = ImageTk.PhotoImage(logo)
tk.Label(splash, image=logo, bg="black").pack(pady=50)
splash.after(4000, showPlayerEntry)
splash.mainloop()       

# --- End Splash; now create the main application window ---

def minimize_window():
    root.iconify()

def toggle_fullscreen():
    state = root.attributes('-fullscreen')
    root.attributes('-fullscreen', not state)

def close_window():
    root.destroy()

def start_game(event=None):
    """F3: Validate teams and move to play action screen."""
    print("F3: Starting game!")
    red_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 0)
    green_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 1)
    if not red_has_player or not green_has_player:
        messagebox.showwarning("Incomplete Team", "Each team must have at least one player before starting the game.")
        return
    game_window = tk.Toplevel(root)
    game_window.title("Play Action Screen")
    tk.Label(game_window, text="Play Action Screen", font=("Arial", 20)).pack(padx=20, pady=20)
    tk.Button(game_window, text="Close", command=game_window.destroy, font=("Arial", 12)).pack(pady=10)

def clear_fields(event=None):
    """F12: Clear all player entry fields."""
    print("F12: Clearing all fields!")
    for entry_id, entry_name in player_entries:
        entry_id.delete(0, tk.END)
        entry_name.delete(0, tk.END)

def quit_game(event=None):
    """F7: Quit the game."""
    print("F7: Quitting game!")
    root.destroy()

root = tk.Tk()
root.title("Player Entry Terminal")
root.geometry("900x600")
root.attributes('-fullscreen', True)
root.bind("<F3>", start_game)
root.bind("<F12>", clear_fields)
root.bind("<F7>", quit_game)
root.bind("<F4>", update_player_ui)

try:
    image_path = os.path.join(os.getcwd(), "background.png")
    bg_image = PhotoImage(file=image_path)
    canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
    canvas.pack(fill="both", expand=True)
    canvas.create_image(root.winfo_screenwidth() // 2, root.winfo_screenheight() // 2, image=bg_image, anchor="center")
except Exception as e:
    print("Background image not found, using default background.")
    root.configure(bg="black")

red_frame = tk.Frame(root, bg="darkred", padx=10, pady=10)
red_frame.place(relx=0.25, rely=0.3, anchor="center")
green_frame = tk.Frame(root, bg="darkgreen", padx=10, pady=10)
green_frame.place(relx=0.75, rely=0.3, anchor="center")

tk.Label(red_frame, text="RED TEAM", bg="darkred", fg="white", font=("Arial", 14, "bold"), width=20).grid(row=0, column=0, columnspan=3)
tk.Label(green_frame, text="GREEN TEAM", bg="darkgreen", fg="white", font=("Arial", 14, "bold"), width=20).grid(row=0, column=0, columnspan=3)

player_entries = []
for i in range(15):
    # Red team
    tk.Label(red_frame, text=f"{i+1}", font=("Arial", 10), bg="darkred", fg="white").grid(row=i+1, column=0, padx=5, pady=2)
    entry_red_id = tk.Entry(red_frame, width=5)
    entry_red_id.grid(row=i+1, column=1, padx=5, pady=2)
    entry_red_name = tk.Entry(red_frame, width=12)
    entry_red_name.grid(row=i+1, column=2, padx=5, pady=2)
    entry_red_id.bind("<Return>", partial(autofill_name, entry_red_id, entry_red_name))
    entry_red_id.bind("<Tab>", partial(autofill_name, entry_red_id, entry_red_name))
    player_entries.append((entry_red_id, entry_red_name))
    
    # Green team
    tk.Label(green_frame, text=f"{i+1}", font=("Arial", 10), bg="darkgreen", fg="white").grid(row=i+1, column=0, padx=5, pady=2)
    entry_green_id = tk.Entry(green_frame, width=5)
    entry_green_id.grid(row=i+1, column=1, padx=5, pady=2)
    entry_green_name = tk.Entry(green_frame, width=12)
    entry_green_name.grid(row=i+1, column=2, padx=5, pady=2)
    entry_green_id.bind("<Return>", partial(autofill_name, entry_green_id, entry_green_name))
    entry_green_id.bind("<Tab>", partial(autofill_name, entry_green_id, entry_green_name))
    player_entries.append((entry_green_id, entry_green_name))

button_frame = tk.Frame(root, bg="black")
button_frame.place(relx=0.5, rely=0.85, anchor="center")

buttons = [
    ("F1 Edit Game", "F1"),
    ("F2 Game Parameters", "F2"),
    ("F3 Start Game", "F3"),
    ("F4 Update Player", "F4"),
    ("F5 PreEntered Games", "F5"),
    ("F7 Quit Game", "F7"),
    ("F8 View Game", "F8"),
    ("F10 Flick Sync", "F10"),
    ("F12 Clear Game", "F12")
]

key_action_map = {
    "F3": start_game,
    "F4": update_player_ui,
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

root.mainloop()
