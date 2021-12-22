import lch

__all__ = 'Game'.split()

class Game(object):
    """
    """
    def __init__(self, team1, team2, bf):
        size_x, size_y = bf.size
        self.bf = bf
        self.teams = [team1, team2]
        for i,model in enumerate(team1.models):
            model.position = (0, i)
        for i,model in enumerate(team2.models):
            model.position = (size_x-1, size_y-1-i)
        self.max_turns = 12
        self.winning_team = -1
        self.hash = lch.get_hash(bf.hash, team1.hash, team2.hash)
        self.logger = lch.get_logger('game', self.hash)
        self.logger.debug(f'Game based on {bf.hash} {team1.hash} {team2.hash}')

    def start_of_turn(self, turn_i):
        self.logger.debug(f'Starting turn {turn_i}')
        for team in self.teams:
            team.ready_up()

    def end_of_turn(self, turn_i):
        self.logger.debug(f'Ending turn {turn_i}')
        pass

    def determine_victory(self, turn_i):
        if turn_i >= self.max_turns or self.teams[0].is_dead() or self.teams[1].is_dead():
            return True
        return False

    def turn(self, turn_i):
        other_team_actions = 0
        turn_finished = False
        while not turn_finished:
            for t in range(2):
                actions = []
                for model in self.teams[t].models:
                    actions += model.possible_actions(self.teams[t], self.teams[t^1], self.bf)
                if len(actions) == 0 and other_team_actions == 0:
                    # neither team has actions left
                    turn_finished = True
                    break
                other_team_actions = len(actions)

                if len(actions):
                    self.logger.trace(f'Turn {turn_i} team {t} actions {len(actions)}')
                    action = self.teams[t].AI.select_action(actions)
                    action.engage()

        return

    def game_loop(self):
        for i in range(self.max_turns):
            self.start_of_turn(i)
            self.turn(i)
            self.end_of_turn(i)
            if self.determine_victory(i):
                break
        w = int(self.teams[0].strength() < self.teams[1].strength())
        return self.teams[w].AI.hash, self.teams[w^1].AI.hash

