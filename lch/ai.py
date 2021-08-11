import lch
import numpy as np


class AI(object):
    """
    """
    def __init__(self, deterministic=True, top_n=None):
        N = 9
        # action has shape (N,1)
        #self.action_dtype = f'{N}f8'
        self.action_fields = N
        # hidden controls has shape (nodes, N)
        nodes = 12
        self.hidden_controls = np.random.random(size=(nodes, N))
        self.hidden_bias = np.random.random(size=nodes)

        # output controls has shape (1, nodes)
        self.output_controls = np.random.random(size=(1, nodes))
        self.output_bias = np.random.random(size=1)

        self.deterministic = deterministic
        self.top_n = top_n

    def normalize_input(self, actions):
        normed = np.zeros((len(actions), self.action_fields), dtype=np.float32)
        for i,a in enumerate(actions):
            normed[i] = a.normalize()
        return normed

    def activation_function_hidden(self, weighted_sum):
        # start with rectivied linear for now
        return np.maximum(weighted_sum, np.zeros_like(weighted_sum))

    def activation_function_output(self, weighted_sum):
        return np.maximum(weighted_sum, np.zeros_like(weighted_sum))

    def select_action(self, actions):
        """
        """
        if len(actions) == 0:
            return NoAction()
        normed = self.normalize_input(actions)
        prob = np.zeros(len(normed))
        for i,a in enumerate(normed):
            hidden = np.matmul(self.hidden_controls, a) + self.hidden_bias
            hidden = self.activation_function_hidden(hidden)

            output = np.matmul(self.output_controls, hidden) + self.output_bias
            output = self.activation_function_output(output)
            prob[i] = output[0]
            print(f'{actions[i]}: {output}')

        if self.deterministic:
            best_i = np.argmax(prob)
        else:
            if self.top_n != 0:
                top = np.argsort(prob)[-self.top_n:]
                prob[~top] = 0
            best_i = np.random.choice(len(prob), p=prob/prob.sum())

        return actions[best_i]

