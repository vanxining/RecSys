#!/usr/bin/env python2

import StringIO

from datetime import datetime
from collections import defaultdict

import pymongo
import numpy as np

import myconfig
import ptcat


def cmp_datetime(a, b):
    return -1 if a < b else 1 if a > b else 0


class Config(myconfig.MyConfig):
    def __init__(self):
        super(Config, self).__init__()
        config = self.open("config/data.ini")

        self.year_from = config.getint("default", "year_from")
        self.end_date = myconfig.parse_date(config.get("default", "end_date"))

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
                len(challenge[u"prize"]) > 0)

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


def _calc_duration(challenge, keyword):
    posting_date = challenge["postingDate"]
    end_date = challenge[keyword]
    delta = end_date - posting_date

    return delta.days


def _calc_max_working_days(challenge):
    return _calc_duration(challenge, "submissionEndDate")


def _calc_appeals_duration(challenge):
    return _calc_duration(challenge, "appealsEndDate")


class DlData(Data):
    def __init__(self):
        Data.__init__(self)

        self.sio = StringIO.StringIO()

        self.user_win_times = None
        self.count_user_win_times()

        self.user_ids = {}
        index = 0
        for user in self.user_win_times:
            if self.user_win_times[user] >= g_config.win_times_threshold:
                self.user_ids[user] = index
                index += 1

        self.nb_training = 0
        self.nb_test = 0

        for _ in Data.training_set(self):
            self.nb_training += 1

        for _ in Data.test_set(self):
            self.nb_test += 1

        self.log("# traning: %d" % self.nb_training)
        self.log("# test: %d" % self.nb_test)

    def log(self, msg):
        print(msg)
        self.sio.write(msg + "\n")

    def _count_vital_features(self):
        fake_line = {}
        DlData._fill_line(fake_line, self.db.challenges.find()[0])

        return len(fake_line)

    def count_user_win_times(self):
        user_win_times = defaultdict(int)

        for challenge in Data.training_set(self):
            user_win_times[get_winner(challenge)] += 1

        self.user_win_times = user_win_times

        self.log("Max win times: %d" % max(user_win_times.values()))

    def is_challenge_ok(self, challenge):
        ok = Data.is_challenge_ok(self, challenge)

        if ok and self.user_win_times:
            return (self.user_win_times[get_winner(challenge)] >=
                    g_config.win_times_threshold)
        else:
            return ok

    def validate_matrix(self, m, iterator):
        nb_vital_features = self._count_vital_features()

        def ptcat_index(platech):
            return nb_vital_features + ptcat.get_category(platech) - 1

        count = 20

        for index, challenge in enumerate(iterator(self)):
            if index % 5 != 0:
                continue

            for plat in challenge[u"platforms"]:
                assert m[index, ptcat_index(plat)] == 1

            for tech in challenge[u"technology"]:
                assert m[index, ptcat_index(tech)] == 1

            winner = get_winner(challenge)

            assert m[index, -1] == self.user_ids[winner]
            assert self.user_win_times[winner] >= g_config.win_times_threshold

            count -= 1
            if count == 0:
                break

    @staticmethod
    def _fill_line(line, challenge):
        index = 0

        # First prize
        line[index] = challenge[u"prize"][0]
        index += 1

        # Number of prize
        line[index] = len(challenge[u"prize"])
        index += 1

        if False:
            # TODO: Review type
            line[index] = 1
            index += 1

        # Max working days
        line[index] = _calc_max_working_days(challenge)
        index += 1

        if False:
            # TODO: Type (develop, ...)
            line[index] = 1
            index += 1

            # TODO: Challenge type (F2F, ...)
            line[index] = 1
            index += 1

        # Appeals duration in days
        line[index] = _calc_appeals_duration(challenge)
        index += 1

    def generate_matrix(self, nb_rows, iterator):
        nb_vital_features = self._count_vital_features()
        nb_platech = ptcat.get_number_of_platech()
        nb_cols = nb_vital_features + nb_platech + 1

        def ptcat_index(platech):
            return nb_vital_features + ptcat.get_category(platech) - 1

        m = np.zeros((nb_rows, nb_cols), dtype=np.uint16)

        for index, challenge in enumerate(iterator(self)):
            line = m[index]
            DlData._fill_line(line, challenge)

            for plat in challenge[u"platforms"]:
                line[ptcat_index(plat)] = 1

            for tech in challenge[u"technology"]:
                line[ptcat_index(tech)] = 1

            line[nb_cols - 1] = self.user_ids[get_winner(challenge)]

        return m

    def training_set(self):
        return self.generate_matrix(self.nb_training, Data.training_set)

    def test_set(self):
        return self.generate_matrix(self.nb_test, Data.test_set)


def main():
    data = DlData()

    training_set = data.training_set()
    data.validate_matrix(training_set, Data.training_set)

    test_set = data.test_set()
    data.validate_matrix(test_set, Data.test_set)

    np.savetxt("datasets/training.txt", training_set, fmt="%d")
    np.savetxt("datasets/test.txt", test_set, fmt="%d")

    data.log("# distinct developers: %d" % len(data.user_ids))
    data.log("DONE!")

    ts = myconfig.get_current_timestamp()
    with open("results/%s-dataset.log" % ts, "w") as outf:
        outf.write(data.sio.getvalue())


if __name__ == "__main__":
    main()
