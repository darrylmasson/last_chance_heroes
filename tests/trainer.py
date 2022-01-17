import lch
from test_inst import *
import argparse
import tqdm
import itertools
import os
from concurrent.futures import ProcessPoolExecutor as pool_exec
import signal
from collections import defaultdict

def play(game):
    return game.game_loop()

class SignalHandler(object):
    def __init__(self):
        self.run = True
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

    def interrupt(self, *args):
        self.run = False

sh = SignalHandler()

def generation_multithread(teams, ais, rounds, workers):
    results = defaultdict(int)
    n_games = (rounds * len(ais) * (len(ais)-1) // 2)
    while sh.run == True:
        for _ in range(rounds):
            size_x, size_y = 20, 12
            bf = lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y))
            games = []
            for ai in itertools.combinations(ais, 2):
                # generate a game of each AI against each other AI on this map
                games.append(lch.Game(teams, ai, bf))
        try:
            with pool_exec(max_workers=workers) as executor:
                for (i,j) in executor.map(play, games):
                    results[i] += 1
                    if not sh.run:
                        break
        except Exception as e:
            tqdm.tqdm.write(f'Caught a {type(e)}: {e}, continuing')
        if sum(results.values()) == n_games:
            break
    return results

def generation_singlethread(teams, ais, rounds):
    results = defaultdict(int)
    games = []
    for _ in range(rounds):
        # generate a map
        size_x, size_y = 20, 12
        bf = lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y))

        for ai in itertools.combinations(ais, 2):
            # generate a game of each AI against each other AI on this map
            games.append(lch.Game(teams, ai, bf))

    for g in tqdm.tqdm(games, leave=False, desc='Games'):
        results[g.game_loop()[0]] += 1
        if not sh.run:
            break

    return results

def main():
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

    teams = ['8f74e6', '8f0bbc']

    for gen_i in tqdm.trange(args.generations, desc='Generations'):
        if gen_i == 0:
            ais = [lch.DenseMultilayer.from_scratch() for _ in range(args.agents)]
        else:
            ais = [winner] + [winner.mutate() for _ in range(args.agents//2)] + [lch.DenseMultilayer.from_scratch() for _ in range(args.agents//2)]

        for ai in ais:
            try:
                lch.store_in_cache('ai', ai.encode())
            except:
                pass
        ais = [ai.hash for ai in ais]

        # fight to the death for our amusement
        if args.threads > 1:
            results = generation_multithread(ais, teams, args.rounds, args.threads)
        else:
            results = generation_singlethread(ais, teams, args.rounds)

        top_hash, top_wins = None, 0
        for k, v in results.items():
            if v > top_wins:
                top_hash = k
                top_wins = v

        # losers get forgotten
        for ai in ais:
            if ai != top_hash:
                lch.remove_from_cache('ai', ai)
            else:
                winner = lch.AI.from_hash(ai)

if __name__ == '__main__':
    main()
