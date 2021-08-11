import lch

class Game(object):
    """
    """
    def __init__(self, team1, team2):
        size_x, size_y = 24, 16
        self.bf = lch.Battlefield(size_x, size_y, lambda x,y: (1, 0))
        self.teams = [team1, team2]
        for i,model in enumerate(team1.models):
            model.position = (i, 0)
        for i,model in enumerate(team2.models):
            model.position = (size_x-1-i, size_y-1)
        self.max_turns = 6

    def start_of_turn(self, turn_i):
        print(f'Start of turn {turn_i}')
        for team in self.teams:
            team.ready_up()

    def end_of_turn(self, turn_i):
        print(f'End of turn {turn_i}')

    def determine_victory(self, turn_i):
        return turn_i >= 6 or self.teams[0].is_dead() or self.teams[1].is_dead()

    def turn(self, turn_i):
        other_team_actions = 0
        turn_finished = False
        while not turn_finished:
            for t in range(2):
                actions = []
                for model in self.teams[t].models:
                    actions += model.possible_actions(self.teams[t], self.teams[t^1], self.bf)

                print(f'Team {t} made {len(actions)} actions')
                if len(actions) == 0 and other_team_actions == 0:
                    # neither team has actions left
                    turn_finished = True
                    break
                if other_team_actions := len(actions) == 0:
                    continue

                self.teams[t].AI.select_action(actions).engage()

            # t in teams
        return

    def game_loop(self):
        print('Starting game loop!')
        for i in range(self.max_turns):
            self.start_of_turn(i)
            self.turn(i)
            self.end_of_turn(i)
            if self.determine_victory(i):
                break

