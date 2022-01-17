import lch
import copy

__all__ = 'Team'.split()

class Team(object):
    """
    The primary way of creating teams is by calling from_hash, or from_tuple if
    you're populating the cache with new teams. __init__ isn't really intended for
    "user" use, but it takes hashes rather than instances.
    """
    MAX_TEAM_SIZE=6

    def __init__(self, models=None, ai=None, _hash=None):
        self.models = models
        self.hash = _hash or lch.get_hash(*(m.hash for m in models))
        self.game_hash = lch.get_hash(self.hash, *(m.name for m in models))
        lch.global_vars[self.game_hash] = self
        self.logger = lch.get_logger('team', self.hash)
        self.AI = ai
        for m in self.models:
            m.team = self
            m.logger = self.logger

    def __eq__(self, rhs):
        return self.game_hash == rhs.game_hash

    @classmethod
    def create_table(cls, conn):
        cmd = "CREATE TABLE team (hash TEXT PRIMARY KEY NOT NULL"
        for i in range(cls.MAX_TEAM_SIZE):
            cmd += f", m{i}_hash TEXT, m{i}_name TEXT, m{i}_mw TEXT, m{i}_rw TEXT"
        cmd += ');'
        try:
            conn.execute(cmd)
        except Exception as e:
            pass

    def encode(self, use_game_hash=False):
        """
        A db-serializable tuple
        """
        ret = [self.game_hash if use_game_hash else self.hash]
        for m in self.models:
            ret += [m.hash, m.name, m.mw.hash, m.rw.hash]

        if len(ret) < 1 + 4*self.MAX_TEAM_SIZE:
            ret += [None] * (1 + 4*self.MAX_TEAM_SIZE - len(ret))
        return tuple(ret)

    @classmethod
    def from_hash(cls, _hash):
        return cls.from_tuple(lch.load_from_cache('team', _hash))

    @classmethod
    def from_tuple(cls, args):
        """
        The reverse of encode
        """
        #print(f'Decoding {args}')
        _hash = args[0]
        models = []
        for i in range(1, len(args), 4):
            if args[i] is None:
                break
            model = lch.Model.from_hash(args[i])
            model.name = args[i+1]
            model.mw = lch.Weapon.from_hash(args[i+2])
            model.mw.owner = model
            model.rw = lch.Weapon.from_hash(args[i+3])
            model.rw.owner = model
            model.game_hash = lch.get_hash(model.hash, model.name)
            models.append(model)
            lch.global_vars[model.game_hash] = model
        return cls(models=models, _hash=_hash)

    def generate_actions(self, enemies, bf):
        actions = []
        for model in self.models:
            friendlies = self.positions(exclude=model)
            actions += model.generate_actions(friendlies, enemies, bf)

        return actions

    def ready_up(self):
        for model in self.models:
            if model.status not in ['dead']:
                model.status = 'ready'

    def is_dead(self):
        for model in self.models:
            if model.status != 'dead':
                return False
        return True

    def strength(self):
        # how many HP are left
        return sum(m.current_health for m in self.models)

    def positions(self, exclude=None, include_dead=False):
        ret = []
        for m in self.models:
            if (exclude is not None and m == exclude) or (m.status == 'dead' and not include_dead):
                continue
            ret.append(m.position)
        return set(ret)

    def remaining_actions(self):
        return sum(1 if m.status == 'ready' else 0 for m in self.models)

    def adjacent(self, bf):
        ret = set()
        for m in self.models:
            if m.status == 'dead':
                continue
            ret |= bf.adjacent(m.position)
        return ret

    def __iter__(self):
        return self.models.__iter__()
