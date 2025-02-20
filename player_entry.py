import tkinter as tk
from PIL import Image, ImageTk
from tkinter import PhotoImage, messagebox, simpledialog
import psycopg2
import os
from functools import partial  # Fix lambda scope issues
import pygame  # For music playback

# Import our UDP client module
from python_udpclient import send_equipment_id

# Initialize pygame mixer and load music file
pygame.mixer.init()
try:
    pygame.mixer.music.load("Incoming.mp3")
except Exception as e:
    print(f"Error loading music: {e}")

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

# --- New Delete Player Functions ---
def delete_player(player_id):
    """Delete the player with the given ID from the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM players WHERE id = %s;", (player_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"Database error during deletion: {e}")
        return False

def delete_player_ui(event=None):
    player_id_str = simpledialog.askstring("Delete Player", "Enter the player ID to delete:")
    if player_id_str and player_id_str.isdigit():
        player_id = int(player_id_str)
        # Retrieve the current codename to confirm deletion
        codename = get_player_codename(player_id)
        if codename:
            confirm = messagebox.askyesno("Confirm Deletion",
                                          f"Are you sure you want to delete player {player_id} ({codename})?")
            if confirm:
                if delete_player(player_id):
                    messagebox.showinfo("Success", "Player deleted successfully!")
                else:
                    messagebox.showerror("Error", "Failed to delete player.")
            else:
                messagebox.showinfo("Cancelled", "Player deletion cancelled.")
        else:
            messagebox.showwarning("Not Found", "Player not found in database.")
    else:
        messagebox.showwarning("Invalid Input", "Please enter a valid numeric player ID.")
# --- End Delete Player Functions ---

# Function to prompt for equipment id and send it via UDP
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
    valid_player = False  # Flag to indicate a valid player exists (found or added)
    if player_id.isdigit():
        print(f"Checking database for player ID: {player_id}")
        codename = get_player_codename(int(player_id))
        if codename:
            print(f"Found codename: {codename}")
            entry_name.delete(0, tk.END)
            entry_name.insert(0, codename)
            valid_player = True
        else:
            print("No codename found for this ID.")
            if messagebox.askyesno("Player Not Found", "No player found for the entered ID. Would you like to add a new player?"):
                new_codename = simpledialog.askstring("Add New Player", "Enter codename for the new player:")
                if new_codename:
                    if add_new_player(int(player_id), new_codename):
                        entry_name.delete(0, tk.END)
                        entry_name.insert(0, new_codename)
                        messagebox.showinfo("Player Added", "New player added successfully!")
                        valid_player = True
                    else:
                        messagebox.showerror("Database Error", "Failed to add new player.")
            # If user selects "No", valid_player remains False

    # Only prompt for equipment ID if we have a valid player (found or added)
    if event is not None:
        if event.keysym in ("Return", "Tab") and valid_player:
            prompt_equipment_id(player_id)
        if event.keysym == "Tab":
            event.widget.tk_focusNext().focus()


# --- Function to View All Players (F9) ---
def view_all_players(event=None):
    """F9: Retrieve and display all player IDs and codenames."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT id, codename FROM players ORDER BY id;")
        players = cur.fetchall()
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        messagebox.showerror("Database Error", f"Error retrieving players: {e}")
        return

    # Create a new window to display the players
    view_window = tk.Toplevel(root)
    view_window.title("All Players")
    
    # Set up a text widget with a scrollbar
    text_area = tk.Text(view_window, width=50, height=20)
    text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar = tk.Scrollbar(view_window, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.config(yscrollcommand=scrollbar.set)
    
    if players:
        for player in players:
            text_area.insert(tk.END, f"ID: {player[0]} - Codename: {player[1]}\n")
    else:
        text_area.insert(tk.END, "No players found in the database.")
    text_area.config(state=tk.DISABLED)
# --- End of View All Players ---

# --- Splash screen and transition to player entry screen ---
def showPlayerEntry():
    splash.destroy()
    entry_root = tk.Tk()
    entry_root.title("Player Entry Screen")
    try:
        entry_root.state('zoomed')
    except Exception as e:
        entry_root.attributes('-zoomed', True)
    
    # Create a canvas that fills the entire window.
    canvas = tk.Canvas(entry_root, width=entry_root.winfo_screenwidth(), 
                        height=entry_root.winfo_screenheight())
    canvas.pack(fill="both", expand=True)
    
    # Try to load and center the background image.
    try:
        bg_path = os.path.join(os.getcwd(), "background.png")
        bg_image = PhotoImage(file=bg_path)
        entry_root.bg_image = bg_image  # keep a reference
        canvas.create_image(entry_root.winfo_screenwidth() // 2,
                            entry_root.winfo_screenheight() // 2,
                            image=bg_image, anchor="center")
    except Exception as e:
        canvas.configure(bg="black")
    
    # Start background music (looped)
    pygame.mixer.music.play(-1)
    
    # Create a frame to hold the label and button.
    frame = tk.Frame(entry_root, bg="", bd=0)
    tk.Label(frame, text="Welcome Photon Warriors! \nPress START to begin Player Entry!", fg="black", font=("Arial", 20)).pack(pady=20)
    tk.Button(frame, text="Start", command=entry_root.destroy, font=("Arial", 14)).pack(pady=10)
    
    # Place the frame in the center of the canvas.
    canvas.create_window(entry_root.winfo_screenwidth() // 2,
                         entry_root.winfo_screenheight() // 2, window=frame)
    
    entry_root.mainloop()

## Create splash screen
splash = tk.Tk()
splash.title("Splash Screen")
splash.geometry("600x400")
splash.configure(bg="black")

# Define splash dimensions
splash_width = 600
splash_height = 400

# Calculate maximum logo size (80% of splash dimensions)
max_logo_width = int(splash_width * 0.8)
max_logo_height = int(splash_height * 0.8)

# Open, resize, and center the logo
logo_image = Image.open("logo.jpg")
logo_image = logo_image.resize((max_logo_width, max_logo_height), Image.Resampling.LANCZOS)
logo = ImageTk.PhotoImage(logo_image)

# Use pack with expand=True to center the logo
tk.Label(splash, image=logo, bg="black").pack(expand=True)

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
    """F3: Validate teams, display play action screen with player info and a countdown timer."""
    print("F3: Starting game!")
    
    # Validate that each team has at least one player
    red_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 0)
    green_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 1)
    if not red_has_player or not green_has_player:
        messagebox.showwarning("Incomplete Team", "Each team must have at least one player before starting the game.")
        return

    # Fade out the background music over 2 seconds only if team validation passes
    pygame.mixer.music.fadeout(2000)
    
    # Retrieve players for each team
    red_players = [(eid.get().strip(), ename.get().strip()) 
                   for idx, (eid, ename) in enumerate(player_entries) 
                   if idx % 2 == 0 and eid.get().strip() != ""]
    green_players = [(eid.get().strip(), ename.get().strip()) 
                     for idx, (eid, ename) in enumerate(player_entries) 
                     if idx % 2 == 1 and eid.get().strip() != ""]

    # Create a new window for the play action screen
    game_window = tk.Toplevel(root)
    game_window.title("Play Action Screen")
    
    # Create frames for each team
    red_frame_game = tk.Frame(game_window, bg="darkred", padx=10, pady=10)
    red_frame_game.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    green_frame_game = tk.Frame(game_window, bg="darkgreen", padx=10, pady=10)
    green_frame_game.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    # Display Red team players
    tk.Label(red_frame_game, text="RED TEAM", bg="darkred", fg="white", font=("Arial", 14, "bold")).pack(pady=5)
    for pid, codename in red_players:
        tk.Label(red_frame_game, text=f"ID: {pid} - {codename}", bg="darkred", fg="white", font=("Arial", 12)).pack(pady=2)
    
    # Display Green team players
    tk.Label(green_frame_game, text="GREEN TEAM", bg="darkgreen", fg="white", font=("Arial", 14, "bold")).pack(pady=5)
    for pid, codename in green_players:
        tk.Label(green_frame_game, text=f"ID: {pid} - {codename}", bg="darkgreen", fg="white", font=("Arial", 12)).pack(pady=2)
    
    # Add a countdown timer label
    countdown_label = tk.Label(game_window, text="", font=("Arial", 24))
    countdown_label.pack(pady=20)
    
    countdown_time = 5  # Countdown starting from 5 seconds

    def update_countdown():
        nonlocal countdown_time
        if countdown_time > 0:
            countdown_label.config(text=f"Game starting in {countdown_time}...")
            countdown_time -= 1
            game_window.after(1000, update_countdown)
        else:
            countdown_label.config(text="Game Started!")
            # Additional game-start logic can be added here

    update_countdown()


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
root.bind("<F4>", update_player_ui)
root.bind("<F6>", delete_player_ui)  # Key binding for delete
root.bind("<F7>", quit_game)
root.bind("<F9>", view_all_players)  # Key binding for view all players
root.bind("<F12>", clear_fields)

