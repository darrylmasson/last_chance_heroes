import lch
from math import sqrt, sin, cos, atan2, pi
from collections import defaultdict
import typing as ty


class Location(object):
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
            terrain_func: ty.Callable[[int,int],ty.Tuple[float,float]],
            logger=None):
        """
        :param size_x: size of the battlefield in the X direction
        :param size_y: same, in Y
        :param terrain_func: function with signature (x,y) -> (float, float). This
            function determines the terrain on the battlefield. The first returned
            value is the movement difficulty for the specified square, 1 means
            unobstructed, more means difficult. The second determines line-of-sight
            difficulty, 1 means unobstructed, more means difficult. -1 means
            impassable.
        :param logger: Logger instance
        """
        self.cache = defaultdict(None)
        self.size = (size_x, size_y)
        self.terrain_func = terrain_func
        self.logger = logger
        # first, generate terrain
        for x in range(size_x):
            for y in range(size_y):
                self.cache[(x,y)] = Location(x, y, *terrain_func(x,y))

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
            x,y = this_sq.position
            for direction in range(0,8,2):
                x1, y1 = x+_adjacent[direction][0], y+_adjacent[direction][1]
                direction = (direction+2)%8
                x2, y2 = x+_adjacent[direction][0], y+_adjacent[direction][1]
                if ((sq1 := self.cache.get((x1,y1))) is not None and 
                        (sq2 := self.cache.get((x2, y2))) is not None):
                    sq1.move_cost[(x2, y2)] = -1
                    sq2.move_cost[(x1, y1)] = -1

    def log(self, level: str, message: str) -> None:
        if self.logger is not None:
            self.logger.entry(level, message)

    def get_json(self):
        d = {
                'size': list(self.size()),
                'nonzero': [
                    dict(x=x,y=y,m=s['move_scale'],v=s['los_scale'])
                    for (x,y), s in self.cache.items()
                    ],
                'team1': self.team1.get_dict(),
                'team2': self.team2.get_dict()
                }
        return json.dumps(d)

    def adjacent(self, position: ty.Union[ty.Tuple[int,int], list]) -> set:
        if isinstance(position, tuple):
            return set(k for k,v in self.cache[position].move_cost.items() if v != -1)
        elif isinstance(position, list):
            ret = set()
            for pos in position:
                ret = ret | self.adjacent(pos)
            return ret - set(position)
        raise ValueError(f'Invalid position: {type(position)}, must be list or tuple')

    def straight_line(self, start: ty.Tuple[int,int], end: ty.Tuple[int,int], penetrating=False) -> ty.Generator[ty.Tuple[int,int],None,None]:
        """
        Generator for squares falling in a straight line
        :param start: (x,y) tuple, starting point
        :param end: (x,y) tuple, end point
        :bool penetrating: ignore obstructions on exact corners
        :yields: squares along the line
        """
        current = start
        theta = atan2(end[1]-start[1], end[0]-start[0])
        C, S = cos(theta), sin(theta)
        dx = 1 if end[0] >= start[0] else -1
        dy = 1 if end[1] >= start[1] else -1
        self.log('trace', f'Direction: {dx},{dy},{theta:.3f}')

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

    def los_range(self, start: ty.Tuple[int,int], end: ty.Tuple[int,int]) -> ty.Tuple[float, float]:
        """
        A to B as the crow (or bullet) flies, accounting for LOS blocking. Does
        a bunch of math to account for only crossing the corner of a square
        :param start: (x,y) tuple, start position
        :param end: (x,y) tuple, end position
        :returns: (float, float) tuple, LOS distance and amount of obstruction
        """
        distance = sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)
        if end in self.cache[start].los_cost:
            # squares are adjacent
            return distance, self.cache[start].los_cost[end]
        obstruction = self.cache[start].los_scale*self.dist_through_square(0, theta)*0.5
        for square in self.straight_line(start, end):
            #dist = dist_to_line(square, start, theta)
            #obstruction += self.dist_through_square(dist, theta)*self.cache[current].los_scale
            # TODO walk before run
            obstruction += self.cache[current].los_scale
        # we add too much in the previous step for the last square because
        # we only need to cross half
        # TODO walk before run
        #obstruction -= self.cache[end].los_scale*self.dist_through_square(0, theta)*0.5
        return distance, obstruction

    def evaluate_los(self, start: ty.Tuple[int,int], end: ty.Tuple[int,int]) -> ty.Tuple[float, float]:
        """
        How clear of a shot do you have from start to end? Evaluates both outside corners as well as one inside corner.
        If all three are obstructed then no bueno
        :param start: (x,y) tuple, start position
        :param end: (x,y) tuple, end position
        :returns:
        """
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

    def evaluate_line(self, start: ty.Tuple[float, float], end: ty.Tuple[float, float]) -> ty.Tuple[float, float]:
        """
        Evaluates LOS and obstruction along a line from one corner of one square to another corner of another
        :param start: (x,y) tuple, start coordinates (not integers)
        :param end: (x,y) tuple, end coordinates (not integers)
        :returns: (float, float) tuple, integrated obstruction > 0, integrated obstruction < 0
        """
        pass

    @staticmethod
    def dist_to_line(pos: ty.Tuple[int,int], ref: ty.Tuple[int,int],
                     theta: float, scale=1000) -> int:
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

    @staticmethod
    def dist_through_square(perp_dist: float, theta: float) -> float:
        """
        So a line passes through a square, some distance from the center
        and at some angle. How long is the segment of the line in this
        square?
        :param perp_dist: float, distance from the line to the center of the square
        :param theta: angle to the horizontal
        :returns: float, the length of the line in the square in (0, sqrt(2)]
        """
        if perp_dist == 0:
            if theta/pi < 1/4 or theta/pi > 7/4 or 3/4 < theta/pi < 5/4:
                return abs(1/cos(theta))
            else:
                return abs(1/sin(theta))
        elif condition:
            theta = theta % (pi/4)
            B = abs(perp_dist/cos(theta))
            return perp_dist*tan(theta) + (1-B)/sin(theta)
        else:
            B = 0.5  # grid size
            return (B*(sin(theta)+cos(theta)) - perp_dist)/(sin(theta)*cos(theta))
        return 0

    def determine_cover(self, start: ty.Tuple[int,int], end: ty.Tuple[int,int]) -> float:
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

    def astar_path(self, start: ty.Tuple[int,int], end: ty.Tuple[int,int],
            max_distance=None) -> ty.Tuple[list, float]:
        '''
        A* pathfinding algorithm
        :param start: (x,y) tuple, start position
        :param end: (x,y) tuple, end position
        :param max_distance: the maximum distance you want to consider. Default None,
            which means all
        :returns: (path, total distance)
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

        while not frontier.empty:
            if (current := frontier.get()) == end:
                break
            self.log('trace', f'Current: {current} | {cost_so_far[current]:.1f}')
            for _next, differential_cost in self.cache[current].move_cost.items():
                if differential_cost == -1:
                    continue
                _next = _next.position
                new_cost = came_from[current][1] + differential_cost
                self.log('trace', f'Evaluating {_next}: {cost:.1f} {new_cost:.1f}')
                if ((max_distance is None or new_cost <= max_distance) and
                        (_next not in came_from or new_cost < came_from[_next][1])):
                    priority = heuristic(end, _next) + new_cost
                    frontier.put(_next, priority)
                    self.log('trace', f'Putting {_next} at {priority:.1f}')
                    came_from[_next] = (current, new_cost)
        if end not in came_from:
            # didn't make it
            return [], -1
        path = []
        current = end
        while current != start:
            path.append(current)
            current = came_from[current][0]
        path.append(start)
        path.reverse()
        return path, cost_so_far[end]

    def reachable(self,
            start: ty.Tuple[int,int],
            max_distance: int) -> ty.Generator[ty.Tuple[int,int], None, None]:
        '''
        Dijkstra's alg. This is a generator because it's only ever used as
        "for position in reachable"
        :param start: (x,y) tuple, start location
        :param max_distance: maximum distance to consider
        :yields: (x,y) positions that can be reached
        '''
        frontier = lch.PriorityQueue(start)
        came_from = {start: (None,0)}
        already_seen = set()

        while not frontier.empty:
            current = frontier.get()
            yield current
            alread_seen.add(current)
            for _next, differential_cost in self.cache[current].move_cost.items():
                if _next.position in already_seen or differential_cost == -1:
                    continue
                _next = _next.position
                new_cost = cost_so_far[current] + differential_cost
                if (new_cost < max_distance and 
                        (_next not in came_from or new_cost < came_from[_next][1])):
                    cost_so_far[_next] = new_cost
                    frontier.put(_next, new_cost)
                    came_from[_next] = current

