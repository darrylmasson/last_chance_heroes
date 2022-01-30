import lch
import sqlite3 as sql
import time
from scipy.stats import norm


__all__ = 'Game'.split()

class Game(object):
    """
    The master class representing one game between two teams on one battlefield
    :param teams: an iterable containing two hashes of teams stored in the cache
    :param ais: an iterable containing two hashes of AIs stored in the cache
    :param bf: a Battlefield instance
    :param store: bool, store a replay of this game. Default False.
    """
    def __init__(self, teams, ais, bf, store=False):
        self.bf = bf
        self.teams = list(map(lch.Team.from_hash, teams))
        for i in range(2):
            self.teams[i].AI = None if ais[i] is None else lch.AI.from_hash(ais[i])
        for i,model in enumerate(self.teams[0].models):
            xy = (0, i)
            model.coords = xy
            self.bf.cache[xy].model = model
        for i,model in enumerate(self.teams[1].models):
            xy = (bf.size[0]-1, bf.size[1]-1-i)
            model.coords = xy
            self.bf.cache[xy].model = model
        self.max_turns = 12
        self.winning_team = -1
        self.hash = lch.get_hash(bf.hash, *teams, *ais)
        self.logger = lch.get_logger('game', self.hash)
        self.logger.debug(f'Game based on {bf.hash} {teams[0]} {teams[1]}')
        self.store = store
        # setup initial conditions
        self.db_setup()
        self.replay = []
        for team in self.teams:
            for model in team.models:
                self.add_to_replay(0, 0, model.get_snapshot())

    def __del__(self):
        if not self.store:
            return
        self.connection.executemany('INSERT INTO replay VALUES (?,?,?,?,?,?,?);', self.replay)
        self.connection.commit()
        self.connection.close()

    def db_setup(self):
        if not self.store:
            return
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

    def engage_action(self, action):
        print(f'Engaging action for {action.model.name}')
        action.model.status = 'activated'
        if isinstance(action, lch.MoveAction):
            print(f'Moving {action.model.name} from {action.model.coords} to {action.move_dest}')
            self.move_model(action.model, action.move_dest)
        if isinstance(action, lch.ShootAction):
            print(f'{action.model.name} shooting at {action.target.name}')
            self.shoot_action(action)
        elif isinstance(action, lch.MeleeAction):
            print(f'{action.model.name} stabbing {action.target.name}')
            self.melee_action(action)

    def move_model(self, model, destination):
        model.coords = destination

    def do_damage(self, defender, weapon, hits, shot_dist=0):
        """
        Do some damage against a defender with a weapon
        :param defender: a Model
        :param weapon: the Weapon in question
        :param hits: how many times to roll damage
        :returns: None
        """
        effective_armor = max(defender.armor - weapon.punch, 0)
        tot_damage = 0
        damage = []
        for _ in range(hits):
            damage.append(max(weapon.damage(shot_dist) - effective_armor, 0))
            defender.current_health -= damage[-1]
            if defender.current_health <= 0:
                defender.status = 'dead'
                defender.current_health = 0
                defender.coords = (-1, -1)
                print(f'Killed {defender.name}')
                return f'killed {defender.name}'
        s = f'Did {"/".join(map(str, damage))} to {defender.name}'
        print(s)
        return s

    def shoot_action(self, action):
        attacker = action.model
        defender = action.target
        start, end = attacker.coords, defender.coords
        shot_dist = self.bf.distance(start, end)
        penalty = attacker.rw.penalty(action.move_dist, action.shot_dist)
        if penalty is None:
            return "Can\'t move and shoot a heavy weapon"
        print(f'Penalty: {penalty}')
        attacks = attacker.rw.attacks
        hit_rolls = norm.rvs(loc=attacker.rs, scale=attacker.rc, size=attacks)
        target_num = defender.dodge + sum(penalty)*attacker.rc
        hits = sum(hit_rolls > target_num)
        hit_rolls = [f'{x:.1f}' for x in hit_rolls]
        s = f'Attack skill {attacker.rs}/{attacker.rc}, rolls {hit_rolls}, target {target_num:.1f}. '
        if hits == 0:
            print(s + f"No hits")
            return s + f"No hits"
        s += f"{hits} hits, " + self.do_damage(defender, attacker.rw, hits, shot_dist)
        print(s)
        return s

    def melee_action(self, action):
        attacker = action.model
        defender = action.target
        charged = isinstance(action, lch.MoveAction)
        bonus = attacker.mc * (action.move_dist > 0)
        attacks = attacker.mw.attacks
        attack_roll = norm.rvs(loc=attacker.ms, scale=attacker.mc, size=attacks) + bonus
        defense_roll = norm.rvs(loc=defender.ms, scale=defender.mc, size=attacks)
        hits = sum(attack_roll > defense_roll)
        attack_roll = [f'{x:.1f}' for x in attack_roll]
        defense_roll = [f'{x:.1f}' for x in defense_roll]
        s = f'Skill {attacker.ms}/{attacker.mc} vs {defender.ms}/{defender.mc}, rolls {attack_roll}/{defense_roll} '
        if hits == 0:
            return s + f'no hits'
        return s + f"{hits} hits, " + self.do_damage(defender, attacker.mw, hits)

    def do_team_action(self, team_i):
        """
        Selects an action from an AI team
        :param team_i: 0 or 1
        :returns: None, or the Action that was taken
        """
        actions = self.teams[team_i].generate_actions(self.teams[team_i^1], self.bf)
        if len(actions) == 0:
            return None
        action = self.teams[team_i].AI.select_action(actions)
        self.engage_action(action)
        action.model.status = 'activated'
        return action

    def turn(self, turn_i):
        other_team_action = 1 # start nonzero
        turn_finished = False
        step = 0
        while not turn_finished:
            for t in range(2):
                this_team_action = self.do_team_action(t)
                if this_team_action is None and other_team_action is None:
                    turn_finished = True
                    break
                other_team_action = this_team_action

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
        return self.teams[w].AI.hash, self.teams[w^1].AI.hash

if __name__ == '__main__':
    team = ['8f74e6', '8f0bbc']
    ais = ['6edfda', '6edfda']
    size_x, size_y = 24,18
    t_start = time.perf_counter()
    g = Game(team, ais, lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y)))
    print(f'Starting game, setup took {time.perf_counter()-t_start:.2f} s')
    t_start = time.perf_counter()
    g.game_loop()
    print(f'All done, game took {time.perf_counter()-t_start:.2f} s')
