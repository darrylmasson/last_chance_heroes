import lch

NoRangedWeaponHash = 'bb5d1b'

class Model(object):
    """
    """
    def __init__(self, move=None, rs=None, rc=None, ms=None, mc=None, dodge=None,
            max_health=None, mw=None, armor=None, pos_x=-1, pos_y=-1, status=None,
            rw=None, current_health=None, team=None, _hash=None):
        self.move = move
        self.rs = rs
        self.rc = rs
        self.ms = ms
        self.mc = mc
        self.max_health = max_health
        self.current_health = current_health or max_health
        self.mw = mw
        self.rw = rw
        self.dodge = dodge
        self.position = (pos_x, pos_y)
        self.status = status or 'ready'
        self.armor = armor
        self.team = team
        self.hash = _hash or lch.get_hash(*map(lambda s : str(s).encode(), self.skills))
        self.game_hash = self.hash # store separately for reasons

    def __str__(self):
        return f'{self.hash}, pos {self.position}, status {self.status}'

    def __eq__(self, rhs):
        return self.hash == rhs.hash

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

    def get_snapshot(self):
        return (self.game_hash, self.current_health, self.status, *self.position)

    def load_snapshot(self, snap):
        _, self.current_health, self.status, x, y = snap
        self.position = (x,y)

    def generate_actions(self, friendly_occupied, enemies, bf):
        if self.status != 'ready':
            return []
        self.logger.trace(f'Generating actions for {self}')
        enemy_positions = enemies.positions()
        enemy_adjacent = bf.adjacent(enemy_positions)
        occupied = friendly_occupied | enemy_positions

        actions = []
        action_kwargs = self.evaluate_position(None, enemies, bf, occupied)
        # first, are we in combat already?
        if self.position in enemy_adjacent:
            for enemy in enemies:
                if self.position in bf.adjacent(enemy.position):
                    actions.append(lch.MeleeAction(model=self, target=enemy, **action_kwargs))
            return actions

        # second, shoot without moving
        if self.rw.hash != NoRangedWeaponHash:
            for e in enemies:
                dist, obs = bf.los_range(self.position, e.position)
                if dist < self.rw.range:
                    actions.append(lch.ShootAction(model=self, target=e, obstruction=obs, **action_kwargs))

        # move and handle actions
        for pos in bf.reachable(self.position, self.move, occupied):
            action_kwargs = self.evaluate_position(pos, enemies, bf, occupied)
            if pos in enemy_adjacent:
                for enemy in enemies:
                    if enemy.position == pos:
                        actions.append(lch.ChargeAction(model=self, target=enemy, move_destination=pos, **action_kwargs))
            else:
                actions.append(lch.MoveAction(model=self, target=None, move_destination=pos, **action_kwargs))
                if self.rw.hash != NoRangedWeaponHash:
                    # NoRangedWeapon hash
                    for e in enemies:
                        dist, obs = bf.los_range(pos, e.position)
                        if dist <= self.rw.range:
                            actions.append(lch.SnapShotAction(model=self, target=e, move_destination=pos, obstruction=obs, **action_kwargs))

        return actions

    def evaluate_position(self, position, enemies, bf, occupied):
        """
        Location-based kwargs for actions
        :param position: (x,y) tuple, position of model if not current
        :param enemies: list of enemy models
        :param bf: battlefield
        :returns: dict of kwargs for Action
        """
        ret = {'shootable_targets': 0, 'chargeable_targets': 0,
                'can_shoot_back': 0, 'can_charge_back': 0}
        position = position or self.position
        for enemy in enemies:
            los_dist, obstruction = bf.los_range(position, enemy.position)
            if self.rw.range >= los_dist:
                ret['shootable_targets'] += 1
            if enemy.rw.range >= los_dist:
                ret['can_shoot_back'] += 1
            _, dist = bf.astar_path(position, enemy.position, max(self.move, enemy.move), occupied)
            if dist != -1 and self.move >= dist:
                ret['chargeable_targets'] += 1
            if dist != -1 and enemy.move >= dist:
                ret['can_charge_back'] += 1
        return ret
