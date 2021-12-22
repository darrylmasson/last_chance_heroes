import itertools
import datetime
import logging
import hashlib
from functools import partial
from enum import IntEnum

__all__ = 'get_hash get_logger PriorityQueue'.split()

def get_hash(*args, hash_length=6):
    m = hashlib.sha256()
    for arg in args:
        m.update(str(arg).encode())
    return m.hexdigest()[:hash_length]

class LogLevels(IntEnum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5

class ScratchLogger(object):
    """
    From scratch because the python logging
    isn't working?
    """
    def __init__(self, printlevel='info', filelevel='debug', module=None, _hash=None, f=None):
        self.module = module
        self.hash = _hash
        self.f = f
        self.printlevel = LogLevels[printlevel.upper()]
        self.filelevel = LogLevels[filelevel.upper()]
        for lvl in 'trace debug info warning error critical'.split():
            setattr(self, lvl, partial(self.log, lvl.upper()))

    def log(self, level, msg):
        now = datetime.datetime.now()
        m = (f'{now.isoformat(sep=" ")} | '
             f'{self.module} | '
             f'{level} | '
             #f'{record.funcName} | '
             #f'{record.lineno} | '
             f'{msg}')
        if LogLevels[level] >= self.filelevel and self.f is not None:
            self.f.write(m + '\n')
            self.f.flush()
        if LogLevels[level] >= self.printlevel:
            print(m)

class LogHandler(logging.Handler):
    def __init__(self, module, game_hash):
        logging.Handler.__init__(self)
        self.module = module
        self.f = open(f'logs/test.log', 'w')

    def __del__(self):
        self.f.close()

    def emit(self, record):
        msg_datetime = datetime.datetime.fromtimestamp(record.created)
        m = (f'{msg_datetime.isoformat(sep=" ")} | '
             f'{self.module} | '
             f'{str(record.levelname).upper()} | '
             f'{record.funcName} | '
             f'{record.lineno} | '
             f'{record.getMessage()}')
        self.f.write(m + '\n')
        self.f.flush()
        #if record.level >= logging.INFO:
        print(m)

def get_logger(module, game_hash, f=None):
    return ScratchLogger(module=module, _hash=game_hash)


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
        the priority because usually we don't care
        """
        return self.q.pop(0)[0]

    @property
    def empty(self):
        """
        Returns whether or not the queue is currently empty
        """
        return len(self.q) == 0

