import lch
import numpy as np
import io

__all__ = 'AI SimpleAI'.split()

class AI(object):
    """
    A base class implementing some common things
    """
    def __init__(self):
        pass

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
    def fields(cls):
        raise NotImplementedError()

    @staticmethod
    def from_hash(_hash):
        args = lch.load_from_cache('ai', _hash)
        return getattr(lch, args[2]).from_tuple(args)

    def encode(self):
        """
        Encodes self into a database-serializable tuple with format (hash, parent_hash
        class name, blob of np-compressed data)
        """
        with io.BytesIO() as f:
            np.savez_compressed(f, **{k: getattr(self, k) for k in self.fields()})
            return (self.hash, self.parent_hash, self.__class__.__name__, f.getvalue())

    @classmethod
    def from_tuple(cls, args):
        """
        The opposite of encode - generates a new *AI from the tuple
        stored in the database
        """
        _hash, parent_hash, _, blob = args
        with io.BytesIO(blob) as f:
            data = np.load(f)
            return cls(_hash = _hash, parent_hash=parent_hash,
                    **{k: data[k] for k in cls.fields()})

class SimpleAI(AI):
    """
    A very simple ML ai, one hidden layer with 12 nodes, 8 input fields
    """
    nodes = 12
    dtype = [
            ('n_actions', np.float32),
            ('shootable_targets', np.float32),
            ('chargeable_targets', np.float32),
            ('can_shoot_back', np.float32),
            ('can_charge_back', np.float32),
            ('chance_to_hit', np.float32),
            ('average_damage', np.float32),
            ('target_health', np.float32)
            ]

    def __init__(self,
            hidden_controls=None, hidden_bias=None,
            output_controls=None, output_bias=None,
            top_n=None, _hash=None, parent_hash=None,
            games=None, generations=None):
        self.hidden_controls = hidden_controls
        self.hidden_bias = hidden_bias

        self.output_controls = output_controls
        self.output_bias = output_bias

        self.top_n = top_n
        self.hash = _hash or lch.get_hash(
                self.hidden_controls.tobytes().hex(),
                self.hidden_bias.tobytes().hex(),
                self.output_controls.tobytes().hex(),
                self.output_bias.tobytes().hex(),
                self.top_n)
        self.parent_hash = parent_hash or '0'*6

        self.games = games or 0
        self.generations = generations or 0

    @classmethod
    def from_scratch(cls):
        """
        Returns a new SimpleAI with random parameters
        """
        return cls(
                hidden_controls = np.random.random(size=(cls.nodes, len(cls.dtype))),
                hidden_bias = np.random.random(size=(cls.nodes, 1)),
                output_controls = np.random.random(size=(1, cls.nodes)),
                output_bias = np.random.random(size=(1,1)),
                top_n = np.random.randint(3, 6))

    @classmethod
    def fields(cls):
        """
        Returns a list of things to be serialized
        """
        return 'hidden_controls hidden_bias output_controls output_bias top_n games generations'.split()

    def mutate(self, step=0.01, prob=0.5):
        """
        Mutate into a child
        :param step: how much to change parameters by, default 0.01
        :param prob: the probability that a any one value changes, default 0.5
        :returns: a hash of a new SimpleAI
        """
        mask = np.random.random(size=self.hidden_controls.shape) > prob
        hc_change = mask*step*(np.random.random(size=self.hidden_controls.shape) - 0.5)
        mask = np.random.random(size=self.hidden_bias.shape) > prob
        hb_change = mask*step*(np.random.random(size=self.hidden_bias.shape) - 0.5)
        mask = np.random.random(size=self.output_controls.shape) > prob
        oc_change = mask*step*(np.random.random(size=self.output_controls.shape) - 0.5)
        mask = np.random.random(size=self.output_bias.shape) > prob
        ob_change = mask*step*(np.random.random(size=self.output_bias.shape) - 0.5)
        top_n_change = np.random.choice([-1,0,1], p=[step, 1-2*step, step]) * (np.random.random() > prob)

        return self.__class__(hidden_controls = self.hidden_controls + hc_change,
                    hidden_bias = self.hidden_bias + hb_change,
                    output_controls = self.output_controls + oc_change,
                    output_bias = self.output_bias + ob_change,
                    top_n = min(1, self.top_n + top_n_change),
                    parent_hash = self.hash)

    def normalize_input(self, actions):
        """
        Takes a list of actions and normalizes them pre-selection
        :param actions: a list of unencoded actions to normalize
        :returns: a np array of encoded and normalized actions
        """
        normed = np.zeros((len(actions), len(self.dtype)))
        for i,a in enumerate(actions):
            normed[i] = a.normalize()

        # number of possible actions
        normed[:, 0] = np.log(len(normed))

        # shootable targets
        m = normed[:, 1] != 0
        normed[m, 1] = np.log(normed[m, 1])
        normed[~m, 1] = -1

        # chargeable targets
        m = normed[:, 2] != 0
        normed[m, 2] = np.log(normed[m, 2])
        normed[~m, 2] = -1

        # can shoot back
        m = normed[:, 3] != 0
        normed[m, 3] = np.log(normed[m, 3])
        normed[~m, 3] = -1

        # can charge back
        m = normed[:, 4] != 0
        normed[m, 4] = np.log(normed[m, 4])
        normed[~m, 4] = -1

        # hit prob
        # already in [0,1), no normalization necessary

        # avg damage
        m = normed[:, 6] != 0
        normed[m, 6] = np.log(normed[m, 6])
        normed[~m, 6] = 0

        # target health
        m = normed[:, 7] != 0
        normed[m, 7] = np.log(normed[m, 7])
        normed[~m, 7] = 0

        return normed

    @staticmethod
    def rectified_linear(arr):
        return np.maximum(arr, 0, out=arr)

    @staticmethod
    def logistic_sigmoid(arr):
        return 1/(1+np.exp(-arr))

    def activation_function_hidden(self, weighted_sum):
        return self.rectified_linear(weighted_sum)

    def activation_function_output(self, weighted_sum):
        return self.rectified_linear(weighted_sum)

    def select_action(self, actions):
        """
        Selects from the provided actions via ML magicks
        :param actions: list of Action objects
        :returns: Action object that is the "best" one
        """
        if len(actions) == 0:
            return NoAction()
        normed = self.normalize_input(actions)
        prob = np.zeros(len(normed))
        for i,a in enumerate(normed):
            hidden = (self.hidden_controls @ a.reshape((8,1))) + self.hidden_bias
            hidden = self.activation_function_hidden(hidden)

            output = (self.output_controls @ hidden) + self.output_bias
            output = self.activation_function_output(output)
            prob[i] = output

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

