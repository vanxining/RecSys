#!/usr/bin/env python2

import sys
import time
import ConfigParser

from StringIO import StringIO
from datetime import datetime
from collections import namedtuple, defaultdict

import pymongo
import numpy as np
import sim


Result = namedtuple("Result", ("name", "num_real", "accuracy", "recall"))
TestRound = namedtuple("TestRound", ("time", "accuracy", "recall", "diversity"))


def cmp_datetime(a, b):
    return -1 if a < b else 1 if a > b else 0


class MF(object):
    SET = 5
    THRESHOLD = 0.005

    def __init__(self):
        self.V = None
        self.W = None
        self.H = None

    def factorize(self):
        if "nimfa" not in globals():
            import nimfa

        snmf = nimfa.Snmf(self.V, seed="random_vcol", rank=30, max_iter=30, version='r', eta=1.,
                          beta=1e-4, i_conv=10, w_min_change=0)
        print "Algorithm: %s\nInitialization: %s\nRank: %d" % (snmf, snmf.seed, snmf.rank)

        fit = snmf()

        sparse_w, sparse_h = fit.fit.sparseness()
        print """Stats:
- iterations: %d
- Euclidean distance: %5.3f
- Sparseness basis: %5.3f, mixture: %5.3f""" % (fit.fit.n_iter,
                                                fit.distance(metric='euclidean'),
                                                sparse_w, sparse_h)

        self.W, self.H = fit.basis(), fit.coef()

    def predict(self, i, j):
        return max(min((self.W[i, :] * self.H[:, j])[0, 0], 1), 0)


class Config(object):
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read("config/collab_filtering.ini")

        nb_seeds = config.get("default", "nb_seeds").split(',')
        self.nb_seeds = [int(n) if '.' not in n else float(n) for n in nb_seeds]

        self.year_from = config.getint("default", "year_from")

        end_date = config.get("default", "end_date").split('-')
        self.end_date = datetime(*[int(i) for i in end_date])

        self.use_mf = config.get("default", "use_mf") == "True"
        self.sim_func = config.get("default", "sim_func")


g_config = Config()


class CF(object):
    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client.topcoder

        self.users = {}
        self.m = None
        self.factorizer = MF() if g_config.use_mf else None

        self.test_rounds = []
        self.results = defaultdict(list)
        self.predicted_ever = set()

    def diversity(self):
        return len(self.predicted_ever) / float(self.m.shape[0] - 1)

    @staticmethod
    def is_challenge_ok(challenge):
        if u"registrants" not in challenge:
            return False

        if len(challenge[u"registrants"]) == 0:
            return False

        # TODO: challengeType
        return (challenge[u"challengeType"] == u"First2Finish" and
                challenge[u"type"] == u"develop")

    def training_set(self):
        condition = {
            u"postingDate": {
                u"$gte": datetime(g_config.year_from, 1, 1),
                u"$lt": g_config.end_date,
            }
        }

        sorter = (u"postingDate", pymongo.DESCENDING)

        for challenge in self.db.challenges.find(condition).sort(*sorter):
            if CF.is_challenge_ok(challenge):
                yield challenge

    def test_set(self):
        condition = {
            u"postingDate": {
                u"$gte": g_config.end_date,
            }
        }

        challenges = [] if g_config.use_mf else None

        for challenge in self.db.challenges.find(condition):
            if CF.is_challenge_ok(challenge):
                if challenges is not None:
                    challenges.append(challenge)
                else:
                    yield challenge

        if challenges is not None:
            for challenge in challenges:
                yield challenge

    def test(self, seeds_selector, top_n=10):
        sim_func = getattr(sim, g_config.sim_func)

        start = time.time()
        self.predicted_ever.clear()

        nb_processed = 0
        accuracy_sum = 0
        recall_sum = 0

        for challenge in self.test_set():
            regs = challenge[u"registrants"]
            regs.sort(cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                                    y[u"registrationDate"]))

            nb_seeds = seeds_selector(challenge, regs)
            if nb_seeds == 0 or nb_seeds >= len(regs):
                continue

            seeds = set()

            # Find nb_seeds old men.
            for reg in regs:
                handle = reg[u"handle"]

                # Not ever occurred in the training set.
                if handle not in self.users:
                    continue

                seeds.add(self.users[handle])

                if len(seeds) == nb_seeds:
                    break

            real = set()
            newbie_index = len(self.users) + 10000

            for reg in regs:
                handle = reg[u"handle"]

                if handle in self.users:
                    user_index = self.users[handle]
                else:  # TODO: Why do so? We can never find them out.
                    user_index = newbie_index
                    newbie_index += 1

                if user_index not in seeds:
                    real.add(user_index)

            if len(real) == 0:
                continue

            # Prepare for matrix factorization.
            if self.factorizer is not None:
                self.factorizer.V[:, -1].fill(0)

                for seed_index in seeds:
                    self.factorizer.V[seed_index, -1] = MF.SET

                self.factorizer.factorize()

            # Predict.
            predicted = set()

            for user_index in seeds:
                candidates = sim_func(self.m, user_index, top_n * 5)

                before = len(predicted)
                for peer_index in candidates:
                    mf = self.factorizer.predict(peer_index, -1)
                    print "--- mf: %5.4f" % mf

                    if mf < MF.THRESHOLD:
                        continue

                    if peer_index not in seeds and peer_index not in predicted:
                        predicted.add(peer_index)

                        if len(predicted) - before == top_n:
                            break

            if len(predicted) > 0:
                self.predicted_ever |= predicted

                intersection = real.intersection(predicted)
                accuracy = len(intersection) / float(len(predicted))
                recall = len(intersection) / float(len(real))

                result = Result(challenge[u"challengeName"],
                                len(real),
                                accuracy,
                                recall)

                self.results[challenge[u"challengeId"]].append(result)

                nb_processed += 1
                accuracy_sum += accuracy
                recall_sum += recall

                print challenge[u"challengeName"]
                print "> Accuracy: %5.2f%%" % (accuracy * 100)
                print "> Recall: %5.2f%% [#real: %2d]" % (recall * 100, len(real))

        assert nb_processed > 0

        test_round = TestRound(time.time() - start,
                               accuracy_sum / float(nb_processed),
                               recall_sum / float(nb_processed),
                               self.diversity())
        self.test_rounds.append(test_round)

        print test_round

    def train(self):
        num_challenges = 0
        user_index = 0

        for challenge in self.training_set():
            num_challenges += 1

            for reg in challenge[u"registrants"]:
                handle = reg[u"handle"]

                if handle not in self.users:
                    self.users[handle] = user_index
                    user_index += 1

        num_users = user_index

        # The last column contains the numbers of registrants of each task.
        self.m = np.zeros((num_challenges, num_users + 1), dtype=np.uint8)

        for challenge_index, challenge in enumerate(self.training_set()):
            self.m[challenge_index, -1] = len(challenge[u"registrants"])

            for reg in challenge[u"registrants"]:
                user_index = self.users[reg[u"handle"]]
                self.m[challenge_index, user_index] = 1

        # 1 2 3    1 4 7
        # 4 5 6 -> 2 5 8
        # 7 8 9    3 6 9

        self.m = np.transpose(self.m)

        if self.factorizer is not None:
            rows, cols = self.m.shape
            self.factorizer.V = np.zeros((rows - 1, cols + 1), dtype=np.uint8)
            self.factorizer.V[:, :-1] = self.m[:-1, :] * MF.SET