try:
    image_path = os.path.join(os.getcwd(), "background.png")
    bg_image = PhotoImage(file=image_path)
    canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
    canvas.pack(fill="both", expand=True)
    canvas.create_image(root.winfo_screenwidth() // 2, 
                        root.winfo_screenheight() // 2, 
                        image=bg_image, anchor="center")
except Exception as e:
    print("Background image not found, using default background.")
    root.configure(bg="black")

# Place logo image centered between the team rosters
try:
    logo_img = Image.open("logo.jpg")
    # Resize the logo to your desired dimensions
    logo_img = logo_img.resize((200, 150), Image.Resampling.LANCZOS)
    logo_img = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(root, image=logo_img, bg="black")
    # Place the logo at the center; adjust the relx, rely values as needed
    logo_label.place(relx=0.5, rely=0.3, anchor="center")
except Exception as e:
    print("Logo image error:", e)

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
    ("F3 Start Game", "F3"),
    ("F4 Update Player", "F4"),
    ("F6 Delete Player", "F6"),
    ("F7 Quit Game", "F7"),
    ("F9 View All Players", "F9"),
    ("F12 Clear Game", "F12")
]

key_action_map = {
    "F3": start_game,
    "F4": update_player_ui,
    "F6": delete_player_ui,
    "F9": view_all_players,
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
