<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/maddydou/SE">
    <img src="logo.jpg" alt="Logo" width="520" height="360">
  </a>

# Laser Tag Game Interface

## About

This project provides an interface for a laser tag game, allowing users to enter player information for two teams and then transition to the game progress (play action) screen.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

</div>

### Built with

![Python](https://img.shields.io/badge/python-3.9-blue)
![Tkinter](https://img.shields.io/badge/Tkinter-8.6-green)
![psycopg2](https://img.shields.io/badge/psycopg2-2.8.6-yellow)


### Features

- **Player Input Screen:**
  - Two teams: Red and Green.
  - Enter player IDs; the corresponding player codename is automatically retrieved from a PostgreSQL database.
  - Use the **Tab** key to move between input fields.
  
- **Keyboard Shortcuts:**
  - **F3**: Validates that each team has at least one player and then moves to the play action screen.
  - **F12**: Clears all player input fields.
  - **F7**: Quits the game interface.

- **Play Action Screen:**
  - Opens as a new window when F3 is pressed (provided that both teams have at least one player).
  - Acts as a placeholder for further game progress functionality (to be developed by another team member).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

- **Python 3.x**
- **Tkinter:** Usually included with Python installations.
- **Psycopg2:** PostgreSQL adapter for Python. Install using:
  ```bash
  pip install psycopg2-binary
  
<p align="right">(<a href="#readme-top">back to top</a>)</p>
