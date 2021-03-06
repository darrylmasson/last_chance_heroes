import random

__all__ = 'empty_bf Forest'.split()

def empty_bf(*args):
    return (1,0)

class Forest(object):
    def __init__(self, size_x, size_y):
        self.tree_locations = set()
        area = (size_x-1) * (size_y-1)
        num_trees = random.randint(int(area*0.1), int(area*0.33))
        while len(self.tree_locations) < num_trees:
            x, y = random.randint(1, size_x-2), random.randint(1, size_y-2)
            self.tree_locations.add((x,y))

    def __call__(self, x, y):
        if (x,y) in self.tree_locations:
            return -1, -1
        return 1,1

class City(object):
    def __init__(self, size_x, size_y):
        pass

    def __call__(self, x, y):
        pass
