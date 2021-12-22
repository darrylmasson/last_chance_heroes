import lch
import numpy as np
from scipy.stats import norm

__all__ = 'Action NoAction MoveAction MeleeAction ShootAction SnapShotAction ChargeAction'.split()

dice_log = []

def chance_to_hit_ranged(attacker, defender, obstruction=0, category=None, moved=False):
    consistency = attacker.rc
    skill = attacker.rs - (0 if not moved else consistency)
    defense = defender.dodge
    # TODO add range penalties
    return norm.sf(defense, loc=skill, scale=consistency)

def chance_to_hit_melee(attacker, defender, category=None, charged=False, n_trials = 1000):
    a_consistency = attacker.mc
    a_skill = attacker.ms + (0 if not charged else a_consistency)
    d_skill = defender.ms
    d_consistency = defender.mc
    a = norm.rvs(loc=a_skill, scale=a_consistency, size=n_trials)
    d = norm.rvs(loc=d_skill, scale=d_consistency, size=n_trials)
    return (a > d).sum()/n_trials

def do_damage(attacker, defender, weapon):
    effective_armor = max(defender.armor - weapon.punch, 0)
    damage = max(weapon.damage() - effective_armor, 0)
    #print(f'Attacker does {damage} vs {effective_armor}')
    defender.current_health -= damage
    if defender.current_health <= 0:
        defender.status = 'dead'
        defender.current_health = 0
        #print('You is dead, son')
    return

def ranged_combat_action(attacker, defender, obstruction=0, moved=False):
    #print(f'{attacker} attacks {defender}')
    if moved:
        if attacker.rw.category in ['heavy']:
            penalty = attacker.rc
        elif attacker.rw.category in ['assault']:
            penalty = 0
        else:
            penalty = 0.5*attacker.rc
    else:
        penalty = 0
    skill = attacker.rs - penalty
    hit_roll = norm.rvs(loc=skill, scale=attacker.rc)
    #dice_log.append((skill, attacker.rc, hit_roll))
    if hit_roll <= defender.dodge:
        #print(f'Attack roll {hit_roll} misses {defender.dodge}')
        return

    #print(f'{hit_roll} hits {defender.dodge}')
    do_damage(attacker, defender, attacker.rw)
    return

def melee_combat_action(attacker, defender, charged=False):
    #print(f'{attacker} attacks {defender}')
    skill = attacker.ms + (0 if not charged else attacker.mc)
    attack_roll = norm.rvs(loc=skill, scale=attacker.mc)
    defense_roll = norm.rvs(loc=defender.ms, scale=defender.mc)
    #dice_log.append((skill, attacker.mc, attack_roll))
    #dice_log.append((defender.ms, defender.mc, defense_roll))
    if attack_roll <= defense_roll:
        #print(f'Attack roll {attack_roll} misses {defense_roll}')
        return

    #print(f'{attack_roll} hits {defense_roll}')
    do_damage(attacker, defender, attacker.mw)
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
        self.target_health = 0 if target is None else target.current_health
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
        self.model.status = 'activated'
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
        self.hit_prob = chance_to_hit_ranged(self.model, self.target, self.obstruction, self.model.rw.category, isinstance(self, MoveAction))
        self.avg_damage = self.model.rw.avg_damage

    def engage(self):
        self.attack('ranged')

class MeleeAction(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hit_prob = chance_to_hit_melee(self.model, self.target, self.model.mw.category, isinstance(self, MoveAction))
        self.avg_damage = self.model.mw.avg_damage

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

