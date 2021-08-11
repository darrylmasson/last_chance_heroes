import lch
import copy


class Team(object):
    """
    """
    def __init__(self, models):
        self.models = [copy.copy(m) for m in models]
        self.AI = lch.AI()
        for m in self.models:
            m.team = self
        print('This team consists of:', self.models)

    def ready_up(self):
        for model in self.models:
            if model.status not in ['dead']:
                model.status = 'ready'

    def is_dead(self):
        for model in self.models:
            if model.status != 'dead':
                return False
        return True

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
