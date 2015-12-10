
import sys
import time
import ConfigParser

from StringIO import StringIO
from datetime import datetime

from collections import namedtuple, defaultdict
from pymongo import MongoClient

import numpy as np
import sim


Result = namedtuple("Result", ["name", "num_real", "recall"])


def cmp_datetime(a, b):
    return -1 if a < b else 1 if a > b else 0


class CF:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.topcoder

        self.users = {}
        self.m = None

        self.time_costs = []
        self.results = defaultdict(list)

        self.config = ConfigParser.RawConfigParser()
        self.config.read("config/collab_filtering.ini")

        end_date = [
            int(i) for i in self.config.get("default", "end_date").split('-')
        ]

        self.end_date = datetime(*end_date)
        self.year_from = self.config.getint("default", "year_from")

        self.sim_func = getattr(sim, self.config.get("default", "sim_func"))

    @staticmethod
    def is_challenge_ok(challenge):
        if u"registrants" not in challenge:
            return False

        if len(challenge[u"registrants"]) == 0:
            return False

        return (challenge[u"challengeType"] == u"First2Finish" and
                challenge[u"type"] == u"develop")

    def training_set(self):
        condition = {
            u"postingDate": {
                u"$gte": datetime(self.year_from, 1, 1),
                u"$lt": self.end_date,
            }
        }

        for challenge in self.db.challenges.find(condition):
            if CF.is_challenge_ok(challenge):
                yield challenge

    def test_set(self):
        condition = {
            u"postingDate": {
                u"$gte": self.end_date,
            }
        }

        for challenge in self.db.challenges.find(condition):
            if CF.is_challenge_ok(challenge):
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
                a = self.sim_func(self.m, user_index, top_n * 5)

                before = len(predict)
                for peer_index in a:
                    if peer_index not in seeds and peer_index not in predict:
                        predict.add(peer_index)

                        if len(predict) - before == top_n:
                            break

            if len(predict) > 0:
                recall = len(real.intersection(predict)) / float(len(real))

                result = Result(challenge[u"challengeName"], len(real), recall)
                self.results[challenge[u"challengeId"]].append(result)

                print challenge[u"challengeName"]
                print "> Recall: %5.2f%% [#real: %2d]" % (recall * 100, len(real))

        self.time_costs.append(time.time() - start)

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

        self.m = np.zeros((num_challenges, num_users + 1), dtype=np.uint8)

        for challenge_index, challenge in enumerate(self.training_set()):
            self.m[challenge_index, -1] = len(challenge[u"registrants"])

            for reg in challenge[u"registrants"]:
                handle = reg[u"handle"].lower()

                user_index = self.users[handle]
                self.m[challenge_index, user_index] = 1

        # 1 2 3    1 4 7
        # 4 5 6 -> 2 5 8
        # 7 8 9    3 6 9

        self.m = np.transpose(self.m)


def main():
    start = time.time()

    cf = CF()
    cf.train()

    args = (1, 2,)
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

    print ""
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
            sums[i] += result.recall
            print "%f," % result.recall,

        print ',', results[0].name

    print ',',
    for s in sums:
        print s / num_lines, ',',

    print '\n\n,',
    for tc in cf.time_costs:
        print tc, ',',

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fn = cf.config.get("default", "sim_func")

    with open("data/%s-%s.csv" % (ts, fn), "w") as outf:
        outf.write(datetime.now().isoformat() + '\n')
        outf.write(sio.getvalue() + '\n')
        outf.write("Time cost: %d seconds.\n\n" % (time.time() - start))
        outf.write(open("config/collab_filtering.ini").read())

    stdout.write(sio.getvalue())


if __name__ == "__main__":
    main()
    sim.ClearCache()
