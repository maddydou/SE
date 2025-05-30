import tkinter as tk
from PIL import Image, ImageTk
from tkinter import PhotoImage, messagebox, simpledialog
import psycopg2
import os
from functools import partial  # Fix lambda scope issues
import pygame  # For music playback
import vlc     # For video playback
import subprocess   # For running external scripts if needed
import time
import socket  # For connecting with the client
from python_udpclient import send_equipment_id
import random
import threading

# --- Global flags / data structures ---
stop_listener = False

# 🅱️ Keep track of labels to update when a player hits a base
base_hit_labels = {}

# 🗃️ Stats for each player: team, codename, score, base_hits, label
player_stats = {}

# 🆕 Map equipment_id -> player_db_id
equip_to_player = {}  # This is crucial for the new fix

# 🆕 Keep track of blink callback ID so we can cancel it
blink_job_id = None

# 🎮 UDP socket to SEND control messages to traffic generator on port 7500
traffic_control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
traffic_generator_address = ("127.0.0.1", 7500)

pygame.mixer.init()

music_tracks = [
    "Incoming.mp3",
    "button.mp3",
]

instance = vlc.Instance(["--no-xlib", "--quiet", "--quiet-synchro", "--no-video-title-show"])

udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_receive_socket.bind(("127.0.0.1", 7501))
print("[DEBUG] Bound UDP socket on 127.0.0.1:7501 for incoming traffic generator messages")

#########################################################
# Team score labels (red_team_score_label, green_team_score_label)
# We'll reorder the players after each score update
#########################################################
red_team_score_label = None
green_team_score_label = None

blink_state = False

def blink_leading_team():
    """
    Toggle label backgrounds to highlight the leading team.
    We'll store the job ID in blink_job_id so we can cancel later.
    """
    global blink_state, blink_job_id

    # Recompute red_total vs green_total
    red_total = sum(st["score"] for pid, st in player_stats.items() if st["team"] == "red")
    green_total = sum(st["score"] for pid, st in player_stats.items() if st["team"] == "green")

    if red_team_score_label and green_team_score_label:
        if red_total > green_total:
            color = "yellow" if blink_state else "darkred"
            red_team_score_label.config(bg=color)
            green_team_score_label.config(bg="darkgreen")
        elif green_total > red_total:
            color = "yellow" if blink_state else "darkgreen"
            green_team_score_label.config(bg=color)
            red_team_score_label.config(bg="darkred")
        else:
            # tie
            red_team_score_label.config(bg="darkred")
            green_team_score_label.config(bg="darkgreen")

    blink_state = not blink_state
    # Store the callback ID so we can cancel later
    blink_job_id = root.after(500, blink_leading_team)

def reorder_team_labels(team):
    """
    Sort the players on a team from highest to lowest score,
    and re-pack their labels accordingly.
    """
    if team == "red":
        frame = red_frame_game
    else:
        frame = green_frame_game

    team_players = [(pid, st) for pid, st in player_stats.items() if st["team"] == team]
    team_players.sort(key=lambda x: x[1]["score"], reverse=True)

    # skip the first child of the frame (the team's label)
    children = frame.pack_slaves()
    if len(children) > 1:
        for widget in children[1:]:
            widget.forget()

    for pid, stats in team_players:
        label = stats["label"]
        label.pack(pady=2)

def update_player_label(pid):
    if pid not in player_stats:
        return
    stats = player_stats[pid]
    label = stats["label"]

    b_symbol = " 🅱️" if stats["base_hits"] > 0 else ""
    new_font = ("Arial", 12, "bold") if stats["base_hits"] > 0 else ("Arial", 12)

    new_text = f"ID: {pid} - {stats['codename']} (Score: {stats['score']}, BH: {stats['base_hits']}){b_symbol}"
    label.config(text=new_text, font=new_font)

def update_team_scores():
    global red_team_score_label, green_team_score_label
    red_total = 0
    green_total = 0
    for pid, stats in player_stats.items():
        if stats["team"] == "red":
            red_total += stats["score"]
        elif stats["team"] == "green":
            green_total += stats["score"]

    if red_team_score_label:
        red_team_score_label.config(text=f"RED TEAM (Score: {red_total})")
    if green_team_score_label:
        green_team_score_label.config(text=f"GREEN TEAM (Score: {green_total})")

