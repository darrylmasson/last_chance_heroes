import lch
import numpy as np
import io

__all__ = 'AI Random DenseMultilayer'.split()

def rand(shape, _min=-2, _max=-2):
    # a wrapper abound np.random.random
    return (_max - _min)*np.random.random(size=shape) + _min

class AI(object):
    """
    A base class implementing some common things
    """
    version = "0.0.1"
    dtype = [
            ('n_actions', np.float32),
            ('shootable_targets', np.float32),
            ('chargeable_targets', np.float32),
            ('can_shoot_back', np.float32),
            ('can_charge_back', np.float32),
            ('target_has_activated', np.int8),
            ('remaining_friendly_actions', np.int8),
            ('remaining_enemy_actions', np.int8),
            ('chance_to_hit', np.float32),
            ('threat_dist', np.float32),
            ('f_threat_move', np.float32),
            ('f_threat_rs', np.float32),
            ('f_threat_rc', np.float32),
            ('f_threat_ms', np.float32),
            ('f_threat_mc', np.float32),
            ('f_threat_ch', np.float32),
            ('f_threat_dodge', np.float32),
            ('f_threat_armor', np.float32),
            ('f_threat_mw_attacks', np.float32),
            ('f_threat_mw_punch', np.float32),
            ('f_threat_mw_min_dmg', np.float32),
            ('f_threat_mw_max_dmg', np.float32),
            ('f_threat_rw_class', np.float32),
            ('f_threat_rw_range', np.float32),
            ('f_threat_rw_attacks', np.float32),
            ('f_threat_rw_punch', np.float32),
            ('f_threat_rw_min_dmg', np.float32),
            ('f_threat_rw_max_dmg', np.float32),
            ('e_threat_move', np.float32),
            ('e_threat_rs', np.float32),
            ('e_threat_rc', np.float32),
            ('e_threat_ms', np.float32),
            ('e_threat_mc', np.float32),
            ('e_threat_ch', np.float32),
            ('e_threat_dodge', np.float32),
            ('e_threat_armor', np.float32),
            ('e_threat_mw_attacks', np.float32),
            ('e_threat_mw_punch', np.float32),
            ('e_threat_mw_min_dmg', np.float32),
            ('e_threat_mw_max_dmg', np.float32),
            ('e_threat_rw_class', np.float32),
            ('e_threat_rw_range', np.float32),
            ('e_threat_rw_attacks', np.float32),
            ('e_threat_rw_punch', np.float32),
            ('e_threat_rw_min_dmg', np.float32),
            ('e_threat_rw_max_dmg', np.float32),
            ]

    def __init__(self, _hash=None, parent_hash=None, **kwargs):
        for k in self.fields():
            setattr(self, k, kwargs[k])

        self.hash = _hash or lch.get_hash(*[
            kwargs[k].tobytes().hex()
            if isinstance(kwargs[k], np.ndarray) else kwargs[k]
            for k in self.fields()])
        self.parent_hash = parent_hash or '0'*6

    def __eq__(self, rhs):
        return self.hash == rhs.hash

    @staticmethod
    def create_table(conn):
        try:
            conn.execute('CREATE TABLE ai ( '
                'hash TEXT PRIMARY KEY NOT NULL, '
                'parent_hash TEXT, '
                'class_name TEXT, '
                'binary BLOB );')
        except Exception as e:
            pass

    @classmethod
    def base_fields(cls):
        """
        Returns a list of the fields this class uses
        """
        raise NotImplementedError()

    def fields(self):
        """
        Returns a list of specific fields this instance uses. Might be different from
        base_fields in some situations, so we allow that here.
        """
        return self.base_fields()

    @staticmethod
    def from_hash(_hash):
        args = lch.load_from_cache('ai', _hash)
        return getattr(lch, args[2]).from_tuple(args)

    @classmethod
    def from_tuple(cls, args):
        """
        The opposite of encode - generates a new *AI from the tuple
        stored in the database
        """
        _hash, parent_hash, _, blob = args
        with io.BytesIO(blob) as f:
            data = np.load(f)
            fields = data['fields']
            return cls(_hash = _hash, parent_hash=parent_hash,
                    **{k: data[k] for k in fields})

    def encode(self):
        """
        Encodes self into a database-serializable tuple with format (hash, parent_hash
        class name, blob of np-compressed data)
        """
        with io.BytesIO() as f:
            fields = np.array(self.fields(), dtype='U32')
            np.savez_compressed(f, fields=fields,
                    **{k: getattr(self, k) for k in fields})
            return (self.hash, self.parent_hash, self.__class__.__name__, f.getvalue())

    def mutate(self, step=0.1, prob=0.5):
        """
        Mutate into a child
        :param step: how much to change parameters by, default 0.1
        :param prob: the probability that any one value changes, default 0.5
        :returns: a new *AI
        """
        kwargs = {}
        for k in self.fields():
            x = getattr(self, k)
            if isinstance(x, np.ndarray) and x.dtype == float:
                # most parameters here
                mask = np.random.random(size=x.shape) > prob
                kwargs[k] = x + mask * step * rand(x.shape)
            elif isinstance(x, int) or (isinstance(x, np.ndarray) and x.dtype == int):
                # things like top_n here
                c = [0,1] if x == 1 else [-1, 0, 1]
                p = [1-step, step] if x == 1 else [step, 1-2*step, step]
                kwargs[k] = x + np.random.choice(c, p=p)
            else:
                # no change till I figure this out
                kwargs[k] = x

        return self.__class__(parent_hash = self.hash, **kwargs)

    def normalize_input(self, actions):
        """
        Takes a list of actions and normalizes them pre-selection
        :param actions: a list of unencoded actions to normalize
        :returns: a np array of encoded and normalized actions
        """
        # can't be a structured array because they count as 1d not 2d
        normed = np.zeros((len(actions), len(self.dtype)))
        for i,a in enumerate(actions):
            normed[i] = a.normalize()

        # number of possible actions
        idx = 0
        normed[:, idx] = np.log(len(normed))

        # shootable targets
        idx += 1
        m = normed[:, idx] != 0
        normed[m, idx] = np.log(normed[m, idx])
        normed[~m, idx] = -1

        # chargeable targets
        idx += 1
        m = normed[:, idx] != 0
        normed[m, idx] = np.log(normed[m, idx])
        normed[~m, idx] = -1

        # can shoot back
        idx += 1
        m = normed[:, idx] != 0
        normed[m, idx] = np.log(normed[m, idx])
        normed[~m, idx] = -1

        # can charge back
        idx += 1
        m = normed[:, idx] != 0
        normed[m, idx] = np.log(normed[m, idx])
        normed[~m, idx] = -1

        # target has activated
        idx += 1
        # already in [0,1]

        # remaining friendly actions
        idx += 1
        # low integer, no normalization needed

        # remaining enemy actions
        idx += 1
        # low integer, no normalization needed

        # chance to hit
        idx += 1
        # already in [0,1)

        # threat distance
        idx += 1
        normed[:, idx] /= lch.global_vars.get('bf_diag', np.hypot(24, 18))

        # threat parameters already normalized
        return normed

    def process_one(self, vector):
        """
        Run one input vector through the NN. Input has shape (x, 1) so you can
        directly do control @ vector without reshaping.
        """
        raise NotImplementedError()

    def select_action(self, actions):
        """
        Selects from the provided actions via ML magicks
        :param actions: list of Action objects
        :returns: one Action from the list
        """
        if len(actions) == 0:
            return lch.NoAction()
        normed = self.normalize_input(actions)
        prob = np.zeros(len(normed))
        for i,a in enumerate(normed):
            prob[i] = self.process_one(a.reshape((len(self.dtype), 1)))
        if self.top_n is None or self.top_n == 1:
            best_i = np.argmax(prob)
        else:
            n = min(self.top_n, len(prob))
            cutoff = np.sort(prob)[-n]
            prob[prob < cutoff] = 0
            if (s := prob.sum()) == 0:
                # whoops?
                p = np.ones(len(prob))/len(prob)
            else:
                p = prob/s
            best_i = np.random.choice(len(prob), p=p)
        return actions[best_i]

    def take_enemy_action(self, action):
        """
        What did the enemy just do?
        """
        pass

