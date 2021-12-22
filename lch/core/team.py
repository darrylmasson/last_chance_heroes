import lch
import copy

__all__ = 'Team'.split()

class Team(object):
    """
    """
    def __init__(self, models, ai):
        self.models = [copy.copy(m) for m in models]
        self.hash = lch.get_hash(*[m.hash for m in models], ai.hash)
        self.logger = lch.get_logger('team', self.hash)
        self.AI = ai
        for m in self.models:
            m.team = self
            m.logger = self.logger

    def encode(self):
        """
        A db-serializable tuple
        """
        pass

    @staticmethod
    def decode(*args):
        """
        The reverse of encode
        """
        pass

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

    def locations(self, exclude=None, include_dead=False):
        ret = []
        for m in self.models:
            if (exclude is not None and m == exclude) or (m.status == 'dead' and not include_dead):
                continue
            ret.append(m.position)
        return set(ret)

    def adjacent(self, bf):
        ret = set()
        for m in self.models:
            if m.status == 'dead':
                continue
            ret |= bf.adjacent(m.position)
        return ret

    def __iter__(self):
        return self.models.__iter__()
