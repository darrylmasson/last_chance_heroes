import lch
from test_inst import *
import argparse
import tqdm
import itertools
import os
from concurrent.futures import ProcessPoolExecutor as pool_exec
import signal
from collections import defaultdict

def play_game(game):
    return game.game_loop()

class SignalHandler(object):
    def __init__(self):
        self.run = True

    def interrupt(self, *args):
        self.run = False

sh = SignalHandler()
signal.signal(signal.SIGINT, sh.interrupt)
signal.signal(signal.SIGTERM, sh.interrupt)

def do_generation(seed_hash, teams, children, rounds, workers):
    results = defaultdict(int)
    games = []
    ais = [lch.AI.from_hash(seed_hash)]
    ais += [ais[0].mutate() for _ in range(children)]
    for ai in ais[1:]:
        lch.store_in_cache('ai', ai.hash, ai.encode())
    ais = [ai.hash for ai in ais]
    for _ in range(rounds):
        # generate a map
        size_x, size_y = 24, 18
        bf = lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y))
        #num_paths = (size_x * size_y) * (size_x * size_y - 1) // 2
        #bf.fill_astar_cache(leave=False, desc='A*', total=num_paths)

        for ai in itertools.combinations(ais, 2):
            # generate a game of each AI against each other AI on this map
            games.append(lch.Game(teams, ai, bf))

    if workers == 1:
        it = tqdm.tqdm(games, leave=False, desc='Games')
        for g in it:
            results[g.game_loop()[0]] += 1
            if not sh.run:
                break
    else:
        with pool_exec(max_workers=workers) as executor:
            for (i,j) in executor.map(play, games):
                results[i] += 1
                if not sh.run:
                    break

    top_hash, top_wins = None, 0
    for k, v in results.items():
        if v > top_wins:
            top_hash = k
            top_wins = v

    # losers get forgotten
    for ai in ais:
        if ai != top_hash:
            lch.remove_from_cache('ai', ai)
    return top_hash

def main(f):
    parser = argparse.ArgumentParser(description=('A training program for Last Chance '
        'Heroes. Each generation, a number of AIs are created equal to the '
        '"agents" argument, and a number of maps equal to the "rounds" argument. '
        'Each AI plays each other AI on each map, so the number of games per '
        'generation is rounds * agents * (agents-1)/2. The AI that wins the most '
        'in one generation is mutated to form the agents for the next generation. '
        'The winner is immortalized while the losers are forgotten. '
        'This is bloodsport, you win or you die'))
    parser.add_argument('--rounds', default=5, type=int, help='Number of games per agent pairing')
    parser.add_argument('--agents', default=5, type=int, help='Number of agents per generation.')
    parser.add_argument('--generations', default=5, type=int, help='Number of generations')
    parser.add_argument('--threads', default=1, help='Number of CPUs to train with. Int or "all"')
    parser.add_argument('--start-from', type=str, default='scratch',
            help='An AI to start from. "scratch" or a hash')

    args = parser.parse_args()
    if args.threads in ['all', 'max']:
        args.threads = os.cpu_count()
    else:
        args.threads = int(args.threads)
    if args.start_from == 'scratch':
        top_hash = setup_ais()
    else:
        top_hash = args.start_from

    teams = ['37077a']*2

    for gen_i in tqdm.trange(args.generations, desc='Generations'):
        # fight to the death for our amusement
        top_hash = do_generation(top_hash, teams, args.agents-1, args.rounds, args.threads)

if __name__ == '__main__':
    with open('logs/test.log', 'w') as f:
        main(f)
