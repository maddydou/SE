<a id="readme-top"></a>
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
        <li><a href="#features">Features</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#requirements">Requirements</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#contributors">Contributors</a></li>
  </ol>
</details>


<br />
<div align="center">
  <a href="https://github.com/maddydou/SE">
    <img src="logo.jpg" alt="Logo" width="520" height="360">
  </a>

# Laser Tag Game Interface
</div>

## About

This project provides an interface for a laser tag game, allowing users to enter player information for two teams and then transition to the game progress (play action) screen.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built with

* ![Python](https://img.shields.io/badge/python-3.x-blue)
* ![Tkinter](https://img.shields.io/badge/Tkinter-green)
* ![psycopg2](https://img.shields.io/badge/psycopg2-yellow)

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

### Requirements

- **Python 3.x**
- **Tkinter:** Usually included with Python installations.
- **Psycopg2:** PostgreSQL adapter for Python. Install using:
  ```bash
  pip install psycopg2-binary

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/maddydou/SE.git
   ```
2. Ensure login details in player_entry.py are correctly configured
3. Execute the playerentry.py script:
   ```sh
   python playerentry.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Contributors

| Contributor      | Username      |
| ---------------- | ------------- |
| Adam Montano     | adam4475      |
| Zebulun Jenkins  | zubEjankins   |
| Madison Dou      | maddydou      |
| Chase Haskell    | chase-haskell |
| Joey Leder       | JoeyLeder     |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

