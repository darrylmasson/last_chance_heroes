import lch
import random

class Model(object):
    """
    """
    def __init__(self, name, movement, ranged_skill, ranged_consistency, melee_skill, melee_consistency, dodge, health, melee_weapon, armor, pos_x=-1, pos_y=-1, ranged_weapon='NoRangedWeapon', current_health=None, team=None):
        self.movement = movement
        self.ranged_skill = ranged_skill
        self.ranged_consistency = ranged_consistency
        self.melee_skill = melee_skill
        self.melee_consistency = melee_consistency
        self.health = health
        self.current_health = current_health or health
        self.melee_weapon = melee_weapon
        self.ranged_weapon = ranged_weapon
        self.dodge = dodge
        self.position = (pos_x, pos_y)
        self.status = 'ready'
        self.name = name
        self.armor = armor
        self.team = team

    def __str__(self):
        return f'{self.name}, pos {self.position}, status {self.status}'

    def __eq__(self, rhs):
        return self.name == rhs.name

    def possible_actions(self, allies, enemies, bf):
        #print(f'Making actions for {self}')
        if self.status != 'ready':
            return []
        enemy_locations = enemies.locations()
        occupied = enemy_locations | self.team.locations(exclude=self)
        enemy_adjacent = bf.adjacent(enemy_locations)

        actions = []
        action_kwargs = self.evaluate_position(None, enemies, bf)
        # first, are we in combat already?
        if self.position in enemy_adjacent:
            for enemy in enemies:
                if self.position in bf.adjacent(enemy.position):
                    actions.append(lch.MeleeAction(model=self, target=enemy, **action_kwargs))
            return actions

        # second, shoot without moving
        if self.ranged_weapon is not lch.NoRangedWeapon:
            for e in enemies:
                dist, obs = bf.los_range(self.position, e.position)
                if dist < self.ranged_weapon.range:
                    actions.append(lch.ShootAction(model=self, target=e, obstruction=obs, **action_kwargs))

        # move and handle actions
        for pos in bf.reachable(self.position, self.movement):
            if pos in occupied:
                continue
            action_kwargs = self.evaluate_position(pos, enemies, bf)
            if pos in enemy_adjacent:
                for enemy in enemies:
                    if enemy.position == pos:
                        actions.append(lch.ChargeAction(model=self, target=enemy, move_destination=pos, **action_kwargs))
            else:
                actions.append(lch.MoveAction(model=self, target=None, move_destination=pos, **action_kwargs))
                if self.ranged_weapon is not lch.NoRangedWeapon:
                    for e in enemies:
                        dist, obs = bf.los_range(pos, e.position)
                        if dist <= self.ranged_weapon.range:
                            actions.append(lch.SnapShotAction(model=self, target=e, move_destination=pos, obstruction=obs, **action_kwargs))

        return actions

    def evaluate_position(self, position, enemies, bf):
        """
        Location-based kwargs for actions
        :param model: Model instance
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
            if self.ranged_weapon.range >= los_dist:
                ret['shootable_targets'] += 1
            if enemy.ranged_weapon.range >= los_dist:
                ret['can_shoot_back'] += 1
            _, dist = bf.astar_path(position, enemy.position)
            if dist != -1 and self.movement >= dist:
                ret['chargeable_targets'] += 1
            if dist != -1 and enemy.movement >= dist:
                ret['can_charge_back'] += 1
        return ret