def listen_for_messages():
    global stop_listener
    while not stop_listener:
        try:
            data, addr = udp_receive_socket.recvfrom(1024)
            if not data:
                continue
            message = data.decode().strip()
            print(f"[UDP] Received message from {addr}: {message}")

            parts = message.split(":")
            if len(parts) == 2:
                hitter_equip, target_equip = parts
                event_str = ""

                # Translate the hitter equipment -> actual DB ID
                hitter_id = equip_to_player.get(hitter_equip)
                if not hitter_id:
                    print(f"[WARNING] No mapping for equipment {hitter_equip}. Ignoring event.")
                    continue

                hitter_name = player_stats[hitter_id]["codename"] if hitter_id in player_stats else f"Unknown({hitter_id})"
                hitter_team = player_stats[hitter_id]["team"] if hitter_id in player_stats else None

                if target_equip in ("43", "53"):
                    # Base hit
                    base_color = "Green" if target_equip == "43" else "Red"
                    event_str = f"{hitter_name} hits {base_color} base!"

                    # Only award +100 if correct team hits correct base
                    if target_equip == "53":  # Red base
                        if hitter_team == "green":
                            player_stats[hitter_id]["score"] += 100
                            player_stats[hitter_id]["base_hits"] += 1
                            update_player_label(hitter_id)
                            update_team_scores()
                            reorder_team_labels(hitter_team)

                    elif target_equip == "43":  # Green base
                        if hitter_team == "red":
                            player_stats[hitter_id]["score"] += 100
                            player_stats[hitter_id]["base_hits"] += 1
                            update_player_label(hitter_id)
                            update_team_scores()
                            reorder_team_labels(hitter_team)

                    response_id = target_equip

                else:
                    # normal player vs player => translate the target too
                    target_id = equip_to_player.get(target_equip)
                    if not target_id:
                        print(f"[WARNING] No mapping for equipment {target_equip}. Ignoring event.")
                        continue

                    if hitter_team and target_id in player_stats:
                        target_team = player_stats[target_id]["team"]
                        target_name = player_stats[target_id]["codename"]

                        if hitter_team != target_team:
                            player_stats[hitter_id]["score"] += 10
                            event_str = f"{hitter_name} hits enemy {target_name}!"
                        else:
                            player_stats[hitter_id]["score"] -= 10
                            event_str = f"{hitter_name} hits own teammate {target_name}!"

                        update_player_label(hitter_id)
                        update_team_scores()
                        reorder_team_labels(hitter_team)
                    else:
                        event_str = f"{hitter_equip} hits {target_equip} (no mapping found)"

                    # Friendly-fire rule for transmissions
                    if hitter_team and (target_id in player_stats):
                        target_team = player_stats[target_id]["team"]
                        if hitter_team != target_team:
                            response_id = target_equip
                        else:
                            response_id = hitter_equip
                    else:
                        response_id = target_equip

                if event_str:
                    print(f"[DEBUG] Logging event: {event_str}")
                    add_battle_event(event_str)

                traffic_control_socket.sendto(response_id.encode('utf-8'), traffic_generator_address)
                print(f"[DEBUG] Sent response back to traffic generator: {response_id}")

        except Exception as e:
            if not stop_listener:
                print(f"[ERROR] Exception in message listener: {e}")
            break

threading.Thread(target=listen_for_messages, daemon=True).start()

pygame.mixer.init()
try:
    pygame.mixer.music.load("Incoming.mp3")
except Exception as e:
    print(f"Error loading music: {e}")

if os.path.exists("button.mp3"):
    try:
        button_sound = pygame.mixer.Sound("button.mp3")
        button_sound.set_volume(1.0)
    except Exception as e:
        print("Error loading button sound:", e)
else:
    print("button.mp3 not found in:", os.getcwd())

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

