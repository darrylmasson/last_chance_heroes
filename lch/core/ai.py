import lch
import numpy as np

__all__ = 'SimpleAI'.split()

class SimpleAI(object):
    """
    """
    action_fields = 8 # len(lch.NoAction().normalize())

    def __init__(self,
            hidden_controls=None, hidden_bias=None,
            output_controls=None, output_bias=None,
            top_n=None, name=None):
        self.hidden_controls = hidden_controls
        self.hidden_bias = hidden_bias

        self.output_controls = output_controls
        self.output_bias = output_bias

        self.top_n = top_n
        self.dtype = [
                ('n_actions', np.float32),
                ('shootable_targets', np.float32),
                ('chargeable_targets', np.float32),
                ('can_shoot_back', np.float32),
                ('can_charge_back', np.float32),
                ('chance_to_hit', np.float32),
                ('average_damage', np.float32),
                ('target_health', np.float32)
                ]
        self.name = name

    def load_from_file(self, fn):
        def load(f):
            self.hidden_controls = ff['hidden_controls']
            self.hidden_bias = ff['hidden_bias']
            self.output_controls = ff['output_controls']
            self.output_bias = ff['output_bias']

        if isinstance(fn, str):
            with open(fn, 'rb') as f:
                ff = np.load(f)
                load(ff)
        else:
            with np.load(fn) as ff:
                load(ff)

    def normalize_input(self, actions):
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
        """
        if len(actions) == 0:
            return NoAction()
        normed = self.normalize_input(actions)
        prob = np.zeros(len(normed))
        for i,a in enumerate(normed):
            #print('a', a.shape)
            #print('hc', self.hidden_controls.shape)
            hidden = (self.hidden_controls @ a.reshape((8,1,))) + self.hidden_bias
            #print('hb', self.hidden_bias.shape)
            hidden = self.activation_function_hidden(hidden)
            #print('h', hidden.shape)

            output = (self.output_controls @ hidden) + self.output_bias
            #print('oc', self.output_controls.shape)
            output = self.activation_function_output(output)
            #print('o', output.shape)
            prob[i] = output
            #print(f'{actions[i]}: {output}')

        if self.top_n is None:
            best_i = np.argmax(prob)
        else:
            n = max(self.top_n, len(prob))
            top = np.argsort(prob)[-n:]
            p = prob[top]
            best_i = np.random.choice(n, p=p/p.sum())

        return actions[best_i]

