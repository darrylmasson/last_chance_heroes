import lch
from math import sqrt
from scipy.stats import norm

__all__ = 'chance_to_hit_ranged chance_to_hit_melee Action NoAction MoveAction AttackAction MeleeAction ShootAction SnapShotAction ChargeAction'.split()

def chance_to_hit_ranged(attacker, defender, obstruction=0, move_dist=0, shot_dist=0):
    """
    Chance for an attacker to hit a defender at range
    :param attacker: a Model
    :param defender: a Model
    :param obstruction: number of obstructed squares between attacker and target
    :param moved: int, number of squares the attacker has moved
    :returns: float, chance to hit
    """
    penalty = attacker.rw.penalty(move_dist, shot_dist)
    if penalty is None:
        return 0
    penalty = sum(penalty)
    return norm.sf(defender.dodge, loc=attacker.rs-penalty*attacker.rc, scale=attacker.rc)

def chance_to_hit_melee(attacker, defender, charged=False, n_trials = 1000):
    """
    Chance for an attacker to hit a defender in melee combat. No closed-form
    expression so just runs 1000 mock trials
    :param attacker: a Model
    :param defender: a Model
    :param charged: bool, did the attacker charge into this combat
    :param n_trials: how many trials to simulate. Default 1000
    :returns: float, approx chance to hit
    """
    a_consistency = attacker.mc
    a_skill = attacker.ms + (0 if not charged else a_consistency)
    d_skill = defender.ms
    d_consistency = defender.mc
    a = norm.rvs(loc=a_skill, scale=a_consistency, size=n_trials)
    d = norm.rvs(loc=d_skill, scale=d_consistency, size=n_trials)
    return (a > d).sum()/n_trials

class Action(object):
    """
    See AI.dtype for more info about fields
    """
    bf = None
    def __init__(self, model=None, target=None, move_dest=None, bf=None, **kwargs):
        self.model = model
        self.target = target
        self.move_dest = move_dest
        self.move_dist = 0 if move_dest is None else bf.astar_path(model.coords, move_dest)[1]
        start = move_dest or model.coords
        end = start if target is None else target.coords
        self.shot_dist, self.obstruction = bf.los_range(start, end)
        for k in 'shootable_targets chargeable_targets can_shoot_back can_charge_back'.split():
            setattr(self, k, kwargs.pop(k, 0))
        self.hit_prob = 0
        for k,v in kwargs.items():
            setattr(self, k, v)

    def encode(self):
        """
        Serialize for the db
        """
        dest = (None, None) if self.move_dest is None else self.move_dest
        return (self.__class__.__name__,
                self.model.game_hash,
                self.target and self.target.game_hash,
                *dest,
                self.shootable_targets,
                self.chargeable_targets,
                self.can_shoot_back,
                self.can_charge_back
                )

    @staticmethod
    def from_tuple(self, args):
        """
        The reverse of encode. No from_hash method because we don't hash actions
        """
        cls = getattr(lch, args[0])
        return cls(
            model = lch.global_vars[args[1]],
            target = lch.global_vars.get(args[2]),
            move_dest = args[3] and args[4] and (args[3], args[4]),
            shootable_targets = args[5],
            chargeable_tagets = args[6],
            can_shoot_back = args[7],
            can_charge_back = args[8]
            )

    def normalize(self):
        """
        Return a tuple that matches AI.dtype
        """
        f_threat = self.model.threat
        f_threat_mw = self.model.mw.threat
        f_threat_rw = self.model.rw.threat
        start = self.move_dest or self.model.coords
        if self.target is None:
            e_threat = tuple([0]*len(f_threat))
            e_threat_mw = tuple([0]*len(f_threat_mw))
            e_threat_rw = tuple([0]*len(f_threat_rw))
        else:
            e_threat = self.target.threat
            e_threat_mw = self.target.mw.threat
            e_threat_rw = self.target.rw.threat
        return tuple([
            0, # number of possible actions, filled later
            self.shootable_targets,
            self.chargeable_targets,
            self.can_shoot_back,
            self.can_charge_back,
            int(self.target.status != 'ready') if self.target is not None else -1,
            self.model.team.remaining_actions(),
            self.target.team.remaining_actions() if self.target is not None else -1,
            self.hit_prob,
            self.shot_dist,
            *f_threat,
            *f_threat_mw,
            *f_threat_rw,
            *e_threat,
            *e_threat_mw,
            *e_threat_rw
        ])

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

    def normalize(self):
        raise NotImplementedError()

class MoveAction(Action):
    pass

class AttackAction(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hit_prob = self.chance_to_hit()

    def chance_to_hit(self):
        return 0

class ShootAction(AttackAction):
    def chance_to_hit(self):
        return chance_to_hit_ranged(self.model, self.target,
                self.obstruction, self.move_dist, self.shot_dist)

class MeleeAction(AttackAction):
    def chance_to_hit(self):
        return chance_to_hit_melee(self.model, self.target, isinstance(self, MoveAction))

class SnapShotAction(MoveAction, ShootAction):
    pass

class ChargeAction(MoveAction, MeleeAction):
    pass

