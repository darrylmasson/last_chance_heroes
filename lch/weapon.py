import lch
import typing as ty


class Weapon(object):
    """
    """
    def __init__(self, name, attacks=1, punch=0, min_damage=0, max_damage=0, category='none', owner=None):
        self.name = name
        self.attacks = attacks
        self.punch = punch
        self.category = category
        self.damage = (min_damage, max_damage)
        self.owner = owner

    def __str__(self):
        return f'{self.name} ({self.range}/{self.attacks}/{self.punch})'

    def __eq__(self, rhs):
        return self.name == rhs.name

    @property
    def avg_damage(self):
        return 0.5*sum(self.damage)

    def damage(self):
        return random.randint(*self.damage)

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
    pass

NoRangedWeapon = Weapon("None", -1, 0, 0)

