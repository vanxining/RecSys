#!/usr/bin/env python2

from __future__ import print_function

import argparse

from collections import defaultdict
from datetime import datetime

import pymongo


client = pymongo.MongoClient()


class Dates(object):
    def __init__(self):
        self.begin = datetime(2036, 12, 31)
        self.end = datetime(1970, 1, 1)


def topcoder():
    db = client.topcoder

    nb_projects = 0
    nb_finished_projects = 0
    prize_sum = 0
    dates = Dates()
    lasting_days = 0.0
    registering = defaultdict(int)
    winning = defaultdict(int)

    for challenge in db.challenges.find():
        nb_projects += 1
        prize_sum += sum(challenge[u"prize"])

        postingDate = challenge[u"postingDate"]
        if postingDate < dates.begin:
            dates.begin = postingDate
        elif postingDate > dates.end:
            dates.end = postingDate

        delta = challenge[u"submissionEndDate"] - postingDate
        lasting_days += delta.total_seconds() / (24 * 60 * 60.0)

        for registrant in challenge[u"registrants"]:
            registering[registrant[u"handle"]] += 1

        for submission in challenge[u"finalSubmissions"]:
            if submission[u"placement"] == 1:
                if submission[u"submissionStatus"] == u"Active":
                    handle = submission[u"handle"]
                    if handle == u"Applications":
                        continue

                    nb_finished_projects += 1
                    winning[handle] += 1

    print("total project count:", nb_projects)
    print("total developer count:", len(registering))
    print("earliest project:", dates.begin)
    print("latest project:", dates.end)
    print("project average lasting days: %.1f days\n" % (lasting_days / nb_projects))
    print("project average prize: $%.1f\n" % (prize_sum / float(nb_projects)))

    users = registering.keys()
    users.sort(key=lambda u: registering[u], reverse=True)

    print("developer max registering times: ")
    for i in xrange(5):
        print("  %s: %d" % (users[i], registering[users[i]]))

    nb_registering = sum(registering.values())
    print("project average registrant count: %.1f" % (nb_registering / float(nb_projects)))
    print("developer average registering count: %.1f\n" % (nb_registering / float(len(registering))))

    users = winning.keys()
    users.sort(key=lambda u: winning[u], reverse=True)

    print("developer max winning times: ")
    for i in xrange(5):
        print("  %s: %d" % (users[i], winning[users[i]]))

    print("developer average winning times: %.1f" % (nb_finished_projects / float(len(winning))))


def freelancer():
    db = client.freelancer

    nb_projects = 0
    nb_finished_projects = 0
    prize_sum = 0.0
    dates = Dates()
    registering = defaultdict(int)
    winning = defaultdict(int)

    for project in db.projects.find():
        if (nb_projects + 1) % 100 == 0:
            print("counter:", nb_projects + 1)

        if u"result" not in project or u"bids" not in project[u"result"]:
            continue

        if u"bid_avg" not in project[u"bid_stats"]:
            continue

        nb_projects += 1
        prize_sum += project[u"bid_stats"][u"bid_avg"]

        postingDate = datetime.fromtimestamp(project[u"submitdate"])
        if postingDate < dates.begin:
            dates.begin = postingDate
        elif postingDate > dates.end:
            dates.end = postingDate

        for bid in project[u"result"][u"bids"]:
            user = bid[u"user"][u"username"]
            registering[user] += 1

            if "is_awarded" in bid and bid["is_awarded"]:
                nb_finished_projects += 1
                winning[user] += 1

    print("total project count:", nb_projects)
    print("total developer count:", len(registering))
    print("earliest project:", dates.begin)
    print("latest project:", dates.end)
    print("project average prize: $%.1f\n" % (prize_sum / float(nb_projects)))

    users = registering.keys()
    users.sort(key=lambda u: registering[u], reverse=True)

    print("developer max registering times: ")
    for i in xrange(5):
        print("  %s: %d" % (users[i], registering[users[i]]))

    nb_registering = sum(registering.values())
    print("project average registrant count: %.1f" % (nb_registering / float(nb_projects)))
    print("developer average registering count: %.1f\n" % (nb_registering / float(len(registering))))

    users = winning.keys()
    users.sort(key=lambda u: winning[u], reverse=True)

    print("developer max winning times: ")
    for i in xrange(5):
        print("  %s: %d" % (users[i], winning[users[i]]))

    print("developer average winning times: %.1f" % (nb_finished_projects / float(len(winning))))


def main():
    parser = argparse.ArgumentParser("full_stats")
    parser.add_argument("dataset",
                        choices=("topcoder", "freelancer"),
                        help="the dataset to extract")

    args = parser.parse_args()
    globals()[args.dataset]()


if __name__ == "__main__":
    main()
