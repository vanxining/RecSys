#!/usr/bin/env python2

from pymongo import MongoClient

from datetime import datetime
from collections import defaultdict


client = MongoClient()
db = client.topcoder


def census(date_from):
    condition = {
        u"postingDate": {
            u"$gte": date_from,
        }
    }

    numChallenges = 0
    types = defaultdict(int)
    challengeTypes = defaultdict(int)

    for challenge in db.challenges.find(condition):
        numChallenges += 1
        types[challenge[u"type"]] += 1
        challengeTypes[challenge[u"challengeType"]] += 1

    print "Total:", numChallenges

    print ""
    print "Type distribution:"
    for t in types:
        print "  ", t, types[t]

    print ""
    print "challengeType distribution:"
    for ct in challengeTypes:
        print "  ", ct, challengeTypes[ct]


if __name__ == "__main__":
    census(datetime(2015, 1, 1))
