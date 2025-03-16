import tkinter as tk
from PIL import Image, ImageTk
from tkinter import PhotoImage, messagebox, simpledialog
import psycopg2
import os
from functools import partial  # Fix lambda scope issues
import pygame  # For music playback
import vlc     # For video playback

instance = vlc.Instance(["--no-xlib", "--quiet", "--quiet-synchro", "--no-video-title-show"])

# Import our UDP client module
from python_udpclient import send_equipment_id

# Initialize pygame mixer and load background music
pygame.mixer.init()
try:
    pygame.mixer.music.load("Incoming.mp3")
except Exception as e:
    print(f"Error loading music: {e}")

# Check if button.mp3 exists in the current working directory
if os.path.exists("button.mp3"):
    try:
        button_sound = pygame.mixer.Sound("button.mp3")
        # Optionally set volume here:
        button_sound.set_volume(1.0)
    except Exception as e:
        print("Error loading button sound:", e)
else:
    print("button.mp3 not found in:", os.getcwd())

## Define a dedicated channel for button sounds
button_channel = pygame.mixer.Channel(1)
button_channel.set_volume(1.0)

def with_sound(fn):
    def wrapper(*args, **kwargs):
        try:
            button_channel.play(button_sound)
        except Exception as e:
            print("Error playing button sound:", e)
        return fn(*args, **kwargs)
    return wrapper

# --- Custom dialog functions ---
def sound_askstring(title, prompt):
    try:
        button_channel.play(button_sound)
    except Exception as e:
        print("Error playing button sound:", e)
    return simpledialog.askstring(title, prompt)

def sound_askyesno(title, prompt, parent=None):
    try:
        button_channel.play(button_sound)
    except Exception as e:
        print("Error playing button sound:", e)
    return messagebox.askyesno(title, prompt, parent=parent)

def sound_showinfo(title, message):
    try:
        button_channel.play(button_sound)
    except Exception as e:
        print("Error playing button sound:", e)
    messagebox.showinfo(title, message)

def sound_showwarning(title, message):
    try:
        button_channel.play(button_sound)
    except Exception as e:
        print("Error playing button sound:", e)
    messagebox.showwarning(title, message)

def sound_showerror(title, message):
    try:
        button_channel.play(button_sound)
    except Exception as e:
        print("Error playing button sound:", e)
    messagebox.showerror(title, message)

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
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
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
        sound_showerror("Database Error", f"Error connecting to database:\n{e}")
        return None

# Add a new player to the database
def add_new_player(player_id, codename):
    """Insert a new player into the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
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
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
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
@with_sound
def update_player_ui(event=None):
    player_id_str = sound_askstring("Update Player", "Enter the player ID to update:")
    if player_id_str and player_id_str.isdigit():
        player_id = int(player_id_str)
        current_codename = get_player_codename(player_id)
        if current_codename:
            new_codename = sound_askstring("Update Player", f"Current codename is '{current_codename}'.\nEnter new codename:")
            if new_codename:
                if update_player(player_id, new_codename):
                    sound_showinfo("Success", "Player updated successfully!")
                else:
                    sound_showerror("Error", "Failed to update player.")
        else:
            sound_showwarning("Not Found", "Player not found. Cannot update a non-existent player.")
    else:
        sound_showwarning("Invalid Input", "Please enter a valid numeric player ID.")

# --- New Delete Player Functions ---
@with_sound
def delete_player_ui(event=None):
    player_id_str = sound_askstring("Delete Player", "Enter the player ID to delete:")
    if player_id_str and player_id_str.isdigit():
        player_id = int(player_id_str)
        # Retrieve the current codename to confirm deletion
        codename = get_player_codename(player_id)
        if codename:
            confirm = sound_askyesno("Confirm Deletion", f"Are you sure you want to delete player {player_id} ({codename})?")
            if confirm:
                if delete_player(player_id):
                    sound_showinfo("Success", "Player deleted successfully!")
                else:
                    sound_showerror("Error", "Failed to delete player.")
            else:
                sound_showinfo("Cancelled", "Player deletion cancelled.")
        else:
            sound_showwarning("Not Found", "Player not found in database.")
    else:
        sound_showwarning("Invalid Input", "Please enter a valid numeric player ID.")

def delete_player(player_id):
    """Delete the player with the given ID from the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
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

