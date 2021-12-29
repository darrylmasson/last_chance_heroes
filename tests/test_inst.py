import lch
import sqlite3 as sql


def setup_weapons():
    try:
        lch.Weapon.create_table(sql.connect('cache.db'))
    except sql.OperationalError:
        print('Table exists')
    weps = [
            #(hash, name, class, range, attacks, punch, min damage, max damage)
            ('bb5d1b', 'none', 'Weapon', 0, 0, 0, 0, 0),
            ('1a9043', 'test rifle', 'Rifle', 18, 1, 0, 2, 4),
            ('31dc11', 'test heavy', 'MG', 24, 3, 1, 3, 5),
            ('3c7434', 'test smg', 'SMG', 12, 2, 0, 3, 4),
            ('06eba5', 'test shotgun', 'Shotgun', 12, 3, 1, 3, 4),
            ('89a4b9', 'test pistol', 'Pistol', 8, 2, 0, 2, 3),
            ('f00cd8', 'test sniper', 'Sniper', 36, 1, 3, 4, 5),
            ('08e894', 'test knife', 'Knife', 0, 1, 0, 2, 3),
            ('faa427', 'test sword', 'Sword', 0, 2, 0, 3, 4),
            ('d04ab4', 'test axe', 'Axe', 0, 3, 0, 3, 5),
            # note the hashes were added later
            ]
    for wep in weps:
        w = lch.Weapon.from_tuple(wep)
        print(w.name, w.hash)
        lch.store_in_cache('weapon', w.hash, w.encode())

def setup_models():
    try:
        lch.Model.create_table(sql.connect('cache.db'))
    except sql.OperationalError:
        print('Table exists')
    mods = [
            #hash, move, rs, rc, ms, mc, max_health, dodge, armor
            ('f60fbd', 6, 55, 15, 45, 15, 6, 50, 2),
            ]
    for mod in mods:
        m = lch.Model.from_tuple(mod)
        print(m.hash)
        lch.store_in_cache('model', m.hash, m.encode())

def setup_ais():
    try:
        lch.AI.create_table(sql.connect('cache.db'))
    except sql.OperationalError:
        #print('Table exists')
        pass
    ai = lch.SimpleAI.from_scratch()
    lch.store_in_cache('ai', ai.hash, ai.encode())
    return ai.hash

def setup_teams(num):
    def model(t,i):
        # model hash (test model), name, melee hash (knife), ranged hash (rifle)
        return ('f60fbd', f'T{t}M{i}', '08e894', '1a9043')
    try:
        lch.Team.create_table(sql.connect('cache.db'))
    except sql.OperationalError:
        #print('Table exists')
        pass
    teams = [
            # hash, ai_hash, [model hash, name, melee hash, ranged hash]+
            (None, *model(i+1, 1), *model(i+1, 2), *model(i+1, 3), *model(i+1, 4))
            for i in range(num)
            ]
    ret = []
    for t in teams:
        team = lch.Team.from_tuple(t)
        #print(t.hash)
        ret.append(team.hash)
        lch.store_in_cache('team', team.hash, team.encode())
    return ret
