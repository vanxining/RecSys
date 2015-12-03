
from collections import namedtuple, defaultdict
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
        self.calculated = None

        self.results = defaultdict(list)

        self.year_from = 2014
        self.end_date = datetime(2015, 10, 25)

    def training_set(self):
        condition = {
            u"postingDate": {
                u"$gte": datetime(self.year_from, 1, 1),
                u"$lt": self.end_date,
            }
        }

        for challenge in self.db.challenges.find(condition):
            if u"registrants" not in challenge:
                continue

            yield challenge

    def test_set(self, num_registrants_gt):
        condition = {
            u"postingDate": {
                u"$gte": self.end_date,
            }
        }

        for challenge in self.db.challenges.find(condition):
            if u"registrants" not in challenge:
                continue

            if len(challenge[u"registrants"]) > num_registrants_gt:
                yield challenge

    def test(self, num_seeds, top_n=10):
        Result = namedtuple("Result", ["name", "num_real", "accuracy"])

        for challenge in self.test_set(num_registrants_gt=num_seeds):
            regs = challenge[u"registrants"]
            regs.sort(cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                                    y[u"registrationDate"]))

            end = num_seeds if num_seeds >= 1 else int(len(regs) * num_seeds)
            if end >= len(regs):
                continue

            predict = set()
            real = set(r[u"handle"].lower() for r in regs[end:])

            for reg in regs[:end]:
                handle = reg[u"handle"].lower()

                # Not ever occurred in the training set.
                if handle not in self.users:
                    continue

                user_index = self.users[handle]

                self.calc_similarity(user_index)

                indices = np.flatnonzero(self.sim[user_index])
                a = [(int(i), int(self.sim[user_index, i])) for i in indices]

                if len(a) == 0:
                    continue

                a.sort(cmp=lambda x, y: y[1] - x[1])
                a = a if len(a) < top_n else a[:top_n]

                predict |= set(self.users_reverse[i[0]] for i in a)

            if len(predict) > 0:
                accuracy = len(real.intersection(predict)) / float(len(real))

                result = Result(
                    challenge["challengeName"],
                    len(real),
                    accuracy,
                )

                self.results[challenge["challengeId"]].append(result)

                print challenge["challengeName"]
                print "> Accuracy: %5.2f%% [#real: %2d]" % (
                    accuracy * 100, len(real)
                )

    def calc_similarity(self, user_index):
        if self.calculated[user_index] == 1:
            return

        for i in range(self.sim.shape[0]):
            inter = np.bitwise_and(self.m[user_index], self.m[i])
            self.sim[user_index, i] = np.count_nonzero(inter)

        # sim(self, self) == 0
        self.sim[user_index, user_index] = 0

        self.calculated[user_index] = 1

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

        self.sim = np.zeros((num_users, num_users), dtype=np.int8)
        self.calculated = np.zeros(num_users, dtype=np.int8)


def main():
    cf = CF()
    cf.train()

    args = (1, 2, 3, 4, 0.5)
    for num_seeds in args:
        cf.test(num_seeds)
        print ""

    print "#registrants,",

    for num_seeds in args:
        print "#seeds = %g," % num_seeds,

    print ", name"

    for results in cf.results.values():
        if len(results) < len(args):
            continue

        if args[0] >= 1:
            print results[0].num_real + args[0], ',',
        else:
            print ",",

        for result in results:
            print "%f," % result.accuracy,

        print ',', results[0].name


if __name__ == "__main__":
    main()
