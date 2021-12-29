import lch
import typing as ty
import random

__all__ = 'Weapon Pistol SMG Shotgun Rifle MG Sniper Knife Sword Axe'.split()

class Weapon(object):
    """
    """
    category = 'none'
    def __init__(self, name, _range=1, attacks=1, punch=0, min_damage=0, max_damage=0, _hash=None, owner=None):
        self.name = name
        self.range = _range
        self.attacks = attacks
        self.punch = punch
        self._damage = (min_damage, max_damage)
        self.owner = owner
        self.hash = _hash or lch.get_hash(*map(str, self.stats))

    def __str__(self):
        return f'{self.name} ({self.range}/{self.attacks}/{self.punch})'

    def __eq__(self, rhs):
        return self.hash == rhs.hash

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
        return cls(name=name, attacks=attacks, punch=punch, 
                min_damage=min_damage, max_damage=max_damage, _hash=_hash)

    @classmethod
    def from_tuple(cls, x):
        _hash, name, _, _range, attacks, punch, min_damage, max_damage = x
        return cls(name=name, _range=_range, attacks=attacks, punch=punch,
                min_damage=min_damage, max_damage=max_damage, _hash=_hash)

    @property
    def stats(self):
        return (self.range, self.attacks, self.punch, self.category, self._damage[0], self._damage[1])

    def encode(self):
        return (self.hash, self.name, self.__class__.__name__, self.range,
                self.attacks, self.punch, self._damage[0], self._damage[1])

    @property
    def avg_damage(self):
        return 0.5*sum(self._damage)

    def damage(self):
        return random.randint(*self._damage)

    def chance_to_hit(self, target, bf):
        raise NotImplementedError()


class MeleeWeapon(Weapon):
    def __init__(self, **kwargs):
        self.range = 0
        super().__init__(**kwargs)

    def chance_to_hit(self, target, bf):
        if self.owner.position not in bf.adjacent(target.position):
            return 0.
        return 0.5


class RangedWeapon(Weapon):
    def chance_to_hit(self, target, bf):
        dist, obstruction = bf.los_range(self.owner.position, target.position)
        range_increments = dist // self.range
        if hasattr(self, 'move_penalty'):
            pass

class Pistol(RangedWeapon):
    category = 'assault'
    pass

class SMG(RangedWeapon):
    category = 'assault'
    pass

class Shotgun(RangedWeapon):
    category = 'assault'
    pass

class Rifle(RangedWeapon):
    category = 'none'
    pass

class MG(RangedWeapon):
    category = 'heavy'
    pass

class Sniper(RangedWeapon):
    category = 'heavy'
    pass

class Rocket(RangedWeapon):
    pass

class Knife(MeleeWeapon):
    category = 'melee'
    pass

class Sword(MeleeWeapon):
    category = 'melee'
    pass

class Axe(MeleeWeapon):
    category = 'melee'
    pass

