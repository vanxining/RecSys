
import sys
import time

from StringIO import StringIO
from datetime import datetime

from collections import namedtuple, defaultdict
from datetime import datetime
from pymongo import MongoClient

import numpy as np


Result = namedtuple("Result", ["name", "num_real", "accuracy"])


def cmp_datetime(a, b):
    return -1 if a < b else 1 if a > b else 0


class CF:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.topcoder

        self.users = {}

        self.m = None
        self.sim = None
        self.calculated = None

        self.time_costs = []
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

    def test_set(self):
        condition = {
            u"postingDate": {
                u"$gte": self.end_date,
            }
        }

        for challenge in self.db.challenges.find(condition):
            if u"registrants" not in challenge:
                continue

            yield challenge

    def test(self, seeds_selector, top_n=10):
        start = time.time()

        for challenge in self.test_set():
            regs = challenge[u"registrants"]
            regs.sort(cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                                    y[u"registrationDate"]))

            num_seeds = seeds_selector(challenge, regs)
            if num_seeds >= len(regs):
                continue

            seeds = set()

            for reg in regs[:num_seeds]:
                handle = reg[u"handle"].lower()

                # Not ever occurred in the training set.
                if handle not in self.users:
                    continue

                seeds.add(self.users[handle])

            real = set()
            newbie_index = len(self.users) + 10000

            for reg in regs[num_seeds:]:
                handle = reg[u"handle"].lower()

                if handle in self.users:
                    user_index = self.users[handle]
                else:
                    user_index = newbie_index
                    newbie_index += 1

                real.add(user_index)

            predict = set()

            for user_index in seeds:
                self.calc_similarity(user_index)

                indices = np.flatnonzero(self.sim[user_index])
                a = [(int(i), int(self.sim[user_index, i])) for i in indices]

                if len(a) == 0:
                    continue

                a.sort(cmp=lambda x, y: y[1] - x[1])

                before = len(predict)
                for t in a:
                    if t[0] not in seeds and t[0] not in predict:
                        predict.add(t[0])

                        if len(predict) - before == top_n:
                            break

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

        self.time_costs.append(time.time() - start)

    def calc_similarity(self, user_index):
        if self.calculated[user_index] == 1:
            return

        for i in range(self.sim.shape[0]):
            if self.sim[user_index, i] > 0:
                continue

            intersection = np.bitwise_and(self.m[user_index], self.m[i])
            nz = np.count_nonzero(intersection)
            if nz > 0:
                self.sim[user_index, i] = self.sim[i, user_index] = nz

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
    start = time.time()

    cf = CF()
    cf.train()

    args = (1, 2, 4, 8, 0.5,)
    for arg in args:
        cf.test(lambda ch, regs: arg if arg >= 1 else int(len(regs) * arg))
        print ""

    def register_in_the_first_hour(challenge, regs):
        d0 = challenge[u"postingDate"]

        for index, reg in enumerate(regs):
            if (reg[u"registrationDate"] - d0).total_seconds() > 60 * 60:
                return index + 1

        return len(regs)

    cf.test(register_in_the_first_hour)

    # Output the result.

    sio = StringIO()

    stdout = sys.stdout
    sys.stdout = sio

    print "#registrants,",

    for arg in args:
        print "#seeds = %g," % arg,

    print "reg. in the first hour, name"

    sums = [0] * len(cf.time_costs)
    num_lines = 0

    for results in cf.results.values():
        if len(results) < len(cf.time_costs):
            continue

        num_lines += 1

        if args[0] >= 1:
            print results[0].num_real + args[0], ',',
        else:
            print ",",

        for i, result in enumerate(results):
            sums[i] += result.accuracy
            print "%f," % result.accuracy,

        print ',', results[0].name

    print ',',
    for s in sums:
        print s / num_lines, ',',

    print '\n\n,',
    for tc in cf.time_costs:
        print tc, ',',

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    with open("data/%s.csv" % ts, "w") as outf:
        outf.write(datetime.now().isoformat() + '\n')
        outf.write(sio.getvalue() + '\n')
        outf.write("Time cost: %d seconds." % (time.time() - start))

    stdout.write(sio.getvalue())


if __name__ == "__main__":
    main()
