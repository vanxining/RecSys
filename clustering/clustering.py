#!/usr/bin/env python2

import pymongo
import numpy as np


client = pymongo.MongoClient()
db = client.topcoder


def platforms_and_technologies():
    platec = {}

    for challenge in db.challenges.find():
        for plat in challenge["platforms"]:
            platec[plat.lower()] = 0

        for tech in challenge["technology"]:
            platec[tech.lower()] = 0

    for index, key in enumerate(platec):
        platec[key] = index

    affinity = np.zeros((len(platec), len(platec)), dtype=np.uint8)

    for challenge in db.challenges.find():
        s = set()

        for plat in challenge["platforms"]:
            s.add(plat.lower())

        for tech in challenge["technology"]:
            s.add(tech.lower())

        for x in s:
            for y in s:
                if x == y:
                    continue

                affinity[platec[x], platec[y]] += 1
                affinity[platec[y], platec[x]] += 1

    return affinity


if __name__ == "__main__":
    platforms_and_technologies()

