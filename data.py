
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


g_config = Config()


class Data:
    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client.topcoder

    @staticmethod
    def is_challenge_ok(challenge):
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


class DlData(Data):
    def __init__(self):
        Data.__init__(self)

        self.plat_tech = defaultdict(int)
        self.nb_training = 0
        self.nb_test = 0

        def do_count(challenge):
            for plat in challenge["platforms"]:
                self.plat_tech[plat] += 1

            for tech in challenge["technology"]:
                self.plat_tech[tech] += 1

        for challenge in Data.training_set(self):
            self.nb_training += 1
            do_count(challenge)

        for challenge in Data.test_set(self):
            self.nb_test += 1
            do_count(challenge)

        for index, pt in enumerate(self.plat_tech):
            self.plat_tech[pt] = index

        print "# traning:", self.nb_training
        print "# test:", self.nb_test
        print "# plaforms & technologies:", len(self.plat_tech)

    def generate_matrix(self, nb_rows, iterator):
        OFFSET = 2
        nb_cols = len(self.plat_tech) + OFFSET + 1
        m = np.zeros((nb_rows, nb_cols), dtype=np.uint16)

        for index, challenge in enumerate(iterator(self)):
            m[index, 0] = challenge["prize"][0]
            m[index, 1] = len(challenge["prize"])

            for plat in challenge["platforms"]:
                m[index, self.plat_tech[plat] + OFFSET] = 1

            for tech in challenge["technology"]:
                m[index, self.plat_tech[tech] + OFFSET] = 1

        return m

    def training_set(self):
        return self.generate_matrix(self.nb_training, Data.training_set)

    def test_set(self):
        return self.generate_matrix(self.nb_test, Data.test_set)


def main():
    data = DlData()
    ts = data.training_set()
    np.savetxt("training.txt", ts, fmt="%d")


if __name__ == "__main__":
    main()
