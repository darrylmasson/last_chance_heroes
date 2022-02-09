import lch
import tkinter as tk
from tkinter import ttk
import time


__all__ = 'UI'.split()

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

    def start_of_turn(self, turn_i=None):
        self.clear_visualization()
        for i,t in enumerate(self.teams):
            for m in t:
                if m.status != 'dead':
                    m.status = 'ready'
                    self.set_square(*m.coords, m)
                    self.model_disp[i][m.game_hash]['status'].set(m.status)
                    self.model_disp[i][m.game_hash]['health'].set(m.health)

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
            self.clear_visualization()
            if (a := self.do_team_action(1)) is not None:
                d = self.model_disp[1][a.model.game_hash]
                d['status'].set(a.model.status)
                d['health'].set(a.model.health)
                self.set_square(*a.model.coords, a.model)

                if (t := a.target) is not None:
                    d = self.model_disp[0][t.game_hash]
                    d['status'].set(t.status)
                    d['health'].set(t.health)
                    self.set_square(*t.coords, t)

            d = self.model_disp[0][action.model.game_hash]
            d['status'].set(action.model.status)
            d['health'].set(action.model.health)
            self.set_square(*action.model.coords, action.model)

            if (t := action.target) is not None:
                d = self.model_disp[1][t.game_hash]
                d['status'].set(t.status)
                d['health'].set(t.health)
                self.set_square(*t.coords, t)

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
            if self.selected_model is not None:
                se = self.selected_enemy
                sm = self.selected_model
                coords = self.selected_square or sm.coords
                moved = coords != sm.coords
                kw = {'model': sm, 'target': se, 'bf': self.bf}
                if moved:
                    kw['move_dest'] = self.selected_square
                if coords in self.bf.adjacent(se.coords):
                    how = "in melee"
                    c = lch.MeleeAction if not moved else lch.ChargeAction
                else:
                    how = "at range"
                    c = lch.ShootAction if not moved else lch.SnapShotAction
                s = f'Chance for {sm.name} to hit {se.name} {how}: {c(**kw).hit_prob*100:.1f}'
                self.text_log.set(s)
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

    def setup_models(self):
        occupied = []
        for i,team in enumerate(self.teams):
            max_l = 0
            for model in team:
                x,y = model.coords
                occupied.append((x,y))
                self.set_square(x, y, model)

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

        self.text_log = tk.StringVar()
        self.text_log.set("Info log goes here")
        textlog = ttk.Label(frame, width=120, borderwidth=2, textvariable=self.text_log)

        mf = ttk.Frame(frame)
        fields = 'name status move rs rc ms mc dodge armor health mw rw'.split()

        self.model_disp = [
                {m.game_hash: {f: tk.StringVar() for f in fields} for m in t }
                for t in self.teams]

        frame.grid(column=0, row=0, sticky='nw se')
        self.canvas.grid(column=0, row=0, sticky='nw se')
        csbv.grid(column=1, row=0, sticky='n e s')
        csbh.grid(column=0, row=1, sticky='w s e')

        textlog.grid(row=2, column=0, sticky='nw se')

        mf.grid(row=3, column=0, sticky='nw se')
        ff = ttk.LabelFrame(mf, text='Friendlies', borderwidth=1)
        ef = ttk.LabelFrame(mf, text='Enemies', borderwidth=1)
        ff.grid(row=0, column=0, sticky='s w n')
        ef.grid(row=0, column=1, sticky='s e n')
        for i, f in enumerate(fields):
            ttk.Label(ff, text=f.capitalize()).grid(row=0, column=i, sticky='n w e', padx=10)
            ttk.Label(ef, text=f.capitalize()).grid(row=0, column=i, sticky='n w e', padx=10)
        for h, disp in enumerate(self.model_disp):
            for i, d in enumerate(disp.values()):
                for j, sv in enumerate(d.values()):
                    sv.set(getattr(self.teams[h].models[i], fields[j]))
                    ttk.Label([ff, ef][h], textvariable=sv).grid(row=i+1, column=j, padx=10, pady=3)

        self.end_turn_btn = tk.Button(frame, text='End\nturn',
                command=self.end_turn)
        self.end_turn_btn.grid(row=3, column=1, sticky='w n e')

        self.root.title('Last Chance Heroes')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def end_turn(self, *args):
        print('Ending turn')
        while self.do_team_action(1):
            time.sleep(0.5)
        return self.start_of_turn()

    def game_loop(self):
        self.draw_frame()
        self.draw_bf()
        self.setup_models()
        self.start_of_turn()
        self.root.mainloop()

if __name__ == '__main__':
    teams = ['8f74e6', '8f0bbc']
    ais = ['6edfda', '6edfda']
    size_x, size_y = 20, 12
    g = UI(teams, ais, lch.Battlefield(size_x, size_y, lch.Forest(size_x, size_y)))
    g.game_loop()
