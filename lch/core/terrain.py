import random

__all__ = 'empty_bf Forest forest'.split()

def empty_bf(*args):
    return (1,0)

class Forest(object):
    is_init=False
    num_trees=0
    tree_locations=[]

    @classmethod
    def init(cls):
        cls.num_trees = random.randint(10, 20)
        cls.tree_locations = []
        while len(cls.tree_locations) <= cls.num_trees:
            x,y = random.randint(1, 23), random.randint(1, 15)
            if (x,y) in cls.tree_locations:
                continue
            cls.tree_locations.append((x,y))
        cls.is_init=True

    @classmethod
    def generate(cls, x, y):
        if not cls.is_init:
            cls.init()
        if (x,y) in cls.tree_locations:
            return -1, -1
        return 1,1

def forest(x,y):
    return Forest.generate(x,y)
