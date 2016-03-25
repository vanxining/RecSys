
import ConfigParser

from datetime import datetime
from collections import defaultdict

import pymongo
import numpy as np


def cmp_datetime(a, b):
    return -1 if a < b else 1 if a > b else 0


class Config:
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read("config/data.ini")

        self.year_from = config.getint("default", "year_from")

        end_date = config.get("default", "end_date").split('-')
        self.end_date = datetime(*[int(i) for i in end_date])

        self.win_times_threshold = config.getint("default",
                                                 "win_times_threshold")


g_config = Config()


class Data(object):
    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client.topcoder

    def is_challenge_ok(self, challenge):
        if u"registrants" not in challenge:
            return False

        if len(challenge[u"registrants"]) == 0:
            return False

        # TODO: challengeType
        return (challenge[u"challengeType"] == u"First2Finish" and
                challenge[u"type"] == u"develop" and
                len(challenge["prize"]) > 0)

    def training_set(self):
        condition = {
            u"postingDate": {
                u"$gte": datetime(g_config.year_from, 1, 1),
                u"$lt": g_config.end_date,
            }
        }

        sorter = (u"postingDate", pymongo.DESCENDING)

        for challenge in self.db.challenges.find(condition).sort(*sorter):
            if self.is_challenge_ok(challenge):
                yield challenge

    def test_set(self):
        condition = {
            u"postingDate": {
                u"$gte": g_config.end_date,
            }
        }

        for challenge in self.db.challenges.find(condition):
            if self.is_challenge_ok(challenge):
                yield challenge


def get_winner(challenge):
    for submission in challenge[u"finalSubmissions"]:
        if submission[u"placement"] == 1:
            if submission[u"submissionStatus"] == u"Active":
                return submission[u"handle"]


class DlData(Data):
    NUM_VITAL_FEATURES = 2

    def __init__(self):
        Data.__init__(self)

        self.user_win_times = None
        self.count_user_win_times()

        self.user_ids = {}
        for index, user in enumerate(self.user_win_times):
            self.user_ids[user] = index

        self.plat_tech = defaultdict(int)
        self.nb_training = 0
        self.nb_test = 0

        for challenge in Data.training_set(self):
            self.nb_training += 1
            self.count_platforms_and_technologies(challenge)

        for challenge in Data.test_set(self):
            self.nb_test += 1
            self.count_platforms_and_technologies(challenge)

        for index, pt in enumerate(self.plat_tech):
            self.plat_tech[pt] = index

        print "# traning:", self.nb_training
        print "# test:", self.nb_test
        print "# plaforms & technologies:", len(self.plat_tech)

    def count_user_win_times(self):
        user_win_times = defaultdict(int)

        for challenge in Data.training_set(self):
            user_win_times[get_winner(challenge)] += 1

        self.user_win_times = user_win_times

        print "Max win times:", max(user_win_times.values())

    def count_platforms_and_technologies(self, challenge):
        for plat in challenge[u"platforms"]:
            self.plat_tech[plat] += 1

        for tech in challenge[u"technology"]:
            self.plat_tech[tech] += 1

    def is_challenge_ok(self, challenge):
        ok = Data.is_challenge_ok(self, challenge)

        if ok and self.user_win_times:
            return (self.user_win_times[get_winner(challenge)] >=
                    g_config.win_times_threshold)
        else:
            return ok

    def validate_matrix(self, m):
        count = 20
        for index, challenge in enumerate(Data.training_set(self)):
            if index % 5 != 0:
                continue

            count -= 1
            if count == 0:
                break

            for plat in challenge[u"platforms"]:
                assert m[index, self.plat_tech[plat] + self.NUM_VITAL_FEATURES] == 1

            for tech in challenge[u"technology"]:
                assert m[index, self.plat_tech[tech] + self.NUM_VITAL_FEATURES] == 1

            winner = get_winner(challenge)

            assert m[index, -1] == self.user_ids[winner]
            assert self.user_win_times[winner] >= g_config.win_times_threshold

    def generate_matrix(self, nb_rows, iterator):
        nb_cols = len(self.plat_tech) + self.NUM_VITAL_FEATURES + 1
        m = np.zeros((nb_rows, nb_cols), dtype=np.uint16)

        for index, challenge in enumerate(iterator(self)):
            m[index, 0] = challenge[u"prize"][0]
            m[index, 1] = len(challenge[u"prize"])

            for plat in challenge[u"platforms"]:
                m[index, self.plat_tech[plat] + self.NUM_VITAL_FEATURES] = 1

            for tech in challenge[u"technology"]:
                m[index, self.plat_tech[tech] + self.NUM_VITAL_FEATURES] = 1

            m[index, nb_cols - 1] = self.user_ids[get_winner(challenge)]

        return m

    def training_set(self):
        return self.generate_matrix(self.nb_training, Data.training_set)

    def test_set(self):
        return self.generate_matrix(self.nb_test, Data.test_set)


def main():
    data = DlData()

    ts = data.training_set()
    data.validate_matrix(ts)
    # np.savetxt("training.txt", ts[:100, -20:], fmt="%d")


if __name__ == "__main__":
    main()
