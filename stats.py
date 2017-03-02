#!/usr/bin/env python2

from collections import defaultdict

import pymongo


client = pymongo.MongoClient()
db = client.topcoder


def platforms_and_technologies():
    count = defaultdict(int)

    for challenge in db.challenges.find():
        for plat in challenge["platforms"]:
            count[plat] += 1

        for tech in challenge["technology"]:
            count[tech] += 1

    for key in count:
        print "%s: %s" % (key, count[key])

    print "\nTotal:", len(count), "\n"


def winners():
    count = defaultdict(int)

    for challenge in db.challenges.find():
        winner_found = False

        for submission in challenge[u"finalSubmissions"]:
            if submission[u"placement"] == 1:
                if submission[u"submissionStatus"] == u"Active":
                    if winner_found:
                        print challenge
                        assert False

                    count[submission[u"handle"]] += 1
                    winner_found = True

    for key in count:
        print "%s: %s" % (key, count[key])

    print "\nTotal:", len(count), "\n"


def main():
    platforms_and_technologies()
    winners()


if __name__ == "__main__":
    main()
