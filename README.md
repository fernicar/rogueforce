Rogue Force
===========
Rogue Force is a reimagining of the Sega Saturn *Dragon Force* game set in space featuring roguelike graphics. The game is still in very early development with the focus put on the one on one battles, with a very crude version of the overworld view and other details for now. Not even the name is final.

What does it look like?
-----------------------
If the term *roguelike* didn't click in you, here is some hardcore action featuring a wizard minion attacking a mighty general:

    G...(...w

To be honest, that is more concept art than anything. Here is a real screenshot, if you prefer:

![Rogue Force](http://i.imgur.com/E9kDO.png)

How's the gameplay?
-------------------------
Currently? A bit clumsy. All the input is given through the keyboard, with the mouse position being used for some skills. The graphical interface doesn't help new players that much at the moment, so the best way to know what is what is by trial and error.

Does it feature network play?
-----------------------------
Yeah, you can play against your friends. You only need to run your own copy of the server included and connect to it following some obscure and poorly documented protocol. It'll run flawlessly! (At least if the both of you have good PCs that are really near to the server.) Even then, the hardest part, by far, is finding someone to play against.

How can I run it?
-----------------
You'll need to download all the files in this repository and install the requirements:

    python3 -m venv env
    source env/bin/activate
    pip3 install -r requirements.txt

After that, run `scenario.py` from the command line for the full experience or `battle.py` for a quick fight. The only one that supports network play at the moment is `battle.py`, you can try it with:

    python3 battle.py [0|1] {address port}

The first argument is the side on which you are playing (0 is left). The game features a dumb AI that does nothing, so you can try the game against it; just leave empty the last pair of parameters. If you want to play a networked game someone has to run the included server, `server.py`, as follows:

    python3 server.py port

It will launch a TCP server based on sockets on the port included and the next one (port+1). Then each player needs to connect to it in the proper order, first the one going in the port specified and then the other one. Here is an example of the workflow to play a single game of 60 seconds.

    marce:~$ python3 server.py 8888
    marce:~$ python3 battle.py 8888
     sito:~$ python3 battle.py 8889

To customize your experience, such as choosing different generals for each side, you'll to edit the last lines of `battle.py`; and remember to do it on both sides of the network if you want to play the same game. Maybe it's a bit cumbersome, but the `scenario.py` might support network play in the future too.

Rogue Force will have ready to play packages for each major system in the future, but they're not provided yet.

Can I help?
-----------
Probably. I appreciate most kinds of help, from code to game ideas for new generals or gameplay. Feel free to open new issues, fork the code or anything else that you might fancy.

License?
--------
The project uses the free ISC license as you can check in the `LICENSE.txt` file. I really dislike the all caps legal text that goes with every single software license so I decided to strip it.


# How to Play Rogue Force

Rogue Force is a tactical battle game inspired by Dragon Force, featuring ASCII-style graphics and turn-based strategic combat. Here's everything you need to know:

## Game Overview
- **Objective**: Defeat the enemy general by reducing their HP to zero
- **Style**: Turn-based tactical combat with roguelike ASCII graphics
- **Setting**: Space-themed battles with different factions and generals
- **Controls**: Keyboard + mouse (right-click for special actions)

## Starting the Game
```bash
python battle.py 0  # Play as Player 0 (left side) vs AI
python battle.py 1  # Play as Player 1 (right side) vs AI
```

## Interface Layout
- **Main Battlefield**: 60x43 grid in the center where units move and battle
- **Left/Right Panels**: Show your and enemy general's stats, skills, and reserves
- **Bottom Messages**: Combat log and feedback
- **Top Info**: Current tile info and general status

## Controls

### Skill Management
- **Q-W-E-R-T-Y-U-I-O-P**: Use skills 1-10
  - **Uppercase (Q)**: Preview skill area of effect (mouse position determines target)
  - **Lowercase (q)**: Actually use the skill at mouse position
- **1-9**: Swap to reserve units (when cooldown allows)

### Tactics
- **Z-C-V-B-N-M**: Use tactics 1-6
- **Spacebar**: Switch between current and previous tactic

### Actions
- **S**: Stop all current actions
- **Right Mouse Click**: Place flag/marker on battlefield
- **Mouse Movement**: Position affects skill targeting and shows hover effects

## Available Generals

### Doto Faction (Default)
1. **Pock** (Blue): Wizard with teleport and magic orb abilities
2. **Rubock** (Green): Telekinetic with spell stealing capabilities  
3. **Bloodrotter** (Red): Blood-powered fighter with rage mechanics
4. **Ox** (Dark Red): Berserker with taunt and counter-attack skills

### Wizerds Faction
- **Starcall** (Cyan): Cosmic powers with lightning and black hole abilities

## Gameplay Mechanics

### Combat System
- Each general has HP, power, armor, and unique skills
- Skills have cooldowns and various effects (damage, healing, status effects)
- Minions can be summoned and controlled
- Turn-based system with action queues

### Status Effects
- **Buffs**: Empowerment, shielding, speed increases
- **Debuffs**: Poison, weakness, silence, stun
- **Armor**: Physical and magical damage reduction

### Skill Types
- **Single Target**: Damage/heal one enemy/ally
- **Area Effects**: Damage/heal in radius around target
- **Summons**: Create entities like magic orbs
- **Status Effects**: Apply temporary conditions

### Reserves System
- Multiple generals available per side
- Swap between active general and reserves (limited by cooldown)
- Each reserve has unique abilities and stats

## Strategy Tips
1. **Skill Management**: Balance offensive and defensive abilities
2. **Positioning**: Use area effects strategically
3. **Cooldown Timing**: Plan skill usage around cooldowns
4. **Resource Management**: Monitor HP and power levels
5. **Reserve Timing**: Use swaps for tactical advantages

## Network Multiplayer
For multiplayer battles:
1. Start server: `python server.py [port]`
2. Player 1: `python battle.py 0 [server_address] [port]`
3. Player 2: `python battle.py 1 [server_address] [port+1]`

The game is still in early development with limited AI, so expect some rough edges but enjoy the strategic depth!