# LAST CHANCE HEROES

A simple tactical, turn-based strategy game.

## Requirements

You need python >= 3.8, scipy, and numpy. Should be cross-platform but only tested on linux.

## Installation

Run `python setup.py`

## How to play

Start a game by running `main.py`.
Your guys are in red, the enemies are in cyan.
The green are trees, you can't move or see through them.
Single-click to select one of your guys, this shows where he can move.
Single-click a square to select it for perusal.
Double-click on a square to move there, or an enemy to attack it.
If you've selected a square to move to before double-clicking the enemy you'll move and attack.
If you move adjacent to an enemy you can do a melee attack, otherwise you'll shoot with your gun.
When you move a dude, the enemy gets to move one of his dudes.
Once you've activated a dude he's done for the turn.
Once all your dudes are activated, hit the "end turn" button.

### Keep in mind

Your dudes aren't all created equally, and neither are their weapons.
For instance, pistols don't do much against thick armor, and heavy weapons don't work well if you're always running around.
Also, you've got to be really good with your knife if you're up against some dude with an axe.
Maybe axe him for some pointers after he's cut you down.

### Issues

The game doesn't know when you've won, I haven't written that bit yet; you can quit whenever you want and claim victory.
There are some bugs still.
There are no audio assets yet, or anything resembling actual art assets; feel free to provide me with some.
The AI is pretty dumb.
