import lch
from math import sqrt, sin, cos, atan2, pi
import typing as ty
import itertools
import tqdm

__all__ = 'Battlefield'.split()


class Square(object):
    """
    Simple struct to handle terrain stuff, and also which squares are adjacent
    """
    def __init__(self, x: int, y: int, move_scale: float, los_scale: float):
        """
        :param x: the x coordinate, in [0, size_x)
        :param y: the y coordinate, in [0, size_y)
        :param move_scale: float >= 1, how easy it is to move into this square.
            Larger numbers mean more difficult, -1 means impossible
        :param los_scale: float >= 0, how easy it is to see through this square.
            Larger numbers mean more difficult, -1 means impossible
        """
        self.position = (x,y)
        self.move_scale = move_scale
        self.los_scale = los_scale
        self.move_cost = {}
        self.los_cost = {}
        self.cover = {}

    def __str__(self):
        return f"{self.position} | {self.move_scale:.1f}, {self.los_scale:.1f}"

    def __repr__(self):
        return str(self)

    def __eq__(self, rhs):
        return self.position == rhs.position

class Battlefield(object):
    """
    The class handling positions and movement etc, this is where all
    the pathfinding etc algs are
    """
    def __init__(self,
            size_x: int,
            size_y: int,
            terrain_func=None,
            terrain_list=None):
        """
        :param size_x: size of the battlefield in the X direction
        :param size_y: same, in Y
        :param terrain_func: function with signature (x,y) -> (float, float). This
            function determines the terrain on the battlefield. The first returned
            value is the movement difficulty for the specified square, 1 means
            unobstructed, more means difficult. The second determines line-of-sight
            difficulty, 1 means unobstructed, more means difficult. -1 means
            impassable.
        :param terrain_list: list of (x,y,float,float), the pre-computed result
            of the terrain function
        """
        assert terrain_func is not None or terrain_list is not None, (
                "Specify at least one way of determining terrain")
        self.cache = {}
        self.size = (size_x, size_y)
        lch.global_vars['bf_size'] = (size_x, size_y)
        lch.global_vars['bf_diag'] = sqrt(size_x**2 + size_y**2)
        # first, generate terrain
        if terrain_func is not None:
            for x in range(size_x):
                for y in range(size_y):
                    self.cache[(x,y)] = Square(x, y, *terrain_func(x,y))
        else:
            for x, y, move, los in terrain_list:
                self.cache[(x,y)] = Square(x, y, move, los)
            for x in range(size_x):
                for y in range(size_y):
                    if (x,y) not in self.cache:
                        self.cache[(x,y)] = Square(x, y, 1, 1)

        # now, make it into a graph
        _adjacent = [ # CCW from +x
                (1,0),
                (1,1),
                (0,1),
                (-1,1),
                (-1,0),
                (-1,-1),
                (0,-1),
                (1,-1)
                ]
        scale = [0.5,0.707]
        for (x,y),this_sq in self.cache.items():
            if this_sq is None:
                continue
            for adj, (dx, dy) in enumerate(_adjacent):
                if (x+dx,y+dy) in this_sq.move_cost:
                    # this direction already linked
                    continue
                if (other := self.cache.get((x+dx,y+dy))) is not None:
                    if this_sq.move_scale == -1 or other.move_scale == -1:
                        a = -1
                    else:
                        a = (this_sq.move_scale + other.move_scale)*scale[adj%2]
                    this_sq.move_cost[other.position] = a
                    other.move_cost[this_sq.position] = a
                    if this_sq.los_scale == -1 or other.los_scale == -1:
                        a = -1
                    else:
                        a = (this_sq.los_scale + other.los_scale)*scale[adj%2]
                    this_sq.los_cost[other.position] = a
                    other.los_cost[this_sq.position] = a
        # now we check for hard corners by unlinking cardinal pairs around
        # an impassable square, like this:
        #
        #   x   x
        #   #x x#  x#   #x
        #           x   x
        for (x,y), this_sq in self.cache.items():
            if this_sq.move_scale != -1:
                continue
            for direction in range(0,8,2):
                x1, y1 = x+_adjacent[direction][0], y+_adjacent[direction][1]
                direction = (direction+2)%8
                x2, y2 = x+_adjacent[direction][0], y+_adjacent[direction][1]
                if ((sq1 := self.cache.get((x1,y1))) is not None and 
                        (sq2 := self.cache.get((x2, y2))) is not None):
                    sq1.move_cost[(x2, y2)] = -1
                    sq2.move_cost[(x1, y1)] = -1

        l = []
        for (x,y), sq in self.cache.items():
            if sq.move_scale != 1 or sq.los_scale != 1:
                l.append((x, y, sq.move_scale, sq.los_scale))
        self.hash = lch.get_hash(','.join(map(str,l)))
        lch.global_vars[self.hash] = self
        self.logger = lch.get_logger('battlefield', self.hash)
        self.logger.trace(f'BF: {" | ".join(map(str, l))}')
        self.astar_cache = {}
        self.los_cache = {}
        self.los_cache_hits = 0
        self.astar_cache_hits = 0

    def __del__(self):
        #print(f'LOS cache: {self.los_cache_hits} hits, {len(self.los_cache)} misses')
        #print(f'A* cache: {self.astar_cache_hits} hits, {len(self.astar_cache)} misses')
        try:
            del lch.global_vars[self.hash]
        except:
            pass

    def encode(self):
        """
        A db-serializable list of tuples
        """
        return [(self.size[0], self.size[1], 0, 0)] + [
                (x,y,sq.move_scale, sq.los_scale)
                for (x,y), sq in self.cache.items()
                if sq.move_scale != 1 and sq.los_scale != 1
        ]

    @classmethod
    def decode(cls, tuples):
        """
        The inverse of encode
        """
        size_x, size_y = tuples[0][:2]
        return cls(size_x, size_y, terrain_list=tuples[1:])

    def adjacent(self, position):
        """
        All squares adjacent to the input
        :param position: (x,y) tuple or list of (x,y) tuples, the squares of interest
        :returns: set of (x,y) tuples
        """
        if isinstance(position, tuple):
            return set(k for k,v in self.cache[position].move_cost.items() if v != -1)
        elif isinstance(position, (list, set)):
            ret = set()
            for pos in position:
                ret = ret | self.adjacent(pos)
            return ret - set(position)
        raise ValueError(f'Invalid position: {type(position)}, must be list or tuple')

    def straight_line(self, start, end, penetrating=False):
        """
        Generator for squares falling in a straight line
        :param start: (x,y) tuple, starting point
        :param end: (x,y) tuple, end point
        :bool penetrating: ignore obstructions on exact corners, default False
        :yields: (x,y) squares along the line
        """
        current = start
        theta = atan2(end[1]-start[1], end[0]-start[0])
        C, S = cos(theta), sin(theta)
        dx = 1 if end[0] >= start[0] else -1
        dy = 1 if end[1] >= start[1] else -1
        #self.logger.trace(f'Direction: {dx},{dy},{theta:.3f}')

        while current != end:
            # evaluate potential next squares
            A = self.dist_to_line((current[0]+dx, current[1]), start, theta)
            B = self.dist_to_line((current[0], current[1]+dy), start, theta)

            if A < B:
                current = (current[0]+dx, current[1])
            elif A > B:
                current = (current[0], current[1]+dy)
            else:
                # this means we hit the exact vertex between two squares
                # TODO double-blockers
                current = (current[0]+dx, current[1]+dy)
            yield current

    def los_range(self, start, end):
        """
        A to B as the crow (or bullet) flies, accounting for LOS blocking. Does
        a bunch of math to account for only crossing the corner of a square
        :param start: (x,y) tuple, start position
        :param end: (x,y) tuple, end position
        :returns: (float, float) tuple, LOS distance and amount of obstruction
        """
        # check the cache
        if (a := self.los_cache.get((start, end))) is not None or \
                (b := self.los_cache.get((end, start))) is not None:
            self.los_cache_hits += 1
            return a or b

        distance = sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)
        if end in self.cache[start].los_cost:
            # squares are adjacent
            return distance, self.cache[start].los_cost[end]
        theta = atan2(end[1]-start[1], end[0]-start[0])
        obstruction = self.cache[start].los_scale*0.5
        for square in self.straight_line(start, end):
            # TODO walk before run
            obstruction += self.cache[square].los_scale
        # we add too much in the previous step for the last square because
        # we only need to cross half
        obstruction -= self.cache[end].los_scale*0.5
        self.los_cache[(start, end)] = distance, obstruction
        return distance, obstruction

    def evaluate_los(self, start, end):
        """
        How clear of a shot do you have from start to end? Evaluates both outside corners as well as one inside corner.
        If all three are obstructed then no bueno
        :param start: (x,y) tuple, start position
        :param end: (x,y) tuple, end position
        :returns:
        """
        raise NotImplementedError()
        theta = atan2(end[1]-start[1], end[0]-start[0])
        t = theta % (pi/4)
        d1 = int(round(0.5*(cos(t)+sin(t)))*1000)
        d2 = int(round(0.5*(cos(t)-sin(t)))*1000)
        if d1 == d2:
            # line is either vertical or horizontal
            pass
        else:
            pass
        return

    def evaluate_line(self, start, end):
        """
        Evaluates LOS and obstruction along a line from one corner of one square to another corner of another
        :param start: (x,y) tuple, start coordinates (not integers)
        :param end: (x,y) tuple, end coordinates (not integers)
        :returns: (float, float) tuple, integrated obstruction > 0, integrated obstruction < 0
        """
        raise NotImplementedError()

    @staticmethod
    def dist_to_line(pos, ref, theta, scale=1000):
        """
        The perpendicular distance between a point and a line, quantized
        to so we avoid floating-point issues later
        :param pos: (x,y) tuple, square in question
        :param ref: (x,y) tuple, reference square for line
        :param theta: float, the slope of the line
        :param scale: int, the level of quantization, default 1000
        :returns: float, distance from the point to the line
        """
        v_dist = cos(theta)*(pos[1]-ref[1])
        h_dist = sin(theta)*(pos[0]-ref[0])
        return int(scale*abs((v_dist-h_dist)))

    def determine_cover(self, start, end):
        """
        Is the target square in cover from this direction?
        :param start: (x,y) tuple, direction the shot is coming from
        :param end: (x,y) tuple, target square
        :returns: float, hit modifier in (0,1]
        """
        angle = atan2(end[1]-start[1], end[0]-start[0])
        dx, dy = round(cos(angle)/sqrt(2)), round(sin(angle)/sqrt(2))
        blah = self.cache[end].cover.get((dx, dy))
        return blah or 1.

    def astar_path(self, start, end, max_distance=1e12, blocked=None):
        '''
        A* pathfinding algorithm
        :param start: (x,y) tuple, start position
        :param end: (x,y) tuple, end position
        :param max_distance: the maximum distance you want to consider. Default 
            large number which means all
        :param blocked: set of squares that can't be moved through for other reasons 
            (probably occupied)
        :returns: (list of (x,y) tuples, total distance)
        '''
        def heuristic(a,b):
            # TODO improve this
            x1, y1 = a
            x2, y2 = b
            dx = abs(x1-x2)
            dy = abs(y1-y2)
            # scale the diagonal bit by sqrt(2)
            return 0.414*min(dx, dy) + max(dx, dy)

        frontier = lch.PriorityQueue(start)
        came_from = {start: (None,0)}
        blocked = blocked or set()

        if heuristic(start, end) > max_distance:
            # best case distance is too far
            #self.logger.trace(f'Distance too far')
            return [], -1

        if (start, end) in self.astar_cache or (end, start) in self.astar_cache:
            p, d = self.astar_cache.get((start, end)) or self.astar_cache.get((end, start))
            if all(s not in p for s in blocked): # TODO which order is faster?
                self.logger.trace(f'Using cached path from {start} to {end}')
                # cached and still valid
                self.astar_cache_hits += 1
                return p, d # worry about direction of p later

        self.logger.trace(f'Computing a* from {start} to {end} dist {max_distance}')

        while not frontier.empty and (current := frontier.get()) != end:
            #self.log('trace', f'Current: {current} | {cost_so_far[current]:.1f}')
            for _next, diff_cost in self.cache[current].move_cost.items():
                if diff_cost == -1 or _next in blocked:
                    continue
                new_cost = came_from[current][1] + diff_cost
                #self.log('trace', f'Evaluating {_next}: {cost:.1f} {new_cost:.1f}')
                if (new_cost <= max_distance and
                        (_next not in came_from or new_cost < came_from[_next][1])):
                    priority = heuristic(end, _next) + new_cost
                    frontier.put(_next, priority)
                    #self.log('trace', f'Putting {_next} at {priority:.1f}')
                    came_from[_next] = (current, new_cost)
        if end not in came_from:
            # didn't make it
            self.logger.trace(f'No path found')
            return [], -1
        path = []
        current = end
        while current != start:
            path.append(current)
            current = came_from[current][0]
        path.append(start)
        path.reverse()
        self.logger.trace(f'Found path with length {came_from[end][1]}')
        self.astar_cache[(start, end)] = path, came_from[end][1]
        return path, came_from[end][1]

    def reachable(self, start, max_distance, blocked=None):
        '''
        Dijkstra's alg. This is a generator because it's only ever used as
        "for position in reachable"
        :param start: (x,y) tuple, start coords
        :param max_distance: maximum distance to consider
        :param blocked: additional squares that cannot be passed through
        :yields: (x,y) positions that can be reached
        '''
        frontier = lch.PriorityQueue(start)
        came_from = {start: (None, 0)}
        blocked = blocked or set()
        self.logger.trace(f'Finding all squares within {max_distance} of {start}')

        while not frontier.empty:
            current = frontier.get()
            yield current
            blocked.add(current)
            for _next, diff_cost in self.cache[current].move_cost.items():
                if _next in blocked or diff_cost == -1:
                    continue
                new_cost = came_from[current][1] + diff_cost
                if (new_cost < max_distance and 
                        (_next not in came_from or new_cost < came_from[_next][1])):
                    frontier.put(_next, new_cost)
                    came_from[_next] = (current, new_cost)

