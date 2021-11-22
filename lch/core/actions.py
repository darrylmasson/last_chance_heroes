import lch
import numpy as np
from scipy.stats import norm

__all__ = 'Action NoAction MoveAction MeleeAction ShootAction SnapShotAction ChargeAction'.split()

dice_log = []

def chance_to_hit_ranged(attacker, defender, obstruction=0, category=None, moved=False):
    consistency = attacker.ranged_consistency
    skill = attacker.ranged_skill - (0 if not moved else consistency)
    defense = defender.dodge
    # TODO add range penalties
    return norm.sf(defense, loc=skill, scale=consistency)

def chance_to_hit_melee(attacker, defender, charged=False, n_trials = 1000):
    a_consistency = attacker.melee_consistency
    a_skill = attacker.melee_skill + (0 if not charged else a_consistency)
    d_skill = defender.melee_skill
    d_consistency = defender.melee_consistency
    a = norm.rvs(loc=a_skill, scale=a_consistency, size=n_trials)
    d = norm.rvs(loc=d_skill, scale=d_consistency, size=n_trials)
    return (a > d).sum()/n_trials

def do_damage(attacker, defender, weapon):
    effective_armor = max(defender.armor - weapon.punch, 0)
    damage = max(weapon.damage() - effective_armor, 0)
    #print(f'Attacker does {damage} vs {effective_armor}')
    defender.health -= damage
    if defender.health <= 0:
        defender.status = 'dead'
        defender.health = 0
        #print('You is dead, son')
    return

def ranged_combat_action(attacker, defender, obstruction=0, moved=False):
    #print(f'{attacker} attacks {defender}')
    if moved:
        if attacker.ranged_weapon.category in ['heavy']:
            penalty = attacker.ranged_consistency
        elif attacker.ranged_weapon.category in ['assault']:
            penalty = 0
        else:
            penalty = 0.5*attacker.ranged_consistency
    else:
        penalty = 0
    skill = attacker.ranged_skill - penalty
    hit_roll = norm.rvs(loc=skill, scale=attacker.ranged_consistency)
    #dice_log.append((skill, attacker.ranged_consistency, hit_roll))
    if hit_roll <= defender.dodge:
        #print(f'Attack roll {hit_roll} misses {defender.dodge}')
        return

    #print(f'{hit_roll} hits {defender.dodge}')
    do_damage(attacker, defender, attacker.ranged_weapon)
    return

def melee_combat_action(attacker, defender, charged=False):
    #print(f'{attacker} attacks {defender}')
    skill = attacker.melee_skill + (0 if not charged else attacker.melee_consistency)
    attack_roll = norm.rvs(loc=skill, scale=attacker.melee_consistency)
    defense_roll = norm.rvs(loc=defender.melee_skill, scale=defender.melee_consistency)
    #dice_log.append((skill, attacker.melee_consistency, attack_roll))
    #dice_log.append((defender.melee_skill, defender.melee_consistency, defense_roll))
    if attack_roll <= defense_roll:
        #print(f'Attack roll {attack_roll} misses {defense_roll}')
        return

    #print(f'{attack_roll} hits {defense_roll}')
    do_damage(attacker, defender, attacker.melee_weapon)
    return

class Action(object):
    """
    Action type:
    [
    chance to hit,
    average damage,
    target's health,
    shootable targets from specified location
    chargeable targets from specified location
    number of enemies who can shoot specified location
    number of enemies who can charge specified location
    ]
    for later:
      - split enemies into active/inactive
      - add number of remaining models in team
      - cover
      - chance of an enemy's attack to do something

    """
    def __init__(self, model=None, target=None, move_destination=None, **kwargs):
        self.model = model
        self.target = target
        self.move_destination = move_destination
        for k in 'shootable_targets chargeable_targets can_shoot_back can_charge_back'.split():
            setattr(self, k, kwargs.pop(k, 0))
        self.hit_prob = 0
        self.avg_damage = 0
        self.target_health = 0 if target is None else target.health
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return str(self.normalize())

    def normalize(self):
        return tuple([
            0, # number of possible actions
            self.shootable_targets,
            self.chargeable_targets,
            self.can_shoot_back,
            self.can_charge_back,
            self.hit_prob,
            self.avg_damage,
            self.target_health,
        ])

    def engage(self):
        raise NotImplementedError()

    def move_model(self):
        self.model.status = "activated"
        if not isinstance(self.move_destination, tuple):
            raise ValueError(f'Move dest must be a tuple, not a {type(self.move_destination)}')
        #print(f'Moving {self.model} to {self.move_destination}')
        self.model.position = self.move_destination

    def attack(self, attack_type):
        if attack_type == 'ranged':
            return ranged_combat_action(self.model, self.target, isinstance(self, MoveAction))
        if attack_type == 'melee':
            return melee_combat_action(self.model, self.target, isinstance(self, MoveAction))
        raise NotImplementedError()

class NoAction(Action):
    """
    In case we don't want to do anything
    """
    def __init__(self):
        self.shootable_targets = 0
        self.chargeable_targets = 0
        self.can_shoot_back = 0
        self.can_charge_back = 0
        self.hit_prob = 0
        self.avg_damage = 0
        self.target_health = 0

    def __str__(self):
        return "No action"

    def engage(self):
        pass

class MoveAction(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def engage(self):
        self.move_model()

class ShootAction(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, 'obstruction'):
            self.obstruction = 0
        self.hit_prob = chance_to_hit_ranged(self.model, self.target, self.obstruction, self.model.ranged_weapon.category, issubclass(self.__class__, MoveAction))
        self.avg_damage = self.model.ranged_weapon.avg_damage

    def engage(self):
        self.attack('ranged')

class MeleeAction(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hit_prob = chance_to_hit_melee(self.model, self.target, self.model.melee_weapon.category, issubclass(self.__class__, MoveAction))
        self.avg_damage = self.model.melee_weapon.avg_damage

    def engage(self):
        self.attack('melee')

class SnapShotAction(MoveAction, ShootAction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def engage(self):
        self.move_model()
        self.attack('ranged')

class ChargeAction(MoveAction, MeleeAction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def engage(self):
        self.move_model()
        self.attack('melee')

