import lch
import tkinter as tk
from tkinter import ttk
import time


class UI(lch.Game):
    """
    Now with something resembling a user interface
    """
    def __init__(self, teams, ais, bf, store=False):
        super().__init__(teams, ais, bf, store)
        self.teams[0].color='red'
        self.teams[1].color='cyan'

    def bf_to_px(self, val):
        offset_bf = -0.5
        scale = self.canvas_x/(self.bf.size[0]+1)
        offset_px = 10
        return scale*(val[0]-offset_bf)+offset_px, scale*(val[1]-offset_bf)+offset_px

    def px_to_bf(self, val):
        offset_bf = -0.5
        scale = self.canvas_x/(self.bf.size[0]+1)
        offset_px = 10
        x = round((val[0]-offset_px)/scale+offset_bf)
        y = round((val[1]-offset_px)/scale+offset_bf)
        return x, y

    def draw_bf(self):
        # outline
        self.canvas.create_line(
                *self.bf_to_px((-0.5, -0.5)),
                *self.bf_to_px((-0.5, self.bf.size[1]-0.5)),
                *self.bf_to_px((self.bf.size[0]-0.5, self.bf.size[1]-0.5)),
                *self.bf_to_px((self.bf.size[0]-0.5, -0.5)),
                *self.bf_to_px((-0.5, -0.5)),
                width=3)
        for (x,y), sq in self.bf.cache.items():
            # obstructed squares
            if sq.move_scale != -1:
                continue
            dx = dy = 0.45
            self.canvas.create_rectangle(
                    *self.bf_to_px((x-dx, y-dy)),
                    *self.bf_to_px((x+dx, y+dy)),
                    fill='green')

        bf_x, bf_y = self.bf.size
        self.sq = [[None for _ in range(bf_y)] for _ in range(bf_x)]
        self.txt = [[None for _ in range(bf_y)] for _ in range(bf_x)]
        for (x,y), sq in self.bf.cache.items():
            # unobstructed squares
            if sq.move_scale == -1:
                continue
            dx = 0.45
            dy = 0.45
            self.sq[x][y] = self.canvas.create_rectangle(
                    *self.bf_to_px((x-dx, y-dy)),
                    *self.bf_to_px((x+dx, y+dy)),
                    fill=None)
            self.txt[x][y] = self.canvas.create_text(
                    *self.bf_to_px((x,y)), text="")
        self.highlighted_squares = []
        self.selected_model = None
        self.canvas.bind('<Button-1>', self.single_click)
        self.canvas.bind('<Double-Button-1>', self.double_click, add='+')

    def clear_visualization(self):
        self.canvas.delete('move_vis')
        self.canvas.delete('path_vis')
        self.canvas.delete('los_vis')
        self.selected_model = None
        self.selected_square = None
        self.highlighted_squares = []

    def coords_to_model(self, coords):
        for t in self.teams:
            for m in t:
                if m.coords == coords:
                    return m

    def top_of_turn(self):
        self.clear_visualization()
        for t in self.teams:
            for m in t:
                if m.status != 'dead':
                    m.status = 'ready'
                    self.set_square(*m.coords, m)

    def double_click(self, event):
        coords = self.px_to_bf((event.x, event.y))
        action = None
        if self.selected_model is None:
            return
        if coords in self.teams[1].coordinates():
            # selected an enemy
            target = self.coords_to_model(coords)
            c = self.selected_square or self.selected_model.coords
            if c == self.selected_model.coords:
                # not moving
                if c in self.bf.adjacent(target.coords):
                    print('Making a melee attack')
                    action = lch.MeleeAction(model=self.selected_model, target=target,
                            bf=self.bf)
                else:
                    print('Making a ranged attack')
                    action = lch.ShootAction(model=self.selected_model, target=target,
                            bf=self.bf)
            else:
                # move and attack
                if self.selected_square in self.bf.adjacent(target.coords):
                    print('Making a charge attack')
                    action = lch.ChargeAction(model=self.selected_model, bf=self.bf,
                            target=target, move_dest=self.selected_square)
                else:
                    print('Making a snap shot')
                    action = lch.SnapShotAction(model=self.selected_model, bf=self.bf,
                            target=target, move_dest=self.selected_square)
        elif coords == self.selected_square:
            print('Making a move action')
            action = lch.MoveAction(model=self.selected_model, bf=self.bf,
                    move_dest=self.selected_square)
        else:
            self.clear_visualization()
        if action is not None:
            self.engage_action(action)
            self.set_square(*action.model.coords, action.model)
            if action.target is not None:
                self.enemy_list[action.target.game_hash] = action.target.text_status()
            self.clear_visualization()
            if (a := self.do_team_action(1)) is not None:
                if a.target is not None:
                    self.friendly_list[action.target.game_hash] = a.target.text_status()
            self.friendly_sv.set(list(self.friendly_list.values()))
            self.friendly_models['width'] = max(len(s) for s in self.friendly_list.values())
            self.enemy_sv.set(list(self.enemy_list.values()))
            self.enemy_models['width'] = max(len(s) for s in self.enemy_list.values())

    def shoot_action(self, action):
        print('Shooting action')
        s = super().shoot_action(action)
        self.text_log.set(s)
        if action.target.status == 'dead':
            self.set_square(*action.target.coords, None)
        else:
            self.set_square(*action.target.coords, action.target)

    def melee_action(self, action):
        print('Melee action')
        s = super().melee_action(action)
        self.text_log.set(s)
        if action.target.status == 'dead':
            self.set_square(*action.target.coords, None)
        else:
            self.set_square(*action.target.coords, action.target)

    def single_click(self, event):
        coords = self.px_to_bf((event.x, event.y))
        print(coords)

        if coords in self.teams[0].coordinates():
            self.clear_visualization()
            m = self.coords_to_model(coords)
            if m.status != 'ready':
                return
            self.selected_model = m
            self.draw_movement(self.selected_model)
            self.draw_los(m.coords)
        elif coords in self.teams[1].coordinates():
            self.selected_enemy = self.coords_to_model(coords)
        elif coords in self.highlighted_squares:
            self.draw_path(self.selected_model, coords)
            self.draw_los(coords)
            self.selected_square = coords
        else:
            self.clear_visualization()

    def draw_path(self, model, coords):
        if model.status != 'ready':
            return
        self.canvas.delete('path_vis')
        p, _ = self.bf.astar_path(model.coords, coords)
        for i, a in enumerate(p[:-1]):
            b = p[i+1]
            x = self.canvas.create_line(
                    *self.bf_to_px(a),
                    *self.bf_to_px(b),
                    dash='4 4',
                    fill='black', tags='path_vis')

    def draw_movement(self, model):
        if model.status != 'ready':
            return
        self.canvas.delete('move_vis')
        self.highlighted_squares = []
        for sq in self.bf.reachable(model.coords, max_distance=model.move, blocked=model.team.coordinates(exclude=model)):
            self.canvas.create_line(
                    *self.bf_to_px((sq[0]-0.48, sq[1]-0.48)),
                    *self.bf_to_px((sq[0]-0.48, sq[1]+0.48)),
                    *self.bf_to_px((sq[0]+0.48, sq[1]+0.48)),
                    *self.bf_to_px((sq[0]+0.48, sq[1]-0.48)),
                    *self.bf_to_px((sq[0]-0.48, sq[1]-0.48)),
                    width=3, fill='black',
                    tags='move_vis')
            self.highlighted_squares.append(sq)

    def draw_los(self, coords):
        if self.selected_model is None:
            print('No model and los?')
            return
        self.canvas.delete('los_vis')
        for e in self.teams[1]:
            if e.status == 'dead':
                continue
            self.canvas.create_line(
                    *self.bf_to_px(coords),
                    *self.bf_to_px(e.coords),
                    dash='2 2',
                    fill='black' if self.bf.los_range(coords,e.coords)[1] >= 0 else 'orange',
                    tags='los_vis')

    def set_square(self, x, y, model):
        if model is None:
            self.canvas.itemconfigure(self.sq[x][y], fill='white')
            self.canvas.itemconfigure(self.txt[x][y], text='')
        else:
            self.canvas.itemconfigure(self.sq[x][y], fill=model.team.color)
            self.canvas.itemconfigure(self.txt[x][y], text=f'{model.name}\n{model.status}\n{model.current_health} hp')

    def move_model(self, model, destination):
        self.clear_visualization()
        x, y = model.coords
        self.set_square(x, y, None)
        model.coords = destination
        x, y = destination
        self.set_square(x, y, model)

    def draw_models(self):
        occupied = []
        for i,team in enumerate(self.teams):
            max_l = 0
            for model in team:
                s = model.text_status()
                max_l = max(max_l, len(s))
                if i == 0:
                    self.friendly_list[model.game_hash] = s
                else:
                    self.enemy_list[model.game_hash] = s
                if model.status == 'dead':
                    continue
                x,y = model.coords
                occupied.append((x,y))
                self.set_square(x, y, model)

            if i == 0:
                self.friendly_sv.set(list(self.friendly_list.values()))
                self.friendly_models['width'] = max_l
            else:
                self.enemy_sv.set(list(self.enemy_list.values()))
                self.enemy_models['width'] = max_l

        for x in range(self.bf.size[0]):
            for y in range(self.bf.size[1]):
                if (x,y) in occupied:
                    continue
                self.set_square(x, y, None)

    def draw_frame(self):
        self.canvas_x = 1500
        canvas_y = self.canvas_x * self.bf.size[1]/self.bf.size[0]
        self.root = tk.Tk()
        frame = ttk.Frame(self.root, borderwidth=5, relief='ridge')

        csbv = tk.Scrollbar(frame, orient=tk.VERTICAL)
        csbh = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        self.canvas = tk.Canvas(frame, borderwidth=1, width=self.canvas_x, height=canvas_y,
                scrollregion=(0, 0, self.canvas_x, canvas_y),
                yscrollcommand = csbv.set, xscrollcommand=csbh.set)
        csbv['command'] = self.canvas.yview
        csbh['command'] = self.canvas.xview

        action_frame = ttk.Labelframe(frame, text='Possible actions')
        self.action_list = []
        self.action_sv = tk.StringVar(value=self.action_list)
        self.action_lb = tk.Listbox(action_frame, width=0, selectmode='single',
                height=65, listvariable=self.action_sv)
        sb = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.action_lb.yview)
        self.text_log = tk.StringVar()
        self.text_log.set("Info log goes here")
        textlog = ttk.Label(frame, width=120, borderwidth=2, textvariable=self.text_log)

        ff = ttk.Labelframe(frame, text='Friendly models')
        self.friendly_list = {}
        self.friendly_sv = tk.StringVar(value=list(self.friendly_list.values()))
        self.friendly_models = tk.Listbox(ff, height=6, listvariable=self.friendly_sv,
                selectmode='single')
        self.enemy_list = {}
        self.enemy_sv = tk.StringVar(value=list(self.enemy_list.values()))
        ef = ttk.LabelFrame(frame, text='Enemy models')
        self.enemy_models = tk.Listbox(ef, height=6, listvariable=self.enemy_sv,
                selectmode='single')

        frame.grid(column=0, row=0, sticky='nw se')
        self.canvas.grid(column=0, row=0, columnspan=2, sticky='nw se')
        csbv.grid(column=2, row=0, sticky='n e s')
        csbh.grid(column=0, row=1, columnspan=2, sticky='w s e')

        action_frame.grid(column=3, row=0, sticky='n e s', rowspan=2)
        self.action_lb.grid(column=0, row=0, sticky='nw se')
        self.action_lb['yscrollcommand'] = sb.set
        sb.grid(column=4, row=0, rowspan=2, sticky='n s w')
        textlog.grid(row=1, column=0, columnspan=2, sticky='nw se')
        ff.grid(row=2, column=0, sticky='nw se')
        ef.grid(row=2, column=1, columnspan=2, sticky='nw se')
        self.friendly_models.grid(row=0, column=0)
        self.enemy_models.grid(row=0, column=0)

        self.end_turn_btn = tk.Button(frame, text='End turn',
                command=self.end_turn)
        self.end_turn_btn.grid(row=2, column=3, sticky='w n e')

        self.root.title('Last Chance Heroes')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def end_turn(self, *args):
        print('Ending turn')
        while self.do_team_action(1):
            time.sleep(1)
        return self.top_of_turn()

    def game_loop(self):
        self.draw_frame()
        self.draw_bf()
        self.draw_models()
        self.root.mainloop()

    def generate_actions(self, model):
        print('Generate actions')
        actions = model.generate_actions(m.team.coordss(exclude=m), self.teams[1], self.bf)
        print(f'Got {len(actions)} actions')
        self.action_list = actions
        self.action_sv.set(list(map(str, actions)))
        return

    def preview_action(self, event):
        if len(idx) == 1:
            idx = int(idx[0])
        else:
            return
        self.action_lb.see(idx)
        action = self.action_list[idx]
        if isinstance(action, lch.MoveAction):
            p, _ = self.bf.astar_path(action.model.coords, action.move_dest)
            for i, a in enumerate(p[:-1]):
                b = p[i+1]
                x = self.canvas.create_line(
                        *self.bf_to_px(a),
                        *self.bf_to_px(b),
                        dash='4 4',
                        fill='black', tags='path_vis')
                self.last_action_vis.append(x)
            enemies = [t for t in self.teams if t != action.model.team][0]
            for e in enemies:
                if e.status == 'dead':
                    continue
                a, b = action.move_dest, e.coords
                x = self.canvas.create_line(*self.bf_to_px(a), *self.bf_to_px(a),
                        dash='2 2',
                        fill='black' if self.bf.los_range(a,b)[1] == 0 else 'orange',
                        tags='path_vis')
                self.last_action_vis.append(x)
        if isinstance(action, lch.AttackAction):
            pass


if __name__ == '__main__':
    teams = ['8f74e6', '8f0bbc']
    ais = ['6edfda', '6edfda']
    size_x, size_y = 20, 12
    g = UI(teams, ais, lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y)))
    g.game_loop()
