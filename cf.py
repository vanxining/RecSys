#!/usr/bin/env python2

import sqlite3
import sys
import time

from collections import namedtuple, defaultdict
from datetime import datetime
from StringIO import StringIO

import numpy as np
import pymongo

import config.cf as g_config
# noinspection PyUnresolvedReferences
import sim


'''
For every seed developer, recommend 10 similar peers.
'''


Result = namedtuple("Result", ("name", "num_real", "accuracy", "recall"))
TestRound = namedtuple("TestRound", ("time", "accuracy", "recall", "diversity"))


def cmp_datetime(a, b):
    return -1 if a < b else 1 if a > b else 0


class TopCoderChallenge(object):
    def __init__(self, challenge):
        self.id = challenge[u"challengeId"]
        self.name = challenge[u"challengeName"]

        challenge[u"registrants"].sort(
            cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                          y[u"registrationDate"])
        )

        self.regs = [reg[u"handle"] for reg in challenge[u"registrants"]]


class TopCoderDataset(object):
    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client.topcoder

    @staticmethod
    def is_challenge_ok(challenge):
        if u"registrants" not in challenge:
            return False

        if len(challenge[u"registrants"]) <= g_config.nb_seeds[-1]:
            return False

        return (challenge[u"challengeType"] in
                g_config.topcoder_challenge_type_whitelist)

    def training_set(self):
        condition = {
            u"postingDate": {
                u"$gte": g_config.topcoder_begin_date,
                u"$lt": g_config.topcoder_end_date,
            }
        }

        sorter = (u"postingDate", pymongo.DESCENDING)

        for challenge in self.db.challenges.find(condition).sort(*sorter):
            if self.is_challenge_ok(challenge):
                yield TopCoderChallenge(challenge)

    def test_set(self):
        condition = {
            u"postingDate": {
                u"$gte": g_config.topcoder_end_date,
            }
        }

        for challenge in self.db.challenges.find(condition):
            if self.is_challenge_ok(challenge):
                yield TopCoderChallenge(challenge)


class FreelancerProject(object):
    def __init__(self, pid, developers):
        self.id = pid
        self.name = pid
        self.regs = developers


class FreelancerDataset(object):
    def __init__(self):
        SDB_FILE = "datasets/freelancer.sqlite"
        self.scon = sqlite3.connect(SDB_FILE)
        self.sc = self.scon.cursor()

    @staticmethod
    def filter_project(row):
        technologies = [int(tech) for tech in row[1].strip().split(' ')]
        developers = row[2].strip().split(' ')

        for tech in g_config.freelancer_tech_requirement:
            if tech not in technologies:
                return None

        if len(developers) > g_config.nb_seeds[-1]:
            return developers

        return None

    def training_set(self):
        query = '''SELECT id,technologies,developers FROM projects
WHERE type=0 AND submit_date>=? AND submit_date<?
'''

        for row in self.sc.execute(query, (g_config.freelancer_begin_date,
                                           g_config.freelancer_end_date)):
            developers = self.filter_project(row)
            if developers is not None:
                yield FreelancerProject(row[0], developers)

    def test_set(self):
        query = '''SELECT id,technologies,developers FROM projects
WHERE type=0 AND submit_date>=?
'''

        for row in self.sc.execute(query, (g_config.freelancer_end_date,)):
            developers = self.filter_project(row)
            if developers is not None:
                yield FreelancerProject(row[0], developers)


