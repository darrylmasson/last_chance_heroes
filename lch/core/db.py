import lch
import sqlite3 as sql


class DB(object):
    """
    API for database storage
    """
    def __init__(self, fn):
        self.con = sql.connect(fn)
        self.cur = self.con.cursor()


    def get_model(self, model_id):
        self.cur.execute('SELECT * FROM models WHERE model_id=?', model_id)
        row = self.cur.fetchone()

        return lch.Model(*row)

    def get_team(self, team_id):