DB_NAME = "photon"
DB_USER = "student"
DB_PASSWORD = "student"  # Replace with your actual password
DB_HOST = "localhost"
DB_PORT = "5432"

def add_battle_event(text):
    global battle_log
    battle_log.config(state="normal")
    battle_log.insert(tk.END, text + "\n")
    battle_log.see(tk.END)  # auto-scroll to bottom
    battle_log.config(state="disabled")

def get_player_codename(player_id):
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

def add_new_player(player_id, codename):
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

def update_player(player_id, new_codename):
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

@with_sound
def delete_player_ui(event=None):
    player_id_str = sound_askstring("Delete Player", "Enter the player ID to delete:")
    if player_id_str and player_id_str.isdigit():
        player_id = int(player_id_str)
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

@with_sound
def prompt_equipment_id(player_id):
    """
    Prompts the operator to enter the equipment ID for a given player,
    then sends the equipment ID via UDP, and stores equip->player mapping.
    """
    equip_id = sound_askstring("Equipment ID", f"Enter equipment ID for player {player_id}:")
    if equip_id and equip_id.isdigit():
        try:
            send_equipment_id(equip_id)
            sound_showinfo("Equipment ID Sent", f"Equipment ID {equip_id} sent to UDP server.")

            # Also store the mapping in equip_to_player
            equip_to_player[equip_id] = str(player_id)

        except Exception as e:
            sound_showerror("UDP Error", f"Failed to send equipment id: {e}")
    else:
        sound_showwarning("Invalid Input", "Please enter a valid numeric equipment ID.")

@with_sound
def autofill_name(entry_id, entry_name, event=None):
    print("Autofill function triggered!")
    player_id = entry_id.get().strip()
    valid_player = False
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
    if event is not None:
        if event.keysym in ("Return", "Tab") and valid_player:
            prompt_equipment_id(player_id)
        if event.keysym == "Tab":
            event.widget.tk_focusNext().focus()

@with_sound
def view_all_players(event=None):
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

@with_sound
def play_tutorial(event=None):
    pygame.mixer.music.fadeout(3000)
    countdown_win = tk.Toplevel()
    countdown_win.title("Tutorial Loading")
    countdown_win.protocol("WM_DELETE_WINDOW", lambda: None)

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
    video_win = tk.Toplevel()
    video_win.title("Tutorial")
    desired_width = 800
    desired_height = 600
    screen_width = video_win.winfo_screenwidth()
    screen_height = video_win.winfo_screenheight()
    x = (screen_width - desired_width) // 2
    y = (screen_height - desired_height) // 2
    video_win.geometry(f"{desired_width}x{desired_height}+{x}+{y}")
    video_win.attributes("-topmost", True)

    video_frame = tk.Frame(video_win)
    video_frame.pack(fill="both", expand=True)

    instance = vlc.Instance(["--no-xlib", "--quiet", "--quiet-synchro", "--no-video-title-show"])
    player = instance.media_player_new()
    media = instance.media_new("tutorial.mp4")
    player.set_media(media)

    video_win.update_idletasks()
    win_id = video_frame.winfo_id()
    import platform
    if platform.system() == "Windows":
        player.set_hwnd(win_id)
    else:
        player.set_xwindow(win_id)

    video_win.after(100, player.play)

    def on_close():
        player.stop()
        video_win.destroy()
        pygame.mixer.music.play(-1)
    video_win.protocol("WM_DELETE_WINDOW", on_close)

    def on_key(event):
        answer = sound_askyesno("Skip Tutorial", "Do you want to skip the tutorial?", parent=video_win)
        if answer:
            on_close()
        else:
            video_win.lift()
        return "break"
    video_win.bind("<Key>", on_key)

    def check_video():
        state = player.get_state()
        if state in [vlc.State.Ended, vlc.State.Stopped]:
            on_close()
        else:
            video_win.after(1000, check_video)
    check_video()

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
    pygame.mixer.music.play(-1)

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

splash = tk.Tk()
splash.title("Splash Screen")
splash.geometry("600x400")
splash.configure(bg="black")

