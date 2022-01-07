import lch
import random
import numpy as np


def reset_cache(hard=False):
    tables = 'ai model weapon team'.split()
    if hard:
        for table in tables:
            lch.db_conn.execute(f'DROP TABLE {table};')
    else:
        for table in tables:
            lch.db_conn.execute(f'DELETE * FROM {table};')
weps = [
        #(hash, name, class, range, attacks, punch, min damage, max damage)
        ('bb5d1b', 'none', 'Weapon', 0, 0, 0, 0, 0),
        ('1a9043', 'rifle', 'Rifle', 12, 2, 2, 2, 4),
        ('31dc11', 'mg', 'MG', 12, 4, 2, 3, 5),
        ('3c7434', 'smg', 'SMG', 8, 3, 0, 2, 3),
        ('06eba5', 'shotgun', 'Shotgun', 6, 3, 1, 2, 4),
        ('89a4b9', 'pistol', 'Pistol', 6, 1, 0, 1, 3),
        ('f00cd8', 'sniper', 'Sniper', 12, 1, 6, 3, 5),
        ('08e894', 'knife', 'Knife', 0, 1, 0, 2, 4),
        ('faa427', 'sword', 'Sword', 0, 2, 1, 3, 5),
        ('d04ab4', 'axe', 'Axe', 0, 2, 2, 3, 5),
        # note the hashes were added later
        ]

def setup_weapons():
    try:
        lch.Weapon.create_table(lch.db_conn)
    except sql.OperationalError:
        print('Table exists')
    for wep in weps:
        w = lch.Weapon.from_tuple(wep)
        print(w.name, w.hash)
        lch.store_in_cache('weapon', w.encode())

def setup_models():
    try:
        lch.Model.create_table(lch.db_conn)
    except sql.OperationalError:
        print('Table exists')
    def model():
        return (random.randint(4,7), # move
                random.randint(50,75), # rs
                random.randint(10,25), # rc
                random.randint(50,75), # ms
                random.randint(10,25), # mc
                random.randint(4,8), # max health
                random.randint(50,75), # dodge
                random.randint(1,4) # armor
                )
    mods = [
            model() for _ in range(6)
            ]
    for mod in mods:
        m = lch.Model.from_tuple((None, *mod))
        print(m.hash)
        lch.store_in_cache('model', m.encode())

model_hashes = 'eb03ac ef1859 cf2722 0bcae4 fa6fe1 3078b4'.split()

def setup_ais():
    try:
        lch.AI.create_table(lch.db_conn)
    except sql.OperationalError:
        #print('Table exists')
        pass
    ai = lch.DenseMultilayer.from_scratch()
    try:
        lch.store_in_cache('ai', ai.encode())
    except:
        # why do I need this try-except?
        pass
    return ai.hash

def setup_teams():
    def make_team(n):
        t = [None]
        for i,j in enumerate(np.random.choice(6, size=6, replace=False)):
            t += [model_hashes[j], f'T{n}M{i}', weps[random.randint(7,9)][0], weps[i+1][0]]
        return tuple(t)
    try:
        lch.Team.create_table(lch.db_conn)
    except sql.OperationalError:
        #print('Table exists')
        pass

    for t in [make_team(0), make_team(1)]:
        print(t)
        team = lch.Team.from_tuple(t)
        print(team.hash)
        lch.store_in_cache('team', team.encode())
    return
