import lch
import typing as ty
import random
from enum import IntEnum

__all__ = 'Weapon RangedWeapon MeleeWeapon AssaultWeapon HeavyWeapon Pistol SMG Shotgun Rifle MG Sniper Knife Sword Axe'.split()

class WeaponCategory(IntEnum):
    none = 0
    assault = 1
    heavy = 2
    melee = 3

class Weapon(object):
    """
    """
    category = 'none'
    def __init__(self, name, _range=1, attacks=1, punch=0, min_damage=0, max_damage=0, _hash=None, owner=None):
        self.name = name
        self.range = _range
        self.attacks = attacks
        self.punch = punch
        self.min_damage = min_damage
        self.max_damage = max_damage
        self.owner = owner
        self.hash = _hash or lch.get_hash(*map(str, self.stats))

    def __str__(self):
        return f'{self.name} ({self.range}/{self.attacks}/{self.punch})'

    def __eq__(self, rhs):
        return self.hash == rhs.hash

    @property
    def threat(self):
        """
        Properties that go into the threat assessment, normalized
        """
        raise NotImplementedError()

    @staticmethod
    def create_table(conn):
        """
        Creates the appropriate table in the provided database
        """
        try:
            conn.execute("""CREATE TABLE weapon (
                hash TEXT PRIMARY KEY NOT NULL,
                name TEXT,
                type TEXT,
                range INTEGER,
                attacks INTEGER,
                punch INTEGER,
                min_damage INTEGER,
                max_damage INTEGER);""")
        except Exception as e:
            pass

    @staticmethod
    def from_hash(_hash):
        """
        Takes a hash, returns a Weapon
        """
        args = lch.load_from_cache('weapon', _hash)
        cls = getattr(lch, args[2])
        _, name, _, _range, attacks, punch, min_damage, max_damage = args
        return cls(name=name, _range=_range, attacks=attacks, punch=punch,
                min_damage=min_damage, max_damage=max_damage, _hash=_hash)

    @staticmethod
    def from_tuple(x):
        _hash, name, cls_name, _range, attacks, punch, min_damage, max_damage = x
        return getattr(lch, cls_name)(name=name, _range=_range, attacks=attacks,
                punch=punch, min_damage=min_damage, max_damage=max_damage, _hash=_hash)

    @property
    def stats(self):
        return (self.range, self.attacks, self.punch, self.category,
                self.min_damage, self.max_damage)

    def encode(self):
        return (self.hash, self.name, self.__class__.__name__, self.range,
                self.attacks, self.punch, self.min_damage, self.max_damage)

    @property
    def avg_damage(self):
        return 0.5*sum(self.min_damage, self.max_damage)

    def damage(self):
        return random.randint(self.min_damage, self.max_damage)

class MeleeWeapon(Weapon):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.range = 0

    def chance_to_hit(self, target, bf):
        if self.owner.position not in bf.adjacent(target.position):
            return 0.
        return 0.5

    @property
    def threat(self):
        return (self.attacks * 0.33, self.punch * 0.1,
                self.min_damage * 0.2, self.max_damage * 0.1)


class RangedWeapon(Weapon):
    def penalty(self, move_distance, shot_distance):
        """
        What is the penalty to hit if you move X squares? Return -1 if impossible.
        Split into penalties from wielder moving, shot distance, and number of shots
        :param move_distance: how far the wielder moved
        :param shot_distance: how far away the target is
        :returns: int
        """
        if move_distance > 0 and isinstance(self, HeavyWeapon):
            return -1
        move_penalty = 0 if isinstance(self, AssaultWeapon) else self.owner.rs

        shots_penalty = (self.attacks-1)**3  # TODO

        range_increments = shot_distance // self.range
        if isinstance(self, AssaultWeapon):
            # first increment is free
            range_penalty = max(range_increments-1, 0)*self.owner.rs
        elif isinstance(self, HeavyWeapon):
            # second increment is free, others cost
            range_penalty = abs(range_increments-1)*self.owner.rs
        else:
            # first two are free
            range_penalty = max(range_increments-2, 0)*self.owner.rs

        return move_penalty + range_penalty + shots_penalty

    @property
    def threat(self):
        return (WeaponCategory[self.category]/WeaponCategory['melee'],
                self.range/lch.global_vars['bf_diag'], self.attacks * 0.33,
                self.punch * 0.1, self.min_damage * 0.2, self.max_damage * 0.1)

class AssaultWeapon(RangedWeapon):
    category='assault'

class HeavyWeapon(RangedWeapon):
    category='heavy'

class Pistol(AssaultWeapon):
    pass

class SMG(AssaultWeapon):
    pass

class Shotgun(AssaultWeapon):
    pass

class Rifle(RangedWeapon):
    pass

class MG(HeavyWeapon):
    pass

class Sniper(HeavyWeapon):
    pass

class Rocket(HeavyWeapon):
    pass

class Knife(MeleeWeapon):
    pass

class Sword(MeleeWeapon):
    pass

class Axe(MeleeWeapon):
    pass

