#!/usr/bin/env python2

from collections import defaultdict

import pymongo

import datasets.util


client = pymongo.MongoClient()
db = client.topcoder


def platforms_and_technologies():
    count = defaultdict(int)

    for challenge in db.challenges.find():
        for plat in challenge[u"platforms"]:
            count[plat] += 1

        for tech in challenge[u"technology"]:
            count[tech] += 1

    for key in sorted(count.keys()):
        print u"%s: %s" % (key, count[key])

    print "\nTotal:", len(count), "\n"


def winners():
    count = defaultdict(int)

    for challenge in db.challenges.find():
        winner = datasets.util.topcoder_get_winner(challenge)
        if winner is not None:
            count[winner] += 1

    for key in sorted(count.keys()):
        print u"%s: %s" % (key, count[key])

    print "\nTotal:", len(count), "\n"


def main():
    platforms_and_technologies()
    winners()


if __name__ == "__main__":
    main()
