                      PHOTON
         The Ultimate Game on Planet Earth
-----------------------------------------------------
             Laser Tag Game Interface


-----
About

This project provides an interface for PHOTON, the original Laser Tag game, allowing users to enter player information for two teams and then transition to the game progress (play action) screen.

Built with
   Python 3 	(https://www.python.org/)
   Tkinter	(https://docs.python.org/3/library/tkinter.html)
   psycopg2	(https://www.psycopg.org/docs/)
   Pillow	(https://github.com/python-pillow/Pillow)
   pygame       (https://www.pygame.org/)
   python-vlc   (https://pypi.org/project/python-vlc/)

Features
	Player Input Screen:
		Two teams: Red and Green.
		Enter player IDs; the corresponding player codename is automatically retrieved from a PostgreSQL database.
		Use the Tab key to move between input fields.

	Keyboard Shortcuts:
		F3: Validates that each team has at least one player and then moves to the play action screen.
		F12: Clears all player input fields.
		F7: Quits the game interface.
	
	Play Action Screen:
		Opens as a new window when F3 is pressed (provided that both teams have at least one player).
		Acts as a placeholder for further game progress functionality (to be developed by another team member).

UDP Communication
	python_udpclient.py:
		This file now contains the UDP client functionality. It defines the function send_equipment_id(equip_id, server_address=("127.0.0.1", 7500)) for sending equipment IDs via UDP. A test loop is included under an if __name__ == "__main__": block so that when imported by the GUI code, only the function is used.
	python_udpserver.py:
		A UDP server that listens for messages on port 7500 and responds (simulating game state communication).


---------------
Getting Started

Requirements
	Python 3.x
	Tkinter: Usually included with Python installations.
	Pillow: For image handling
	Psycopg2: PostgreSQL adapter for Python.
	PostgreSQL
        Pygame: For music handling
	Python-vlc: For video handling

Installation
	1: Clone the repo
		git clone https://github.com/maddydou/SE.git
		cd SE

	2: Ensure login details in player_entry.py are correctly configured (Should be fine on Photon VM)

	3: Ensure dependencies are installed
		pip install psycopg2-binary Pillow
		pip install pygame
		pip install python-vlc

	4: Tkinter is usually bundled with Python 3 installations, but on certain operating systems, notably Debian-based systems (Ubuntu, Arch, Fedora, SUSE), you may need to install this component separately with:
		sudo apt-get install python3-tk

	5: For additional VLC support, make sure that the VLC media player (and its libraries) is installed on your system. On Ubuntu, for example, you might run:
		sudo apt-get update && sudo apt-get install vlc libvlc-dev


-----
Usage

Player Entry Interface
	Run the main application
		python3 player_entry.py

UDP Communication (These processes should start automatically when running player_entry.py)
	Open two separate terminal windows
	Start UDP Server in one window
		python3 python_udpserver.py

	Start UDP Client in other window
		python3 python_udpclient.py

	Follow the prompts in the UDP client to send equipment codes or control to the program.

	If the processes are opened by player_entry.py and the entry screen process terminates, the user may need to manually terminate the UDP processes.

Database
	Create a database named photon with a table called players having at least the following columns:
		sql CREATE TABLE players ( id INTEGER PRIMARY KEY, codename TEXT );

	Optionally, insert a test record:
		sql INSERT INTO players (id, codename) VALUES (1, 'Opus');


-----------------
Project Structure

player_entry.py: Contains the splash screen and the player entry GUI. It integrates database operations (retrieving, adding, and updating players) and provides the main interface for entering player data.
python_udpclient.py: Implements a UDP client that sends messages (equipment codes) to the server and supports commands for starting/stopping the game and switching networks.
python_udpserver.py: Implements a UDP server that listens for incoming messages and simulates game state responses.
background.png: Background image used for the player entry screen.
logo.jpg: Logo image displayed on the splash screen.
README.md: This file.



------------
Contributors - Name (GitHub Username)
	
	Adam Montano	(adam4475)
	Zebulun Jenkins	(zubEjankins)
	Madison Dou	(maddydou)
	Chase Haskell	(chase-Haskell)
	Joey Leder	(JoeyLeder)


----------------
Additional Notes

The server will automatically close when if the client is unable to communicate with it, such as if there is a change to the network.

The project demonstrates full CRUD operations on the players table:
	Retrieving player information.
	Adding a new player when a player ID is not found.
	Updating an existing player's codename.

The UDP modules simulate equipment code transmissions and can be extended for full game integration.
The code is modular to facilitate collaboration among team members.
For any issues or further enhancements, please refer to our Slack channel or contact the team.


-------
License

This project is licensed under the MIT License.

Repository: https://github.com/maddydou/SE/





