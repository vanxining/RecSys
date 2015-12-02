
from datetime import datetime
from pymongo import MongoClient

import numpy as np


def cmp_datetime(a, b):
    return -1 if a < b else 1 if a > b else 0


class CF:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.topcoder

        self.users = {}
        self.users_reverse = None

        self.m = None
        self.sim = None

        self.year_from = 2014
        self.end_date = datetime(2015, 11, 1)

    def training_set(self):
        condition = {
            u"postingDate": {
                u"$gte": datetime(self.year_from, 1, 1),
                u"$lt": self.end_date,
        }}

        for challenge in self.db.challenges.find(condition):
            if u"registrants" not in challenge:
                continue

            yield challenge

    def test_set(self):
        condition = {
            u"postingDate": {
                u"$gte": self.end_date,
        }}

        for challenge in self.db.challenges.find(condition):
            if u"registrants" not in challenge:
                continue

            yield challenge

    def test(self, count, top_n=10):
        for challenge in self.test_set():
            regs = challenge[u"registrants"]
            regs.sort(cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                                    y[u"registrationDate"]))

            end = count if count >= 1 else len(regs) * count
            if end >= len(regs):
                continue

            predict = set()
            real = set(r[u"handle"].lower() for r in regs[end:])

            for reg in regs[:end]:
                handle = reg[u"handle"].lower()
                user_index = self.users[handle]

                self.calc_similarity(user_index)

                indices = np.flatnonzero(self.sim[user_index])
                a = [(i, int(self.sim[user_index, i])) for i in indices]

                if len(a) == 0:
                    continue

                a.sort(cmp=lambda x, y: y[1] - x[1])
                a = a if len(a) < top_n else a[:top_n]

                predict |= set(self.users_reverse[i[0]] for i in a)

            if len(predict) > 0:
                accuracy = (len(real.intersection(predict)) /
                            float(min(len(real), len(predict))))

                print "Accuracy: %5.2f%%" % (accuracy * 100)

    def calc_similarity(self, user_index):
        if self.sim[user_index, self.sim.shape[0]] == 1:
            return

        for i in range(self.sim.shape[0]):
            inter = np.bitwise_and(self.m[user_index], self.m[i])
            self.sim[user_index, i] = np.count_nonzero(inter)

        self.sim[user_index, user_index] = 0
        self.sim[user_index, self.sim.shape[0]] = 1

    def train(self):
        num_challenges = 0
        user_index = 0

        for challenge in self.training_set():
            num_challenges += 1

            for reg in challenge[u"registrants"]:
                handle = reg[u"handle"].lower()

                if handle not in self.users:
                    self.users[handle] = user_index
                    user_index += 1

        num_users = user_index

        self.users_reverse = [None] * num_users
        for handle in self.users:
            self.users_reverse[self.users[handle]] = handle

        self.m = np.zeros((num_challenges, num_users), dtype=np.int8)

        for challenge_index, challenge in enumerate(self.training_set()):
            for reg in challenge[u"registrants"]:
                handle = reg[u"handle"].lower()

                user_index = self.users[handle]
                self.m[challenge_index, user_index] = 1

        self.m = np.transpose(self.m)

        # The last column is the "calculated" mark.
        self.sim = np.zeros((num_users, num_users + 1), dtype=np.int8)


if __name__ == '__main__':
    cf = CF()

    cf.train()
    cf.test(count=2)
