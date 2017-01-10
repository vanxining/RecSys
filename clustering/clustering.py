#!/usr/bin/env python2

import numpy as np
import pymongo
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

    print("# platforms and technologies: %d" % len(platec))
    print("# challenges: %d" % nb_challenges)

    return platec, nb_challenges


def calc_platec_affinity():
    platec, _ = extract_all()
    affinity = np.zeros((len(platec), len(platec)), dtype=np.uint8)
    s = set()

    for challenge in db.challenges.find():
        for plat in challenge["platforms"]:
            s.add(plat.lower())

        for tech in challenge["technology"]:
            s.add(tech.lower())

        for x in s:
            for y in s:
                if x == y:
                    continue

                affinity[platec[x], platec[y]] += 1

        s.clear()

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
    estimator = KMeans(n_clusters=10)
    data = scikit_learn_format()

    labels = estimator.fit_predict(data)
    print labels


def main():
    cluster()
    quit()

    affinity = calc_platec_affinity()
    print affinity[0]


if __name__ == "__main__":
    main()
