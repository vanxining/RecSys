#!/usr/bin/env python2

import pymongo
import numpy as np
from sklearn.cluster import KMeans


client = pymongo.MongoClient()
db = client.topcoder


def extract_all():
    platec = {}
    nb_challenges = 0

    for challenge in db.challenges.find():
        nb_challenges += 1

        for plat in challenge["platforms"]:
            platec[plat.lower()] = 0

        for tech in challenge["technology"]:
            platec[tech.lower()] = 0

    for index, key in enumerate(platec):
        platec[key] = index

    return platec, nb_challenges


def platforms_and_technologies():
    platec, _ = extract_all()
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


def scikit_learn_format():
    platec, nb_challenges = extract_all()
    data = np.zeros((nb_challenges, len(platec)), dtype=np.uint8)

    for index, challenge in enumerate(db.challenges.find()):
        for plat in challenge["platforms"]:
            data[index, platec[plat.lower()]] = 1

        for tech in challenge["technology"]:
            data[index, platec[tech.lower()]] = 1

    return np.transpose(data)


def cluster():
    estimator = KMeans(n_clusters=8)
    data = scikit_learn_format()
    labels = estimator.fit_predict(data)
    print labels
    quit()


if __name__ == "__main__":
    cluster()
    print platforms_and_technologies()