from PIL import Image
logo_image = Image.open("logo.jpg")
logo_image = logo_image.resize((600, 400), Image.Resampling.LANCZOS)
logo = ImageTk.PhotoImage(logo_image)

tk.Label(splash, image=logo, bg="black").pack(expand=True, fill="both")

splash.after(4000, showPlayerEntry)
splash.mainloop()

def minimize_window():
    root.iconify()

def toggle_fullscreen():
    state = root.attributes('-fullscreen')
    root.attributes('-fullscreen', not state)

def close_window():
    root.destroy()

@with_sound
def start_game(event=None):
    print("F3: Starting game!")
    red_has_player = any(
        entry_id.get().strip() != ""
        for idx, (entry_id, _) in enumerate(player_entries)
        if idx % 2 == 0
    )
    green_has_player = any(
        entry_id.get().strip() != ""
        for idx, (entry_id, _) in enumerate(player_entries)
        if idx % 2 == 1
    )
    if not red_has_player or not green_has_player:
        sound_showwarning("Incomplete Team", "Each team must have at least one player before starting the game.")
        return

    pygame.mixer.music.fadeout(30000)

    red_players = [
        (eid.get().strip(), ename.get().strip())
        for idx, (eid, ename) in enumerate(player_entries)
        if idx % 2 == 0 and eid.get().strip() != ""
    ]
    green_players = [
        (eid.get().strip(), ename.get().strip())
        for idx, (eid, ename) in enumerate(player_entries)
        if idx % 2 == 1 and eid.get().strip() != ""
    ]

    global game_window
    game_window = tk.Toplevel(root)
    game_window.title("Play Action Screen")

    global red_frame_game, green_frame_game
    red_frame_game = tk.Frame(game_window, bg="darkred", padx=10, pady=10)
    red_frame_game.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    green_frame_game = tk.Frame(game_window, bg="darkgreen", padx=10, pady=10)
    green_frame_game.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    global red_team_score_label, green_team_score_label
    red_team_score_label = tk.Label(
        red_frame_game,
        text="RED TEAM (Score: 0)",
        bg="darkred",
        fg="white",
        font=("Arial", 14, "bold")
    )
    red_team_score_label.pack(pady=5)

    for pid, codename in red_players:
        player_text = f"ID: {pid} - {codename}"
        label = tk.Label(red_frame_game, text=player_text, bg="darkred", fg="white", font=("Arial", 12))
        label.pack(pady=2)
        base_hit_labels[pid] = label
        player_stats[pid] = {
            "team": "red",
            "codename": codename,
            "score": 0,
            "base_hits": 0,
            "label": label
        }

    green_team_score_label = tk.Label(
        green_frame_game,
        text="GREEN TEAM (Score: 0)",
        bg="darkgreen",
        fg="white",
        font=("Arial", 14, "bold")
    )
    green_team_score_label.pack(pady=5)

    for pid, codename in green_players:
        player_text = f"ID: {pid} - {codename}"
        label = tk.Label(green_frame_game, text=player_text, bg="darkgreen", fg="white", font=("Arial", 12))
        label.pack(pady=2)
        base_hit_labels[pid] = label
        player_stats[pid] = {
            "team": "green",
            "codename": codename,
            "score": 0,
            "base_hits": 0,
            "label": label
        }

    countdown_label = tk.Label(game_window, text="", font=("Arial", 24))
    countdown_label.pack(pady=20)

    log_frame = tk.Frame(game_window, bg="black")
    log_frame.pack(pady=10)

    log_scroll = tk.Scrollbar(log_frame)
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    global battle_log
    battle_log = tk.Text(log_frame, width=50, height=6, state="disabled", bg="white", yscrollcommand=log_scroll.set)
    battle_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_scroll.config(command=battle_log.yview)

    countdown_time = 30

    def start_game_flow():
        print("[DEBUG] start_game_flow() triggered")
        try:
            game_window.state('zoomed')
        except Exception:
            game_window.attributes('-zoomed', True)

        pygame.mixer.music.stop()

        track_list = [f"Track0{i}.mp3" for i in range(1, 9)]
        first_track = random.choice(track_list)
        last_track = [first_track]

        try:
            pygame.mixer.music.load(first_track)
            pygame.mixer.music.play()
            print(f"Now playing: {first_track}")
        except Exception as e:
            print(f"Error loading {first_track}: {e}")

        def music_loop_handler():
            try:
                if not pygame.mixer.music.get_busy():
                    next_track = random.choice([t for t in track_list if t != last_track[0]])
                    try:
                        pygame.mixer.music.load(next_track)
                        pygame.mixer.music.play()
                        print(f"Switched to: {next_track}")
                        last_track[0] = next_track
                    except Exception as e:
                        print(f"Error switching to {next_track}: {e}")
            except pygame.error as e:
                print("Music error:", e)
            root.after(1000, music_loop_handler)

        music_loop_handler()
        countdown_label.config(text="Get ready...")

        # Start blinking
        blink_leading_team()

        def start_gameplay_timer():
            print("[DEBUG] start_gameplay_timer() triggered")
            try:
                traffic_control_socket.sendto(b"202", traffic_generator_address)
                print("[DEBUG] Sent game start signal (202) to traffic generator.")
            except Exception as e:
                print(f"[ERROR] Failed to send game start signal: {e}")

            nonlocal countdown_label
            gameplay_time = 360

            def update_game_timer():
                nonlocal gameplay_time, countdown_label
                print(f"[DEBUG] Timer running: {gameplay_time} seconds remaining")
                countdown_label.config(text=f"Time remaining: {gameplay_time // 60}:{gameplay_time % 60:02d}")
                if gameplay_time > 0:
                    gameplay_time -= 1
                    game_window.after(1000, update_game_timer)
                else:
                    pygame.mixer.music.stop()
                    try:
                        pygame.mixer.music.load("Incoming.mp3")
                        pygame.mixer.music.play(-1)
                        print("Resuming main menu music")
                    except Exception as e:
                        print("Error loading main menu music:", e)

                    # Notify traffic generator
                    traffic_control_socket.sendto(b"221", traffic_generator_address)

                    # Show final scoreboard
                    show_final_scoreboard()

            update_game_timer()

        game_window.after(16000, start_gameplay_timer)

    def update_countdown():
        nonlocal countdown_time
        if countdown_time > 0:
            countdown_label.config(text=f"Map loading in {countdown_time}...")
            countdown_label.update_idletasks()
            countdown_time -= 1
            game_window.after(1000, update_countdown)
        else:
            countdown_label.config(text="Get ready...")
            game_window.after(1000, start_game_flow)

    update_countdown()

