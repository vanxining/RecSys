#!/usr/bin/env python2

from __future__ import print_function

import argparse
from datetime import datetime

import pymongo
from dateutil.parser import parse


client = pymongo.MongoClient()


class Minute(object):
    def __init__(self, minute):
        self.minute = minute
        self.nb_projects = 0
        self.ratio_sum = 0.0
        self.nb_registrants = 0
        self.tmp_nb_registrants = 0

    def finish_project(self, nb_registrants_all):
        self.nb_projects += 1
        self.ratio_sum += float(self.tmp_nb_registrants) / nb_registrants_all
        self.nb_registrants += self.tmp_nb_registrants
        self.tmp_nb_registrants = 0

    def stats(self):
        return (self.ratio_sum / self.nb_projects * 100.0,
                float(self.nb_registrants) / self.nb_projects)


def topcoder(minutes):
    db = client.topcoder

    for challenge in db.challenges.find():
        if u"registrants" not in challenge:
            continue

        regs = challenge[u"registrants"]
        if len(regs) == 0:
            continue

        postingDate = challenge[u"postingDate"]

        for reg in regs:
            val = reg[u"registrationDate"]
            if type(val) is unicode:
                registrationDate = parse(val).replace(tzinfo=None)
            else:
                registrationDate = val

            delta = (registrationDate - postingDate).total_seconds()

            for minute in minutes:
                if delta <= minute.minute * 60:
                    minute.tmp_nb_registrants += 1

        for minute in minutes:
            minute.finish_project(len(regs))


def freelancer(minutes):
    db = client.freelancer

    for project in db.projects.find():
        if (minutes[-1].nb_projects + 1) % 100 == 0:
            print("counter:", minutes[-1].nb_projects + 1)

        if u"result" not in project or u"bids" not in project[u"result"]:
            continue

        if u"bid_avg" not in project[u"bid_stats"]:
            continue

        bids = project[u"result"][u"bids"]
        if len(bids) == 0:
            continue

        postingDate = datetime.fromtimestamp(project[u"submitdate"])

        for bid in bids:
            registrationDate = datetime.fromtimestamp(bid[u"submitdate_ts"])
            delta = (registrationDate - postingDate).total_seconds()

            for minute in minutes:
                if delta <= minute.minute * 60:
                    minute.tmp_nb_registrants += 1

        for minute in minutes:
            minute.finish_project(len(bids))


def main():
    parser = argparse.ArgumentParser("full_stats")
    parser.add_argument("dataset",
                        choices=("topcoder", "freelancer"),
                        help="the dataset to census")

    args = parser.parse_args()

    minutes = []
    minute = 1
    while minute <= 2 ** 14:
        minutes.append(Minute(minute))
        minute *= 2

    globals()[args.dataset](minutes)

    for minute in minutes:
        print("%d minutes: %.2f%% - %.1f" % ((minute.minute,) + minute.stats()))


if __name__ == "__main__":
    main()
