import itertools
from enum import IntEnum
import datetime

class LogLevel(IntEnum):
    trace=0,
    detailed=1,
    debug=2,
    info=3,
    warning=4,
    error=5,
    fatal=6

class Logger(object):
    """
    Custom logging class because reasons
    """
    level = LogLevel.debug
    def __init__(self, module):
        self.module = module

    def entry(self, level, message):
        if LogLevel[level] >= self.level:
            print(f'{datetime.datetime.now().isoformat(sep=" ")} | {level.upper()} | {message}')


class PriorityQueue(object):
    """
    Class that implements a priority queue to support pathfinding. We want
    something that takes the lowest priority rather than the highest so
    we write it ourselves
    """
    def __init__(self, x, p=0, logger=None):
        """
        Constructor
        :param x: the first item for the queue
        :param p: float, the priority, default 0
        """
        self.q = [(x,p)]
        self.logger = logger

    def log(self, level, message):
        if self.logger is not None:
            self.logger.entry(level, message)

    def put(self, x, p):
        """
        Puts a new item into the queue so that it's still sorted. The queue
        is guaranteed to have stuff in it so we don't check first
        :param x: the item
        :param p: float, the priority
        :returns: None
        """
        LARGE_NUMBER = 1e12 # if you actually get real numbers this high, increase
        if len(self.q) == 1:
            if self.q[0][1] >= p:
                self.q.insert(0, (x,p))
            else:
                self.q.append((x,p))
        else:
            idx = len(self.q)//2
            for i in itertools.count(2):
                lesser = self.q[idx-1][1] if idx > 0 else -1
                greater = self.q[idx][1] if idx < len(self.q) else LARGE_NUMBER
                if lesser <= p <= greater:
                    self.log('trace', f'Inserting item {p:.1f} before {idx} ({lesser:.1f},{greater:.1f})')
                    self.q.insert(idx, (x,p))
                    return
                elif p > greater:
                    idx += max(1, len(self.q)>>i)
                elif p < lesser:
                    idx -= max(1, len(self.q)>>i)

    def get(self):
        """
        Returns the item with the lowest score (aka the first item). Does not return
        the priority
        """
        return self.q.pop(0)[0]

    @property
    def empty(self):
        """
        Returns whether or not the queue is currently empty
        """
        return len(self.q) == 0

