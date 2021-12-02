import lch
from test_inst import *
import numpy as np
import argparse
import tqdm
import itertools
from concurrent.futures import ProcessPoolExecutor

def play_games(gen_i, ais, rounds, workers):
    wins = []
    map_pool = []
    for i in range(rounds):
        lch.Forest.init()
        map_pool.append(lch.Battlefield(24, 12, lch.forest))

    games = []
    for (i,j) in itertools.product(range(len(ais)), repeat=2):
        # generate a game of each AI against each other AI on this generation's
        # map pool.
        if i == j:
            continue
        for bf in map_pool:
            t1 = TestTeam1()
            t1.AI = ais[i]
            t2 = TestTeam1() # walk before you run
            t2.AI = ais[j]
            games.append(lch.Game(t1, t2, bf))
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for (i,j) in executor.map(lambda g: g.game_loop(), games):
            wins.append((i,j))
    return np.array(wins, dtype=[('winner', np.int16),('loser', np.int16)])

def mutate(parent, step=0.01, name):
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
                name=name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', default=10, type=int, help='Number of games per agent pairing')
    parser.add_argument('--agents', default=10, type=int, help='Number of agents per generation. This is quadratic on runtime')
    parser.add_argument('--generations', default=10, type=int, help='Number of generations')
    parser.add_argument('--threads', default=os.cpu_count(), type=int, help='Number of CPUs to train with')

    args = parser.parse_args()
    N = lch.SimpleAI.action_fields
    nodes = 12
    winningest_ai = lch.SimpleAI(hidden_controls=np.random.random(size=(nodes, N)),
        hidden_bias=np.random.random(size=(nodes, 1)),
        output_controls=np.random.random(size=(1, nodes)),
        output_bias=np.random.random(size=(1,1)),
        top_n=np.random.randint(3,6),
        name=0)

    fmt = f'0{int(np.ceil(np.log10(args.generations)))}d'
    for gen_i in tqdm.trange(args.generations, desc='Generations'):
        # make this generation's agents by mutating the best one
        winningest_ai.name = 0
        ais = [winningest_ai] + [mutate(winningest_ai, name=i+1) for i in range(args.agents-1)]

        # fight to the death for our amusement
        results = play_games(gen_i, ais, args.rounds, args.threads)

        # determine who won the most
        wins, _ = np.histogram(results['winner'], bins=np.arange(0, args.agents+1))
        winningest_ai = ais[np.argmax(wins)]

        # immortalize the winner
        np.savez_compressed(f'generations/{gen_i:{fmt}}.npz',
                hc=winningest_ai.hidden_controls,
                hb=winningest_ai.hidden_bias,
                oc=winningest_ai.output_controls,
                ob=winningest_ai.output_bias,
                topn=winningest_ai.top_n)

if __name__ == '__main__':
    main()