class CF(object):
    def __init__(self, dataset):
        self.dataset = dataset

        self.users = {}
        self.m = None

        self.test_rounds = []
        self.results = defaultdict(list)
        self.predicted_ever = set()

    def train(self):
        num_challenges = 0
        user_index = 0

        for challenge in self.dataset.training_set():
            num_challenges += 1

            for handle in challenge.regs:
                if handle not in self.users:
                    self.users[handle] = user_index
                    user_index += 1

        num_users = user_index

        # The last column contains the numbers of registrants of each task.
        self.m = np.zeros((num_challenges, num_users + 1), dtype=np.uint8)

        for challenge_index, challenge in enumerate(self.dataset.training_set()):
            self.m[challenge_index, -1] = len(challenge.regs)

            for handle in challenge.regs:
                user_index = self.users[handle]
                self.m[challenge_index, user_index] = 1

        # 1 2 3    1 4 7
        # 4 5 6 -> 2 5 8
        # 7 8 9    3 6 9

        self.m = np.transpose(self.m)

    def test(self, seeds_selector, top_n=10):
        sim_func = getattr(sim, g_config.sim_func)

        start = time.time()
        self.predicted_ever.clear()

        nb_processed = 0
        accuracy_sum = 0
        recall_sum = 0

        for challenge in self.dataset.test_set():
            nb_seeds = seeds_selector(challenge, challenge.regs)
            if nb_seeds == 0 or nb_seeds >= len(challenge.regs):
                continue

            seeds = set()

            # Find nb_seeds old men.
            for handle in challenge.regs:
                # Not ever occurred in the training set.
                if handle not in self.users:
                    continue

                seeds.add(self.users[handle])

                if len(seeds) == nb_seeds:
                    break

            real = set()
            newbie_index = len(self.users) + 10000

            for handle in challenge.regs:
                if handle in self.users:
                    user_index = self.users[handle]
                else:  # TODO: Why do so? We can never find them out.
                    user_index = newbie_index
                    newbie_index += 1

                if user_index not in seeds:
                    real.add(user_index)

            assert len(real) > 0

            # Predict.
            predicted = set()

            for user_index in seeds:
                candidates = sim_func(self.m, user_index, top_n * 5)

                before = len(predicted)
                for peer_index in candidates:
                    if peer_index not in seeds and peer_index not in predicted:
                        predicted.add(peer_index)

                        if len(predicted) - before == top_n:
                            break

            if len(predicted) > 0:
                self.predicted_ever |= predicted

                intersection = real.intersection(predicted)
                accuracy = len(intersection) / float(len(predicted))
                recall = len(intersection) / float(len(real))

                result = Result(challenge.name,
                                len(real),
                                accuracy,
                                recall)

                self.results[challenge.id].append(result)

                nb_processed += 1
                accuracy_sum += accuracy
                recall_sum += recall

                print(challenge.name)
                print("> Accuracy: %5.2f%%" % (accuracy * 100))
                print("> Recall: %5.2f%% [#real: %2d]" % (recall * 100, len(real)))

        assert nb_processed > 0

        test_round = TestRound(time.time() - start,
                               accuracy_sum / float(nb_processed),
                               recall_sum / float(nb_processed),
                               self.diversity())
        self.test_rounds.append(test_round)

        print(test_round)

    def diversity(self):
        return len(self.predicted_ever) / float(self.m.shape[0] - 1)


def run_all_test_rounds(cf):
    for nb in g_config.nb_seeds:
        print("# seed(s) = %d:\n" % nb)
        cf.test(lambda ch, regs: nb if nb >= 1 else int(len(regs) * nb))
        print("")


def outpu_result(start_time, cf):
    sio = StringIO()
    stdout = sys.stdout
    sys.stdout = sio

    accuracy_sums = [0.0] * len(cf.test_rounds)
    recall_sums = list(accuracy_sums)
    num_test_cases = 0

    for results in cf.results.itervalues():
        assert len(results) == len(cf.test_rounds)

        num_test_cases += 1

        for i, result in enumerate(results):
            accuracy_sums[i] += result.accuracy
            recall_sums[i] += result.recall

    print("=============================\n")

    for i, nb in enumerate(g_config.nb_seeds):
        print("# seed(s) = %d:" % nb)
        print("  Accuracy:\t%.2f%%" % (accuracy_sums[i] / num_test_cases * 100.0))
        print("  Recall rate:\t%.2f%%" % (recall_sums[i] / num_test_cases * 100.0))
        print("  Diversity:\t%.2f%%" % (cf.test_rounds[i].diversity * 100.0))
        print("  Time cost:\t%.2fs\n" % cf.test_rounds[i].time)

    print("Training set size: {}".format(cf.m.shape))
    print("Test set size: %d" % num_test_cases)
    print("Total time cost: %.2fs.\n" % (time.time() - start_time))

    print("=============================\n")
    print(g_config.raw)

    from logger import get_current_timestamp
    ts = get_current_timestamp()
    with open("results/%s-%s.csv" % (ts, g_config.sim_func), "w") as outf:
        outf.write(datetime.now().isoformat() + "\n\n")
        outf.write(sio.getvalue())

    stdout.write(sio.getvalue())
    sys.stdout = stdout


def main():
    start_time = time.time()

    if g_config.dataset == "topcoder":
        dataset = TopCoderDataset()
    else:
        dataset = FreelancerDataset()

    cf = CF(dataset)
    cf.train()

    run_all_test_rounds(cf)

    outpu_result(start_time, cf)

    sim.ClearCache()


if __name__ == "__main__":
    main()