class Random(AI):
    """
    Selects randomly. "Artificial"? Yes. "Intelligence"? Behave yourself
    """
    @classmethod
    def base_fields(cls):
        return []

    def select_action(self, actions):
        return actions[np.random.choice(len(actions))]

class DenseMultilayer(AI):
    """
    A simple ai with densly-connected layers
    """
    hidden_nodes = [64, 16]

    @classmethod
    def from_scratch(cls, **kwargs):
        """
        Returns a new AI with random parameters
        """
        output_shape = kwargs.get('output_shape', 1)
        input_shape = kwargs.get('input_shape', len(cls.dtype))
        kwargs = {
                'top_n': np.random.randint(3,6),
                'oc': rand((1, cls.hidden_nodes[-1])),
                'ob': rand((output_shape, 1)),
        }
        for i, v in enumerate(cls.hidden_nodes):
            cols = input_shape if i == 0 else cls.hidden_nodes[i-1]
            kwargs[f'hc_{i}'] = rand((v, cols))
            kwargs[f'hb_{i}'] = rand((v, 1))
        return cls(**kwargs)

    def fields(self):
        n = range(len(self.hidden_nodes))
        return 'oc ob top_n'.split() + [f'hc_{i}' for i in n] + [f'hb_{i}' for i in n]

    def process_one(self, a):
        hidden = a
        for i in range(len(self.hidden_nodes)):
            hidden = getattr(self, f'hc_{i}') @ hidden
            hidden = activation_funcs['leaky_relu'](np.add(hidden, getattr(self, f'hb_{i}'), out=hidden))

        output = self.oc @ hidden
        output = activation_funcs['tanh'](np.add(output, self.ob, out=output))
        return output

