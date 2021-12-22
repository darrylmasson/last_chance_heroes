import lch
from test_inst import *
import numpy as np
import argparse
import tqdm
import itertools
import os
from concurrent.futures import ProcessPoolExecutor as pool_exec
import signal
from collections import defaultdict

use_tqdm=True

def play(game):
    return game.game_loop()

class SignalHandler(object):
    def __init__(self):
        self.run = True

    def interrupt(self, *args):
        self.run = False

def play_games(gen_i, ais, rounds, workers, log_kwargs):
    wins = []
    map_pool = []
    it = tqdm.trange(rounds, leave=False, desc='Making maps') if use_tqdm else range(rounds)
    for i in it:
        lch.Forest.init()
        size_x, size_y = 24, 12
        paths = (size_x * size_y) * (size_x * size_y - 1) // 2
        map_pool.append(lch.Battlefield(size_x, size_y, lch.forest))
        #map_pool[-1].fill_astar_cache(leave=False, desc='Precomputing A*', total=paths)

    games = []
    for (i,j) in itertools.combinations(ais, 2):
        # generate a game of each AI against each other AI on this generation's
        # map pool.
        for bf in map_pool:
            t1 = TestTeam1(i)
            t2 = TestTeam1(j) # walk before you run
            games.append(lch.Game(t1, t2, bf))
    if workers == 1:
        it = tqdm.tqdm(games, leave=False, desc='Games') if use_tqdm else games
        for g in it:
            wins.append(g.game_loop())
    else:
        with pool_exec(max_workers=workers) as executor:
            for (i,j) in executor.map(play, games):
                wins.append((i,j))
    return wins

def mutate(parent, step=0.01):
    hc_change = step*(np.random.random(size=parent.hidden_controls.shape) - 0.5)
    hb_change = step*(np.random.random(size=parent.hidden_bias.shape) - 0.5)
    oc_change = step*(np.random.random(size=parent.output_controls.shape) - 0.5)
    ob_change = step*(np.random.random(size=parent.output_bias.shape) - 0.5)
    top_n_change = np.random.choice([-1,0,1], p=[0.01, 0.98, 0.01])

    return lch.SimpleAI(hidden_controls = parent.hidden_controls + hc_change,
                hidden_bias = parent.hidden_bias + hb_change,
                output_controls = parent.output_controls + oc_change,
                output_bias = parent.output_bias + ob_change,
                top_n = parent.top_n + top_n_change,
                parent_hash = parent.hash)

def main(f):
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', default=10, type=int, help='Number of games per agent pairing')
    parser.add_argument('--agents', default=10, type=int, help='Number of agents per generation. This is quadratic on runtime. Minimum 5')
    parser.add_argument('--generations', default=10, type=int, help='Number of generations')
    parser.add_argument('--threads', default=1, help='Number of CPUs to train with. Int or "all"')
    parser.add_argument('--no-tqdm', action='store_true', help='Don\'t use tqdm')
    parser.add_argument('--printlog', choices='trace debug info warning error critical'.split(), help='Log level to print', default='info')
    parser.add_argument('--filelog', choices='trace debug info warning error critical'.split(), help='Log level to write to file', default='debug')

    #sh = SignalHandler()
    #signal.signal(signal.SIGINT, sh.interrupt)
    #signal.signal(signal.SIGTERM, sh.interrupt)

    args = parser.parse_args()
    global use_tqdm
    use_tqdm = not args.no_tqdm
    if args.threads in ['all', 'max']:
        args.threads = os.cpu_count()
    else:
        args.threads = int(args.threads)
    args.agents = max(5, args.agents)
    N = lch.SimpleAI.action_fields
    nodes = 12
    top2 = [lch.SimpleAI(hidden_controls=np.random.random(size=(nodes, N)),
        hidden_bias=np.random.random(size=(nodes, 1)),
        output_controls=np.random.random(size=(1, nodes)),
        output_bias=np.random.random(size=(1,1)),
        top_n=np.random.randint(3,6)) for _ in range(2)]

    children = [max(2, 2*args.agents//3), max(1, args.agents//3)]

    fmt = f'0{int(np.ceil(np.log10(args.generations)))}d'
    it = tqdm.trange(args.generations, desc='Generations') if use_tqdm else range(args.generations)
    log_kwargs = {'f': f, 'printlevel': args.printlog, 'filelevel': args.filelog}
    for gen_i in it:
        #if not sh.run:
        #    break
        # make this generation's agents by mutating the best two
        ais = top2
        for a,c in zip(top2, children):
            ais += [mutate(a) for _ in range(c)]

        # fight to the death for our amusement
        wins = play_games(gen_i, ais, args.rounds, args.threads, log_kwargs)
        results = defaultdict(int)

        # determine who won the most
        for w,_ in wins:
            results[w] += 1
        top_hash, top_wins = None, 0
        for k,v in results.items():
            if v > top_wins:
                top_hash = k
                top_wins = v
        top2 = [ai for ai in ais if ai.hash == top_hash]
        second_hash, second_wins = None, 0
        for k,v in results.items():
            if v > second_wins and v != top_wins:
                second_hash = k
                second_wins = v
        top2 += [ai for ai in ais if ai.hash == second_hash]

        # immortalize
        for ai in top2:
            np.savez_compressed(
                    f'generations/{gen_i:{fmt}}_{ai.hash}_{ai.parent_hash}.npz',
                    hc=ai.hidden_controls,
                    hb=ai.hidden_bias,
                    oc=ai.output_controls,
                    ob=ai.output_bias,
                    topn=ai.top_n)

if __name__ == '__main__':
    with open('logs/test.log', 'w') as f:
        main(f)
