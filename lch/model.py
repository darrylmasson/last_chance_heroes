import lch
import random

class Model(object):
    """
    """
    def __init__(self, name, movement, ranged_skill, ranged_consistency, melee_skill, melee_consistency, dodge, health, melee_weapon, armor, ranged_weapon=NoRangedWeapon, team=None):
        self.movement = movement
        self.ranged_skill = ranged_skill
        self.ranged_consistency = ranged_consistency
        self.melee_skill = melee_skill
        self.melee_consistency = melee_consistency
        self.health = health
        self.melee_weapon = melee_weapon
        self.ranged_weapon = ranged_weapon
        self.dodge = dodge
        self.position = (-1, -1)
        self.status = 'ready'
        self.name = name
        self.armor = armor
        self.team = team

    def __str__(self):
        return f'{self.name}, pos {self.position}, status {self.status}'

    def __eq__(self, rhs):
        return self.name == rhs.name

    def possible_actions(self, allies, enemies, bf):
        print(f'Making actions for {self}')
        if self.status != 'ready':
            return []
        enemy_locations = enemies.locations()
        occupied = enemy_locations | self.team.locations(exclude=self)
        enemy_adjacent = enemies.adjacent(bf)

        actions = []
        action_kwargs = evaluate_position(self, None, enemies, bf)
        # first, are we in combat already?
        if self.position in enemy_adjacent:
            for enemy in enemies:
                if self.position in bf.adjacent(enemy.position):
                    actions.append(lch.MeleeAction(self, enemy, **action_kwargs))
            return actions

        # second, shoot without moving
        if self.ranged_weapon is not NoRangedWeapon:
            for e in enemies:
                if bf.los_range(self.position, e.position) < self.ranged_weapon.range:
                    actions.append(lch.ShootAction(model=self, target=e, **action_kwargs))

        # move and handle actions
        for pos in bf.reachable(self.position, self.movement):
            if pos in occupied:
                continue
            action_kwargs = evaluate_position(self, pos, enemies, bf)
            # TODO some caching of evaluate_position would be useful here
            if pos in enemy_adjacent:
                actions.append(lch.ChargeAction(model=self, target=enemy, move_destination=pos, **action_kwargs))
            else:
                actions.append(lch.MoveAction(model=self, target=None, move_destination=pos, **action_kwargs))
                if self.ranged_weapon is not NoRangedWeapon:
                    for e in enemies:
                        if bf.los_range(pos, e.position) < self.ranged_weapon.range:
                            actions.append(lch.SnapShotAction(model=self, target=e, move_destination=pos, **action_kwargs))

        return actions

def evaluate_position(a, pos, bb, bf):
    ret = {'shootable_targets': 0, 'chargeable_targets': 0,
            'can_shoot_back': 0, 'can_charge_back': 0}
    pos = pos or a.position
    for b in bb:
        los_dist = bf.los_range(pos, b.position)
        if a.ranged_weapon.range >= los_dist:
            ret['shootable_targets'] += 1
        if b.ranged_weapon.range >= los_dist:
            ret['can_shoot_back'] += 1
        _, dist = bf.astar_path(pos, b.position)
        if dist != -1 and a.movement >= dist:
            ret['chargeable_targets'] += 1
        if dist != -1 and b.movement >= dist:
            ret['can_charge_back'] += 1
    return ret