# Function to prompt for equipment id and send it via UDP
@with_sound
def prompt_equipment_id(player_id):
    """
    Prompts the operator to enter the equipment ID for a given player,
    then sends the equipment ID via UDP.
    """
    equip_id = sound_askstring("Equipment ID", f"Enter equipment ID for player {player_id}:")
    if equip_id and equip_id.isdigit():
        try:
            send_equipment_id(equip_id)
            sound_showinfo("Equipment ID Sent", f"Equipment ID {equip_id} sent to UDP server.")
        except Exception as e:
            sound_showerror("UDP Error", f"Failed to send equipment id: {e}")
    else:
        sound_showwarning("Invalid Input", "Please enter a valid numeric equipment ID.")

# Function to autofill name when ID is entered and prompt for equipment id on Enter or Tab
@with_sound
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
            if sound_askyesno("Player Not Found", "No player found for the entered ID. Would you like to add a new player?"):
                new_codename = sound_askstring("Add New Player", "Enter codename for the new player:")
                if new_codename:
                    if add_new_player(int(player_id), new_codename):
                        entry_name.delete(0, tk.END)
                        entry_name.insert(0, new_codename)
                        sound_showinfo("Player Added", "New player added successfully!")
                        valid_player = True
                    else:
                        sound_showerror("Database Error", "Failed to add new player.")
    # Only prompt for equipment ID if we have a valid player (found or added)
    if event is not None:
        if event.keysym in ("Return", "Tab") and valid_player:
            prompt_equipment_id(player_id)
        if event.keysym == "Tab":
            event.widget.tk_focusNext().focus()