@with_sound
def clear_fields(event=None):
    print("F12: Clearing all fields!")
    for entry_id, entry_name in player_entries:
        entry_id.delete(0, tk.END)
        entry_name.delete(0, tk.END)

@with_sound
def quit_game(event=None):
    global stop_listener
    print("F7: Quitting game!")
    stop_listener = True
    try:
        for _ in range(3):
            traffic_control_socket.sendto(b"221", traffic_generator_address)
            time.sleep(0.01)
    except:
        pass

    udp_receive_socket.close()
    root.destroy()

@with_sound
def change_network(event=None):
    print("F8: Changing network!")
    try:
        with open("network_pin.txt", "r") as pin_file:
            expected_pin = pin_file.read().strip()
    except Exception as e:
        sound_showerror("PIN Error", f"Could not read network PIN file:\n{e}")
        return

    input_pin = tk.simpledialog.askstring("PIN Required", "Enter the network change PIN:")
    if input_pin is None or input_pin.strip() == "":
        sound_showwarning("PIN Required", "You must enter a PIN to proceed.")
        return

    if input_pin.strip() != expected_pin:
        sound_showerror("Invalid PIN", "The PIN you entered is incorrect.")
        return

    network_input = tk.simpledialog.askstring("New Network", "Please enter the new network:")
    if network_input is None or network_input.strip() == "":
        print("Network change cancelled!")
        return

    print(f"Network changed to {network_input.strip()}!")

