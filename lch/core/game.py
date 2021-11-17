import lch


class Game(object):
    """
    """
    def __init__(self, team1, team2, stdscr=None):
        size_x, size_y = 24, 16
        self.bf = lch.Battlefield(size_x, size_y, lch.terrain.forest)
        self.teams = [team1, team2]
        for i,model in enumerate(team1.models):
            model.position = (i, 0)
        for i,model in enumerate(team2.models):
            model.position = (size_x-1-i, size_y-1)
        self.max_turns = 12
        if stdstr is None:
            self.ui = lch.blank_ui()
        else:
            self.ui = lch.ui(stdscr, self.bf)

    def start_of_turn(self, turn_i):
        print(f'Start of turn {turn_i}')
        for team in self.teams:
            team.ready_up()

    def end_of_turn(self, turn_i):
        print(f'End of turn {turn_i}')

    def determine_victory(self, turn_i):
        return turn_i >= self.max_turns or self.teams[0].is_dead() or self.teams[1].is_dead()

    def turn(self, turn_i):
        other_team_actions = 0
        turn_finished = False
        self.ui.draw_bf()
        while not turn_finished:
            for t in range(2):
                self.ui.draw_team(self.teams[0], 1)
                self.ui.draw_team(self.teams[1], 2)
                if len(actions) == 0 and other_team_actions == 0:
                    # neither team has actions left
                    turn_finished = True
                    break
                if other_team_actions := len(actions) == 0:
                    continue

                if self.teams[t].is_human:
                    action = self.ui.choose_action(self.teams[t], self.teams[t^1])
                else:
                    for model in self.teams[t].models:
                        actions += model.possible_actions(self.teams[t], self.teams[t^1], self.bf)

                    action = self.teams[t].AI.select_action(actions)
                self.ui.do_action(action)

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

