import lch
import typing as ty
import random

__all__ = 'Weapon MeleeWeapon RangedWeapon NoRangedWeapon'.split()

class Weapon(object):
    """
    """
    def __init__(self, name, attacks=1, punch=0, min_damage=0, max_damage=0, category='none', owner=None):
        self.name = name
        self.attacks = attacks
        self.punch = punch
        self.category = category
        self._damage = (min_damage, max_damage)
        self.owner = owner

    def __str__(self):
        return f'{self.name} ({self.range}/{self.attacks}/{self.punch})'

    def __eq__(self, rhs):
        return self.name == rhs.name

    @property
    def avg_damage(self):
        return 0.5*sum(self._damage)

    def damage(self):
        return random.randint(*self._damage)

    def chance_to_hit(self, target, bf):
        raise NotImplementedError()


class MeleeWeapon(Weapon):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.range = 0

    def chance_to_hit(self, target, bf):
        if self.owner.position not in bf.adjacent(target.position):
            return 0.
        return 0.5


class RangedWeapon(Weapon):
    def __init__(self, **kwargs):
        self.range = kwargs.pop('range')
        super().__init__(**kwargs)

    def chance_to_hit(self, target, bf):
        dist, obstruction = bf.los_range(self.owner.position, target.position)
        range_increments = dist // self.range
        if hasattr(self, 'move_penalty'):
            pass

class Pistol(RangedWeapon):
    def __init__(self):
        kwargs = {
                'range': 4,
                'punch': 0,
                'move_penalty': 0
                }
        super().__init__(name='pistol', **kwargs)

class SMG(RangedWeapon):
    pass

class Rifle(RangedWeapon):
    pass

class MG(RangedWeapon):
    pass

class Sniper(RangedWeapon):
    pass

class Rocket(RangedWeapon):
    pass

class Knife(MeleeWeapon):
    pass

class Sword(MeleeWeapon):
    pass

class Axe(MeleeWeapon):
    pass

NoRangedWeapon = RangedWeapon(name="None", range=-1, attacks=0)

