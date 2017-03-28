#!/usr/bin/env python2

from collections import defaultdict
from datetime import datetime

import numpy as np
import pymongo

import config.data as g_config
import datasets.util
import logger
import ptcat


class Data(object):
    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client.topcoder

    def is_challenge_ok(self, challenge):
        if not g_config.is_challenge_type_ok(challenge[u"challengeType"]):
            return False

        return datasets.util.topcoder_is_ok(challenge)

    def training_set(self):
        condition = {
            u"postingDate": {
                u"$gte": g_config.begin_date,
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


def _calc_duration(challenge, keyword):
    posting_date = challenge[u"postingDate"]
    end_date = challenge[keyword]
    delta = end_date - posting_date

    return delta.days


def _calc_max_working_days(challenge):
    return _calc_duration(challenge, u"submissionEndDate")


def _calc_appeals_duration(challenge):
    return _calc_duration(challenge, u"appealsEndDate")


class DlData(Data):
    def __init__(self):
        Data.__init__(self)

        self.logger = logger.Logger()

        self.logger.log(g_config.raw)
        self.logger.log("----------")

        self.user_win_times = None
        self._count_user_win_times()

        self.user_ids = {}
        index = 0
        for user in self.user_win_times:
            if self.user_win_times[user] >= g_config.win_times_threshold:
                self.user_ids[user] = index
                index += 1

        challenge_types = set()

        self.nb_training = 0
        self.nb_test = 0

        for challenge in Data.training_set(self):
            challenge_types.add(challenge[u"challengeType"])
            self.nb_training += 1

        for challenge in Data.test_set(self):
            challenge_types.add(challenge[u"challengeType"])
            self.nb_test += 1

        self.challenge_type_ids = {}
        for index, challenge_type in enumerate(challenge_types):
            self.challenge_type_ids[challenge_type] = index

        self.logger.log("Training set size: %d" % self.nb_training)
        self.logger.log("Test set size: %d" % self.nb_test)

    def _count_vital_features(self):
        fake_line = {}
        self._fill_line(fake_line, self.db.challenges.find()[0])

        return len(fake_line)

    def _ptcat_index(self):
        nb_vital_features = self._count_vital_features()

        def ptcat_index(platech):
            index = ptcat.get_category(platech, g_config.categorize_platech)
            return nb_vital_features + index - 1

        return ptcat_index

    def _count_user_win_times(self):
        user_win_times = defaultdict(int)

        for challenge in Data.training_set(self):
            winner = datasets.util.topcoder_get_winner(challenge)
            if winner is not None:
                user_win_times[winner] += 1

        self.user_win_times = user_win_times
        self._output_user_win_times_stats()

    def _output_user_win_times_stats(self):
        max_win_times = 0
        biggest_winner = None

        for winner in self.user_win_times:
            if max_win_times < self.user_win_times[winner]:
                max_win_times = self.user_win_times[winner]
                biggest_winner = winner

        self.logger.log("Max win times: %d" % max_win_times)
        self.logger.log("Biggest winner: " + biggest_winner)

    def is_challenge_ok(self, challenge):
        ok = Data.is_challenge_ok(self, challenge)

        # count_user_win_times() refers this function
        if ok and self.user_win_times is not None:
            winner = datasets.util.topcoder_get_winner(challenge)
            if winner is None:
                return False
            else:
                return (self.user_win_times[winner] >=
                        g_config.win_times_threshold)
        else:
            return ok

    def _validate_matrix(self, m, iterator):
        ptcat_index = self._ptcat_index()

        count = 20

        for index, challenge in enumerate(iterator(self)):
            if index % 5 != 0:
                continue

            for plat in challenge[u"platforms"]:
                assert m[index, ptcat_index(plat)] == 1

            for tech in challenge[u"technology"]:
                assert m[index, ptcat_index(tech)] == 1

            winner = datasets.util.topcoder_get_winner(challenge)
            assert winner is not None

            assert m[index, -1] == self.user_ids[winner]
            assert self.user_win_times[winner] >= g_config.win_times_threshold

            count -= 1
            if count == 0:
                break

    def _fill_line(self, line, challenge):
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

        # Challenge type (F2F, ...)
        if len(g_config.challenge_type_whitelist) != 1:
            line[index] = self.challenge_type_ids[challenge[u"challengeType"]]
            index += 1

        # Appeals duration in days
        line[index] = _calc_appeals_duration(challenge)
        index += 1

    def _generate_matrix(self, nb_rows, iterator):
        nb_vital_features = self._count_vital_features()
        nb_platech = ptcat.get_number_of_platech(g_config.categorize_platech)
        nb_cols = nb_vital_features + nb_platech + 1
        ptcat_index = self._ptcat_index()

        m = np.zeros((nb_rows, nb_cols), dtype=np.uint16)

        for index, challenge in enumerate(iterator(self)):
            line = m[index]
            self._fill_line(line, challenge)

            for plat in challenge[u"platforms"]:
                line[ptcat_index(plat)] = 1

            for tech in challenge[u"technology"]:
                line[ptcat_index(tech)] = 1

            winner = datasets.util.topcoder_get_winner(challenge)
            assert winner is not None
            line[nb_cols - 1] = self.user_ids[winner]

        return m

    def training_set(self):
        return self._generate_matrix(self.nb_training, Data.training_set)

    def test_set(self):
        return self._generate_matrix(self.nb_test, Data.test_set)

    def generate(self):
        training_set = self.training_set()
        self._validate_matrix(training_set, Data.training_set)

        test_set = self.test_set()
        self._validate_matrix(test_set, Data.test_set)

        np.savetxt("datasets/training_topcoder.txt", training_set, fmt="%d")
        np.savetxt("datasets/test_topcoder.txt", test_set, fmt="%d")

        self.logger.log("# distinct developers: %d" % len(self.user_ids))
        self.logger.log("DONE!")

        self.logger.save("topcoder-dataset")


def main():
    data = DlData()
    data.generate()


if __name__ == "__main__":
    main()