def Recurrent(AI):
    """
    Now with some memory. Keeps track of own and enemies' actions
    """
    hidden_nodes = 12

    def __init__(self, **kwargs):
        raise NotImplementedError()
        super().__init__(**kwargs)
        self.last_friendly = []
        self.last_enemy = []

    @classmethod
    def fields(cls):
        return 'hc hb oc ob top_n friendly_recurrent enemy_recurrent friendly_threat enemy_threat memory'.split()

    @classmethod
    def from_scratch(cls):
        return cls(
                hc = rand((cls.hidden_nodes, len(cls.dtype))),
                hb = rand((cls.hidden_nodes, 1)),
                fr = rand((cls.hidden_nodes, len(cls.dtype))),
                er = rand((cls.hidden_nodes, len(cls.dtype))),
                oc = rand((1, cls.hidden_nodes)),
                ob = rand((1,1)),
                top_n = np.random.randint(3, 6),
                memory = 1)

    def evaluate_action(self, action):
        hidden = self.hc @ action
        for b in self.last_friendly:
            hidden = np.add(hidden, self.fr @ b, out=hidden)
        for b in self.last_enemy:
            hidden = np.add(hidden, self.er @ b, out=hidden)
        hidden = activation_funcs['leaky_relu'](np.add(hidden, self.hb, out=hidden))

        output = self.oc @ hidden
        output = activation_funcs['tanh'](np.add(output, self.ob, out=output))

        return output[0]

    def take_enemy_action(self, action):
        self.last_enemy.append(self.normalize_input([action])[0])
        if len(self.last_enemy) > self.memory:
            self.last_enemy = self.last_enemy[-self.memory:]

    def select_action(self, actions):
        ret = super().select_action(actions)
        self.last_friendly.append(self.normalize_input([ret])[0])
        if len(self.last_friendly) > self.memory:
            self.last_friendly = self.last_friendly[-self.memory:]
        return ret


# some activation functions. Most try to operate in-place to avoid
# allocating new memory. Defined as a dict so we can mutate and reference easily
activation_funcs = {
        'relu': lambda arr: np.maximum(arr, 0, out=arr),
        'linear': lambda arr: arr,
        'logistic_sigmoid': lambda arr: 1/(1+np.exp(-arr)),
        'tanh': lambda arr: np.tanh(arr, out=arr),
        'leaky_relu': lambda arr: np.multiply(arr, 0.1, out=arr, where=arr<0),
        'elu': lambda arr: np.expm1(arr, where=arr<0),
        }