# --- Function to View All Players (F9) ---
@with_sound
def view_all_players(event=None):
    """F9: Retrieve and display all player IDs and codenames."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT id, codename FROM players ORDER BY id;")
        players = cur.fetchall()
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        sound_showerror("Database Error", f"Error retrieving players: {e}")
        return

    view_window = tk.Toplevel(root)
    view_window.title("All Players")
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

# --- Tutorial Functions ---
@with_sound
def play_tutorial(event=None):
    """F1: Fade out background music, display countdown and then play tutorial.mp4."""
    # Fade out background music over 3 seconds
    pygame.mixer.music.fadeout(3000)
    
    # Create a countdown window and disable its close button
    countdown_win = tk.Toplevel()
    countdown_win.title("Tutorial Loading")
    countdown_win.protocol("WM_DELETE_WINDOW", lambda: None)  # Disables the close (X) button

    countdown_label = tk.Label(countdown_win, text="Tutorial loading in 3...", font=("Arial", 20))
    countdown_label.pack(padx=20, pady=20)
    countdown_time = 3
    def update_countdown():
        nonlocal countdown_time
        if countdown_time > 0:
            countdown_label.config(text=f"Tutorial loading in {countdown_time}...")
            countdown_time -= 1
            countdown_win.after(1000, update_countdown)
        else:
            countdown_win.destroy()
            launch_tutorial()
    update_countdown()


def launch_tutorial():
    """Launch the tutorial video using VLC in a new window."""
    video_win = tk.Toplevel()
    video_win.title("Tutorial")
    # Set the window size
    desired_width = 800
    desired_height = 600
    # Calculate center position
    screen_width = video_win.winfo_screenwidth()
    screen_height = video_win.winfo_screenheight()
    x = (screen_width - desired_width) // 2
    y = (screen_height - desired_height) // 2
    video_win.geometry(f"{desired_width}x{desired_height}+{x}+{y}")
    video_win.attributes("-topmost", True)  # Keep it on top

    # Create a frame to host the video
    video_frame = tk.Frame(video_win)
    video_frame.pack(fill="both", expand=True)
    
    # Create VLC instance and media player for tutorial.mp4
    instance = vlc.Instance(["--no-xlib", "--quiet", "--quiet-synchro", "--no-video-title-show"])
    player = instance.media_player_new()
    media = instance.media_new("tutorial.mp4")
    player.set_media(media)
    
    video_win.update_idletasks()  # Ensure the window is drawn
    win_id = video_frame.winfo_id()
    import platform
    if platform.system() == "Windows":
        player.set_hwnd(win_id)
    else:
        player.set_xwindow(win_id)
    
    # Delay starting playback slightly
    video_win.after(100, player.play)
    
    # Define a function for closing the window (manual or skip)
    def on_close():
        player.stop()
        video_win.destroy()
        pygame.mixer.music.play(-1)  # Resume background music
    video_win.protocol("WM_DELETE_WINDOW", on_close)
    
    # Bind key events: if the user presses any key, ask if they want to skip
    def on_key(event):
        answer = sound_askyesno("Skip Tutorial", "Do you want to skip the tutorial?", parent=video_win)
        if answer:
            on_close()
        else:
            video_win.lift()  # Bring window back to front
        return "break"  # Prevent further handling
    video_win.bind("<Key>", on_key)
    
    # Check periodically if the video has ended
    def check_video():
        state = player.get_state()
        if state in [vlc.State.Ended, vlc.State.Stopped]:
            on_close()
        else:
            video_win.after(1000, check_video)
    check_video()





# --- Splash screen and transition to player entry screen ---
def showPlayerEntry():
    splash.destroy()
    entry_root = tk.Tk()
    entry_root.title("Player Entry Screen")
    try:
        entry_root.state('zoomed')
    except Exception as e:
        entry_root.attributes('-zoomed', True)
    canvas = tk.Canvas(entry_root, width=entry_root.winfo_screenwidth(),
                        height=entry_root.winfo_screenheight())
    canvas.pack(fill="both", expand=True)
    try:
        bg_path = os.path.join(os.getcwd(), "background.png")
        bg_image = PhotoImage(file=bg_path)
        entry_root.bg_image = bg_image
        canvas.create_image(entry_root.winfo_screenwidth() // 2,
                            entry_root.winfo_screenheight() // 2,
                            image=bg_image, anchor="center")
    except Exception as e:
        canvas.configure(bg="black")
    pygame.mixer.music.play(-1)  # Start looping background music

    # Custom splash start function
    @with_sound
    def splash_start():
        entry_root.destroy()
    
    frame = tk.Frame(entry_root, bg="", bd=0)
    tk.Label(frame, text="Welcome Photon Warriors! \nPress START to begin Player Entry!", 
             fg="black", font=("Arial", 20)).pack(pady=20)
    tk.Button(frame, text="Start", command=splash_start, font=("Arial", 14)).pack(pady=10)
    canvas.create_window(entry_root.winfo_screenwidth() // 2,
                         entry_root.winfo_screenheight() // 2, window=frame)
    entry_root.mainloop()

# Create splash screen
splash = tk.Tk()
splash.title("Splash Screen")
splash.geometry("600x400")
splash.configure(bg="black")

# Open and maximize the logo to fill the splash screen (600x400)
from PIL import Image  # Already imported above
logo_image = Image.open("logo.jpg")
logo_image = logo_image.resize((600, 400), Image.Resampling.LANCZOS)
logo = ImageTk.PhotoImage(logo_image)

# Pack the logo Label to fill the splash window
tk.Label(splash, image=logo, bg="black").pack(expand=True, fill="both")

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

@with_sound
def start_game(event=None):
    """F3: Validate teams, display play action screen with player info and a countdown timer."""
    print("F3: Starting game!")
    red_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 0)
    green_has_player = any(entry_id.get().strip() != "" for idx, (entry_id, _) in enumerate(player_entries) if idx % 2 == 1)
    if not red_has_player or not green_has_player:
        sound_showwarning("Incomplete Team", "Each team must have at least one player before starting the game.")
        return
    pygame.mixer.music.fadeout(5000)
    red_players = [(eid.get().strip(), ename.get().strip())
                   for idx, (eid, ename) in enumerate(player_entries)
                   if idx % 2 == 0 and eid.get().strip() != ""]
    green_players = [(eid.get().strip(), ename.get().strip())
                     for idx, (eid, ename) in enumerate(player_entries)
                     if idx % 2 == 1 and eid.get().strip() != ""]
    game_window = tk.Toplevel(root)
    game_window.title("Play Action Screen")
    red_frame_game = tk.Frame(game_window, bg="darkred", padx=10, pady=10)
    red_frame_game.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    green_frame_game = tk.Frame(game_window, bg="darkgreen", padx=10, pady=10)
    green_frame_game.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    tk.Label(red_frame_game, text="RED TEAM", bg="darkred", fg="white", font=("Arial", 14, "bold")).pack(pady=5)
    for pid, codename in red_players:
        tk.Label(red_frame_game, text=f"ID: {pid} - {codename}", bg="darkred", fg="white", font=("Arial", 12)).pack(pady=2)
    tk.Label(green_frame_game, text="GREEN TEAM", bg="darkgreen", fg="white", font=("Arial", 14, "bold")).pack(pady=5)
    for pid, codename in green_players:
        tk.Label(green_frame_game, text=f"ID: {pid} - {codename}", bg="darkgreen", fg="white", font=("Arial", 12)).pack(pady=2)
    countdown_label = tk.Label(game_window, text="", font=("Arial", 24))
    countdown_label.pack(pady=20)
    countdown_time = 30
    def update_countdown():
        nonlocal countdown_time
        if countdown_time > 0:
            countdown_label.config(text=f"Game starting in {countdown_time}...")
            countdown_time -= 1
            game_window.after(1000, update_countdown)
        else:
            countdown_label.config(text="Game Started!")
    update_countdown()

@with_sound
def clear_fields(event=None):
    """F12: Clear all player entry fields."""
    print("F12: Clearing all fields!")
    for entry_id, entry_name in player_entries:
        entry_id.delete(0, tk.END)
        entry_name.delete(0, tk.END)

@with_sound
def quit_game(event=None):
    """F7: Quit the game."""
    print("F7: Quitting game!")
    root.destroy()

root = tk.Tk()
root.title("Player Entry Terminal")
root.geometry("900x600")
root.attributes('-fullscreen', True)
# Bind our keys – note we now also bind F1 for the tutorial
root.bind("<F1>", with_sound(play_tutorial))
root.bind("<F3>", with_sound(start_game))
root.bind("<F4>", with_sound(update_player_ui))
root.bind("<F6>", with_sound(delete_player_ui))
root.bind("<F7>", with_sound(quit_game))
root.bind("<F9>", with_sound(view_all_players))
root.bind("<F12>", with_sound(clear_fields))

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

button_frame = tk.Frame(root, bg="black")
button_frame.place(relx=0.5, rely=0.85, anchor="center")

buttons = [
    ("F1 Play Tutorial", "F1"),
    ("F3 Start Game", "F3"),
    ("F4 Update Player", "F4"),
    ("F6 Delete Player", "F6"),
    ("F7 Quit Game", "F7"),
    ("F9 View All Players", "F9"),
    ("F12 Clear Game", "F12")
]

key_action_map = {
    "F1": play_tutorial,
    "F3": start_game,
    "F4": update_player_ui,
    "F6": delete_player_ui,
    "F9": view_all_players,
    "F12": clear_fields,
    "F7": quit_game
}

for i, (text, key) in enumerate(buttons):
    if key in key_action_map:
        action_command = with_sound(key_action_map[key])
    else:
        action_command = lambda text=text: print(f'Button {text} clicked!')
    tk.Button(button_frame, text=text, font=("Arial", 10), width=15,
              bg="gray", fg="white", command=action_command).grid(row=0, column=i, padx=5, pady=5)


root.mainloop()