def main():
    start = time.time()

    cf = CF()
    cf.train()

    run_all_tests(cf, first_hour=True)

    # Output the result.

    sio = StringIO()

    stdout = sys.stdout
    sys.stdout = sio

    print "#registrants,,",

    for nb in g_config.nb_seeds:
        print "#seeds = %g,,," % nb,

    print "reg. in the first hour,,, name"

    accuracy_sums = [0.0] * len(cf.test_rounds)
    recall_sums = list(accuracy_sums)
    num_lines = 0

    for results in cf.results.values():
        # Filter out challenges that do not have enough registrants.
        if len(results) < len(cf.test_rounds):
            continue

        num_lines += 1

        if g_config.nb_seeds[0] >= 1:
            print "%2d,," % (results[0].num_real + g_config.nb_seeds[0]),
        else:
            print ",,",

        for i, result in enumerate(results):
            accuracy_sums[i] += result.accuracy
            recall_sums[i] += result.recall

            print "%f,%f,," % (result.accuracy, result.recall),

        print results[0].name

    print "  ,,",
    for accuracy, recall in zip(accuracy_sums, recall_sums):
        print "%f,%f,," % (accuracy / num_lines, recall / num_lines),

    print "Average (Accuracy & Recall rate)"

    print "  ,,",
    for test_round in cf.test_rounds:
        print test_round.diversity, ",,,",

    print "Average (Diversity)\n"

    print "  ,,",
    for test_round in cf.test_rounds:
        print test_round.time, ",,,",

    print "Time\n"

    print "Total time cost: %.2f seconds.\n\n" % (time.time() - start)
    print open("config/collab_filtering.ini").read()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    with open("results/%s-%s.csv" % (ts, g_config.sim_func), "w") as outf:
        outf.write(datetime.now().isoformat() + '\n')
        outf.write("Training set size: %d, " % cf.m.shape[1])
        outf.write("Test set size: %d\n\n" % num_lines)
        outf.write(sio.getvalue())

    stdout.write(sio.getvalue())


def run_all_tests(cf, first_hour=True):
    for nb in g_config.nb_seeds:
        cf.test(lambda ch, regs: nb if nb >= 1 else int(len(regs) * nb))
        print ""

    def register_in_the_first_hour(challenge, regs):
        d0 = challenge[u"postingDate"]
        nb_old_men = 0

        for index, reg in enumerate(regs):
            if (reg[u"registrationDate"] - d0).total_seconds() > 60 * 60:
                return nb_old_men  # TODO: When nb_old_men is 0?
            elif reg[u"handle"] in cf.users:
                nb_old_men += 1

        return len(regs)

    if first_hour:
        cf.test(register_in_the_first_hour)
        print ""


if __name__ == "__main__":
    main()
    sim.ClearCache()