def show_final_scoreboard():
    """
    Display the final scoreboard in a new Toplevel overlay.
    Keep the Play Action Screen open behind it.
    Provide an 'End Game' button that closes both.
    """
    scoreboard_win = tk.Toplevel(game_window)
    scoreboard_win.title("Final Scoreboard")
    scoreboard_win.geometry("800x600")

    tk.Label(
        scoreboard_win,
        text="Game Over! Final Results",
        font=("Arial", 16, "bold")
    ).pack(pady=10)

    red_total = 0
    green_total = 0
    for pid, stats in player_stats.items():
        if stats["team"] == "red":
            red_total += stats["score"]
        else:
            green_total += stats["score"]

    tk.Label(
        scoreboard_win,
        text=f"Red Team Final Score: {red_total}",
        font=("Arial", 14)
    ).pack(pady=5)

    tk.Label(
        scoreboard_win,
        text=f"Green Team Final Score: {green_total}",
        font=("Arial", 14)
    ).pack(pady=5)

    winning_team = None
    if red_total > green_total:
        winning_team = "red"
    elif green_total > red_total:
        winning_team = "green"

    text_area = tk.Text(scoreboard_win, width=40, height=8)
    text_area.pack(pady=5)

    text_area.insert(tk.END, "Final Player Stats:\n\n")
    for pid, stats in player_stats.items():
        text_area.insert(
            tk.END,
            f"Player {pid} ({stats['codename']}) => "
            f"Score: {stats['score']} | BH: {stats['base_hits']}\n"
        )
    text_area.config(state=tk.DISABLED)

    mvw_pid = None
    mvw_value = float("-inf")

    if winning_team:
        for pid, stats in player_stats.items():
            if stats["team"] == winning_team:
                value = stats["score"] + stats["base_hits"]
                if value > mvw_value:
                    mvw_value = value
                    mvw_pid = pid

    mvw_label = tk.Label(scoreboard_win, text="", font=("Arial", 12, "bold"))
    mvw_label.pack(pady=10)

    if not winning_team:
        mvw_label.config(text="It's a tie! No single winning team to pick MVP from.")
    else:
        if mvw_pid:
            mvw_label.config(
                text=f"Most Valuable Warrior (Winning Team): "
                     f"Player {mvw_pid} ({player_stats[mvw_pid]['codename']}) "
                     f"with Score+BH = {mvw_value}"
            )
        else:
            mvw_label.config(text="Winning Team found, but no MVP found?")

    def end_game():
        # 🆕 Cancel blinking job so we don't call config on destroyed labels
        global blink_job_id
        if blink_job_id:
            root.after_cancel(blink_job_id)

        scoreboard_win.destroy()
        game_window.destroy()
        root.deiconify()

    tk.Button(scoreboard_win, text="End Game", font=("Arial", 12, "bold"), command=end_game).pack(pady=15)

root = tk.Tk()
root.title("Player Entry Terminal")
root.geometry("900x600")
root.attributes('-fullscreen', True)

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

try:
    from PIL import Image
    logo_img = Image.open("logo.jpg")
    logo_img = logo_img.resize((200, 150), Image.Resampling.LANCZOS)
    logo_img = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(root, image=logo_img, bg="black")
    logo_label.place(relx=0.5, rely=0.3, anchor="center")
except Exception as e:
    print("Logo image error:", e)

red_frame = tk.Frame(root, bg="darkred", padx=10, pady=10)
red_frame.place(relx=0.25, rely=0.3, anchor="center")
green_frame = tk.Frame(root, bg="darkgreen", padx=10, pady=10)
green_frame.place(relx=0.75, rely=0.3, anchor="center")

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
    ("F8 Change Network", "F8"),
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
    "F7": quit_game,
    "F8": change_network
}

for i, (text, key) in enumerate(buttons):
    if key in key_action_map:
        action_command = with_sound(key_action_map[key])
    else:
        action_command = lambda text=text: print(f'Button {text} clicked!')
    tk.Button(button_frame, text=text, font=("Arial", 10), width=15,
              bg="gray", fg="white", command=action_command).grid(row=0, column=i, padx=5, pady=5)

root.mainloop()
