import lch
import sqlite3 as sql
import argparse

__all__ = 'Game'.split()

class Game(object):
    """
    """
    def __init__(self, teams, ais, bf):
        self.bf = bf
        self.teams = list(map(lch.Team.from_hash, teams))
        self.teams[0].AI = lch.AI.from_hash(ais[0])
        self.teams[1].AI = lch.AI.from_hash(ais[1])
        for i,model in enumerate(self.teams[0].models):
            model.position = (0, i)
        for i,model in enumerate(self.teams[1].models):
            model.position = (bf.size[0]-1, bf.size[1]-1-i)
        self.max_turns = 12
        self.winning_team = -1
        self.hash = lch.get_hash(bf.hash, *teams, *ais)
        self.logger = lch.get_logger('game', self.hash)
        self.logger.debug(f'Game based on {bf.hash} {teams[0]} {teams[1]}')
        self.db_setup()
        # setup initial conditions
        self.replay = []
        for team in self.teams:
            for model in team.models:
                self.add_to_replay(0, 0, model.get_snapshot())

    def __del__(self):
        self.connection.executemany('INSERT INTO replay VALUES (?,?,?,?,?,?,?);', self.replay)
        self.connection.commit()
        self.connection.close()

    def db_setup(self):
        self.connection = sql.connect(f'games/game_{self.hash}.db')
        self.connection.execute("""CREATE TABLE battlefield (
            x INTEGER,
            y INTEGER,
            move REAL,
            los REAL);""")
        for row in self.bf.encode():
            self.connection.execute('INSERT INTO battlefield VALUES (?,?,?,?);', row)
        #lch.Team.create_table(self.connection)
        #for t in self.teams:
        #    args = t.encode(True)
        #    q = ','.join('?'*len(args))
        #    self.connection.execute(f'INSERT INTO team VALUES ({q});', args)
        self.connection.execute("""CREATE TABLE replay (
            turn INTEGER,
            step INTEGER,
            hash TEXT,
            current_health INTEGER,
            status TEXT,
            x INTEGER,
            y INTEGER);""")
        self.connection.commit()

    def add_to_replay(self, turn_i, step, snapshot):
        self.replay.append((turn_i, step, *snapshot))
        #        (turn_i, step, *snapshot))

    def start_of_turn(self, turn_i):
        self.logger.debug(f'Starting turn {turn_i}')
        for team in self.teams:
            team.ready_up()

    def end_of_turn(self, turn_i):
        self.logger.debug(f'Ending turn {turn_i}')
        pass

    def determine_victory(self, turn_i):
        if turn_i > self.max_turns or self.teams[0].is_dead() or self.teams[1].is_dead():
            return True
        return False

    def turn(self, turn_i):
        other_team_actions = 1 # start nonzero
        turn_finished = False
        step = 0
        while not turn_finished:
            for t in range(2):
                actions = self.teams[t].generate_actions(self.teams[t^1], self.bf)
                if len(actions) == 0 and other_team_actions == 0:
                    # neither team has actions left
                    turn_finished = True
                    break
                other_team_actions = len(actions)

                if len(actions) > 0:
                    self.logger.trace(f'Turn {turn_i} team {t} actions {len(actions)}')
                    action = self.teams[t].AI.select_action(actions)
                    action.engage()

                # save current state
                for model in self.teams[t].models:
                    self.add_to_replay(turn_i, step, model.get_snapshot())
                for model in self.teams[t^1].models:
                    self.add_to_replay(turn_i, step, model.get_snapshot())
            step += 1

        return

    def game_loop(self):
        for i in range(1, self.max_turns+1):
            self.start_of_turn(i)
            self.turn(i)
            self.end_of_turn(i)
            if self.determine_victory(i):
                break
        w = int(self.teams[0].strength() < self.teams[1].strength())
        self.connection.commit()
        return self.teams[w].AI.hash, self.teams[w^1].AI.hash

if __name__ == '__main__':
    team = ['37077a']*2
    ais = ['05253e', '083020']
    size_x, size_y = 24,18
    g = Game(team, ais, lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y)))
    print('Starting game')
    g.game_loop()
    print('All done')
