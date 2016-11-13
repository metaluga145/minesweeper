from game import *
from ExperienceBuf import *
from NN import *
import numpy as np

class Agent:
    def __init__(self, load = False):
        self.bsize = (10, 10)
        self.game = Game(10, 10, 10)
        self.nn = NN(self.bsize)
        if load:
            self.nn.load()
        self.buf = ExperienceBuf()
        self.num_episodes = 5000
        self.max_game_moves = 64
        self.observe = 10
        self.e = 0.0
        self.y = 0.99
        self.mini_batch = 64

    def toHot(self, inputState):
        temp = []
        s = np.array([])
        for i in range(25):
            sample = np.zeros(10)
            sample[int(inputState[i])] = 1.0
            temp.append(sample)
        return np.asmatrix(np.append(s, temp))

    def learn(self):
        count = 0

        for i in range(self.num_episodes):
            self.game.reset()
            _, _, d = self.game.open((0, 0))
            while (not d):
                pmines, true_vals = self.choose_possible_mines()

                states = self.make_states(pmines)
                states.shape = (len(pmines), 1, 25)

                pboard = np.zeros(self.bsize)

                for i in range(len(pmines)):
                    tmp_state = states[i].flatten()
                    tmp_state = self.toHot(tmp_state)
                    self.buf.memorize(tmp_state, true_vals[i])
                    h, w = pmines[i]
                    pboard[h, w] = self.nn.predict(tmp_state)

                #print pmines
                #print states
                #print pboard

                act = np.argmax(pboard.flatten())
                a = (act // self.bsize[1], act % self.bsize[1])

                if np.random.rand(1) < self.e:
                    a = (np.random.randint(self.bsize[0]), np.random.randint(self.bsize[1]))


                #print a
                _, _, d = self.game.open(a)

                count += 1

            if count > self.observe:
                x, y, bsize = self.buf.get_batch(self.mini_batch)
                x = np.asarray(x)
                x.shape = (bsize, 250)
                y = np.asarray(y)
                y.shape = (bsize, 1)
                self.nn.train(x, y)

            if count % 50 == 0:
                self.nn.save()

    def make_target(self):
        target = np.zeros(self.bsize)
        s = self.game.display_board
        for h in range(self.bsize[0]):
            for w in range(self.bsize[1]):
                if s[h, w] == COVERED:
                    flag = False
                    for i in range(-1, 2):
                        h_new = h + i
                        if (h_new >= 0):
                            for j in range(-1, 2):
                                w_new = w + j
                                if (w_new >= 0):
                                    try:
                                        if (s[h_new, w_new] > 0):
                                            flag = True
                                    except:
                                        pass
                                if flag: break
                        if flag: break

                    if flag:
                        if self.game.board[h, w] == BOMB + 1: target[h, w] = 0
                        else: target[h, w] = 1
                    else: target[h, w] = 0.5
        return self.softmax(target)

    def choose_possible_mines(self):
        pmines = []
        true_vals = []
        s = self.game.display_board
        for h in range(self.bsize[0]):
            for w in range(self.bsize[1]):
                if s[h, w] == COVERED:
                    flag = False
                    for i in range(-1, 2):
                        h_new = h + i
                        if (h_new >= 0):
                            for j in range(-1, 2):
                                w_new = w + j
                                if (w_new >= 0):
                                    try:
                                        if (s[h_new, w_new] > 0):
                                            flag = True
                                    except:
                                        pass
                                if flag: break
                        if flag: break

                    if flag:
                        pmines.append((h, w))
                        if self.game.board[h, w] == BOMB: true_vals.append(0)
                        else:true_vals.append(1)
        return pmines, true_vals

    def make_states(self, border):
        states = np.zeros((len(border), 5, 5))
        s = self.game.display_board + 1
        for k in range(len(border)):
            h, w = border[k]
            for i in range(0, 5):
                h_new = h + i - 2
                for j in range(0, 5):
                    w_new = w + j - 2
                    if (h_new >= 0 and w_new >= 0):
                        try:
                            states[k, i, j] = s[h_new, w_new]
                        except:
                            pass
        return states


    def softmax(self, y):
        """ simple helper function here that takes unnormalized logprobs """
        #maxy = np.amax(y)
        #e = np.exp(y - maxy)
        return y / np.sum(y)

    def play(self):
        for i in range(self.num_episodes):
            self.game.reset()
            _, _, d = self.game.open((0, 0))
            while (not d):
                pmines, true_vals = self.choose_possible_mines()

                states = self.make_states(pmines)
                states.shape = (len(pmines), 1, 25)

                pboard = np.zeros(self.bsize)

                for i in range(len(pmines)):
                    tmp_state = states[i].flatten()
                    tmp_state = self.toHot(tmp_state)
                    self.buf.memorize(tmp_state, true_vals[i])
                    h, w = pmines[i]
                    pboard[h, w] = self.nn.predict(tmp_state)

                #print pmines
                #print states
                #print pboard

                act = np.argmax(pboard.flatten())
                a = (act // self.bsize[1], act % self.bsize[1])
                _, _, d = self.game.open(a)