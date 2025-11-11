# Rogue Force

Rogue Force is a tactical battle game inspired by the Sega Saturn classic *Dragon Force*, reimagined with 2D pixel art sprites and strategic turn-based combat. The project has been migrated from a terminal-based (tcod) engine to a graphical one using **Pygame**.

Development is focused on enhancing the core 1v1 battle system, with a functional AI opponent and network multiplayer support.

## How's the Gameplay?

The objective is to defeat the enemy general by reducing their HP to zero. Combat is a real-time-with-pause system where units act based on cooldowns and player commands. You control your general and issue commands to your army of minions.

- **Style**: Turn-based tactical combat with real-time elements.
- **Graphics**: 2D pixel art sprites.
- **Controls**: Keyboard and mouse.

## How to Run It

You will need Python 3 and the Pygame library.

1.  **Set up the environment:**
    ```bash
    # Create a virtual environment (optional but recommended)
    python3 -m venv env
    source env/bin/activate  # On Windows, use `env\Scripts\activate`

    # Install requirements
    pip install -r requirements.txt
    ```

2.  **Run the game:**
    -   **Single Player vs. AI:**
        ```bash
        # Play as the left side (Player 0)
        python battle.py 0

        # Play as the right side (Player 1)
        python battle.py 1
        ```
        Generals for both sides are chosen randomly at the start of each match.

    -   **Network Multiplayer:**
        Multiplayer requires one person to host a server.
        1.  **Host runs the server:**
            ```bash
            # The server listens on the given port and the next one (e.g., 8888 and 8889)
            python server.py 8888
            ```
        2.  **Player 1 (Left Side) connects:**
            ```bash
            python battle.py 0 <server_ip> 8888
            ```
        3.  **Player 2 (Right Side) connects:**
            ```bash
            python battle.py 1 <server_ip> 8889
            ```

## Controls

-   **Mouse Movement**: Aims skills and provides hover-over info.
-   **Right Mouse Click**: Place a flag on the battlefield. Your general will move towards it.

### Skill & Tactic Management
-   **Q, W, E, R, T, Y, U, I, O, P**: Use skills 1-10.
-   **SHIFT + (Q, W, E...)**: Preview the area of effect for a skill without using it.
-   **1-9**: Swap to a reserve general (when the swap cooldown is ready).
-   **Z, X, C, V, B, N, M**: Select a tactic for your minions.
-   **Spacebar**: Quickly switch between your current and previous tactic.
-   **S**: Stop all current actions (clears your general's movement flag).

## Available Generals

The game features several factions, each with unique generals possessing distinct skills and playstyles.

### DOTO Faction
| Sprite ID     | General         | Description               |
|---------------|-----------------|---------------------------|
| `pock`        | Pock            | A sky-blue wizard specializing in teleportation and magic orbs. |
| `rubock`      | Rubock          | A green-robed telekinetic who can steal enemy spells. |
| `bloodrotter` | Bloodrotter     | A fearsome warrior powered by blood, with rage-based mechanics. |
| `ox`          | Ox              | A massive, bulky berserker who can taunt enemies and counter their attacks. |

### WIZERDS Faction
| Sprite ID     | General         | Description               |
|---------------|-----------------|---------------------------|
| `starcall`    | Starcall        | A cyan cosmic mage who wields the power of stars, lightning, and black holes. |

### ORACLES Faction
| Sprite ID     | General         | Description               |
|---------------|-----------------|---------------------------|
| `gemekaa`     | Gemekaa         | A mysterious crimson oracle who can foresee enemy movements and call down lightning. |

### SAVIOURS Faction
| Sprite ID     | General         | Description               |
|---------------|-----------------|---------------------------|
| `ares`        | Ares            | A heroic red warrior who excels at close-quarters combat with powerful slash attacks. |

### MECHANICS Faction
| Sprite ID     | General         | Description               |
|---------------|-----------------|---------------------------|
| `flappy`      | Flappy          | A goblin engineer in green overalls who uses mechanical contraptions and explosives. |

## Can I help?
Probably. I appreciate most kinds of help, from code to game ideas for new generals or gameplay. Feel free to open new issues, fork the code or anything else that you might fancy.

**Acknowledgments**

This project is a fork and modernization of the original *Rogue Force* game, created by **Marcelino Alberdi Pereira** and **Jose Eulogio Cribeiro Aneiros**. Their foundational work, developed between 2012-2013, provided the core mechanics and inspiration for this version.

The original project is available on GitHub and is distributed under the permissive ISC license.

*   **Original Repository**: [https://github.com/Alberdi/rogueforce](https://github.com/Alberdi/rogueforce)

## License
The project uses the free ISC license as you can check in the `LICENSE.txt` file.