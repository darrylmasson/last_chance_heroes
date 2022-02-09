import lch
from random import randint


NoRangedWeaponHash = 'bb5d1b'

class Model(object):
    """
    """
    def __init__(self, move=None, rs=None, rc=None, ms=None, mc=None, dodge=None,
            max_health=None, mw=None, armor=None, pos_x=-1, pos_y=-1, status=None,
            rw=None, current_health=None, team=None, _hash=None):
        self.move = move
        self.rs = rs
        self.rc = rc
        self.ms = ms
        self.mc = mc
        self.max_health = max_health
        self.current_health = current_health or max_health
        self.mw = mw
        self.rw = rw
        self.dodge = dodge
        self.coords = (pos_x, pos_y)
        self.status = status or 'ready'
        self.armor = armor
        self.team = team
        self.hash = _hash or lch.get_hash(*map(lambda s : str(s).encode(), self.skills))
        self.game_hash = self.hash # store separately for reasons

    def __str__(self):
        return f'self.name'

    def __eq__(self, rhs):
        return self.hash == rhs.hash

    @property
    def threat(self):
        """
        Properties that go into the threat assessment. Basically skills but current
        instead of max health and normalized
        """
        return (self.move * 0.1, self.rs * 0.01, self.rc * 0.05, self.ms * 0.01,
                self.mc * 0.05, self.current_health * 0.1, self.dodge * 0.01,
                self.armor * 0.1)

    @staticmethod
    def create_table(conn):
        """
        Create the appropriate table in the provided database
        """
        try:
            conn.execute("""CREATE TABLE model (
                hash TEXT PRIMARY KEY NOT NULL,
                move INTEGER,
                rs INTEGER,
                rc INTEGER,
                ms INTEGER,
                mc INTEGER,
                max_health INTEGER,
                dodge INTEGER,
                armor INTEGER);""")
        except Exception as e:
            pass

    @property
    def skills(self):
        return (self.move, self.rs, self.rc, self.ms, self.mc, self.max_health, 
                self.dodge, self.armor)

    def encode(self):
        """
        Returns a db-serializable tuple
        """
        return (self.hash, *self.skills)

    @classmethod
    def from_hash(cls, _hash):
        args = lch.load_from_cache('model', _hash)
        return cls.from_tuple(args)

    @classmethod
    def from_tuple(cls, args):
        """
        The reverse of encode
        """
        _hash, move, rs, rc, ms, mc, max_health, dodge, armor = args
        return cls(_hash=_hash, move=move, rs=rs, ms=ms, rc=rc, mc=mc,
                max_health=max_health, dodge=dodge, armor=armor)

    @classmethod
    def random_new(cls):
        return cls(
                move = randint(4,7),
                rs = randint(50,75),
                rc = randint(10,25),
                ms = randint(50,75),
                mc = randint(10,25),
                max_health = randint(5,8),
                dodge = randint(40,60),
                armor = randint(1,4)
                )

    @property
    def health(self):
        return f'{self.current_health}/{self.max_health}'

    def get_snapshot(self):
        return (self.game_hash, self.current_health, self.status, *self.coords)

    def load_snapshot(self, snap):
        _, self.current_health, self.status, x, y = snap
        self.coords = (x,y)

    def text_status(self):
        s = f'{self.name}  | {self.status}  | move {self.move}  | rs {self.rs}  |'\
                f' rc {self.rc}  | ms {self.ms}  | mc {self.mc}  |'\
                f' dodge {self.dodge}  | armor {self.armor}  |'\
                f' health {self.current_health}/{self.max_health}  |'\
                f' {self.mw.name}, {self.rw.name}'
        return s

    def generate_actions(self, friendly_occupied, enemies, bf):
        if self.status != 'ready':
            return []
        self.logger.trace(f'Generating actions for {self}')
        enemy_coords = enemies.coordinates()
        enemy_adjacent = bf.adjacent(enemy_coords)
        occupied = friendly_occupied | enemy_coords

        actions = []
        action_kwargs = self.evaluate_coords(None, enemies, bf, occupied)
        # first, are we in combat already?
        if self.coords in enemy_adjacent:
            for enemy in enemies:
                if self.coords in bf.adjacent(enemy.coords):
                    actions.append(lch.MeleeAction(model=self, target=enemy, **action_kwargs))
            return actions

        # second, shoot without moving
        if self.rw.hash != NoRangedWeaponHash:
            for e in enemies:
                dist, obs = bf.los_range(self.coords, e.coords)
                if dist < self.rw.range:
                    actions.append(lch.ShootAction(model=self, target=e, obstruction=obs, **action_kwargs))

        # move and handle actions
        for pos in bf.reachable(self.coords, self.move, occupied):
            action_kwargs = self.evaluate_coords(pos, enemies, bf, occupied)
            if pos in enemy_adjacent:
                for enemy in enemies:
                    if enemy.coords == pos:
                        actions.append(lch.ChargeAction(model=self, target=enemy, move_dest=pos, **action_kwargs))
            else:
                actions.append(lch.MoveAction(model=self, target=None, move_dest=pos, **action_kwargs))
                if self.rw.hash != NoRangedWeaponHash and not isinstance(self.rw, lch.HeavyWeapon):
                    for e in enemies:
                        dist, obs = bf.los_range(pos, e.coords)
                        if dist <= self.rw.range:
                            actions.append(lch.SnapShotAction(model=self, target=e, move_dest=pos, obstruction=obs, **action_kwargs))

        return actions

    def evaluate_coords(self, coords, enemies, bf, occupied):
        """
        Location-based kwargs for actions
        :param coords: (x,y) tuple, coords of model if not current
        :param enemies: list of enemy models
        :param bf: battlefield
        :returns: dict of kwargs for Action
        """
        ret = {'shootable_targets': 0, 'chargeable_targets': 0,
                'can_shoot_back': 0, 'can_charge_back': 0, 'bf': bf}
        coords = coords or self.coords
        for enemy in enemies:
            if enemy.status == 'dead':
                continue
            los_dist, obstruction = bf.los_range(coords, enemy.coords)
            if self.rw.range >= los_dist:
                ret['shootable_targets'] += 1
            if enemy.rw.range >= los_dist:
                ret['can_shoot_back'] += 1
            _, dist = bf.astar_path(coords, enemy.coords, max(self.move, enemy.move), occupied)
            if dist != -1 and self.move >= dist:
                ret['chargeable_targets'] += 1
            if dist != -1 and enemy.move >= dist:
                ret['can_charge_back'] += 1
        return ret
