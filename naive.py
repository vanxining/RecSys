#!/usr/bin/env python2

import heapq
import sqlite3
from collections import namedtuple

import pymongo

import config.naive as g_config
import datasets.util
from logger import Logger


SEL_PROJECTS_QUERY = 'SELECT "developers","winner" FROM "projects" ORDER BY "submit_date" DESC LIMIT %d'
RATING_QUERY = 'SELECT "rating" FROM "dev_ratings" WHERE "uid" = %d'


class Developer(object):
    def __init__(self, uid, rating=0.0):
        self.uid = uid
        self.rating = rating


Project = namedtuple("Project", ("developers", "winner",))


def topcoder():
    client = pymongo.MongoClient()
    db = client.topcoder

    sorter = (u"postingDate", pymongo.DESCENDING)
    for challenge in db.challenges.find().sort(*sorter).limit(g_config.project_limit):
        if not datasets.util.topcoder_is_ok(challenge):
            continue

        winner = datasets.util.topcoder_get_winner(challenge)
        if winner is None:
            continue

        developers = []
        registrants = challenge[u"registrants"]
        registrants.sort(key=lambda r: r[u"registrationDate"])

        for reg in registrants:
            handle = reg[u"handle"]
            user = db.users.find_one({u"handle": handle})
            if user is not None and u"maxRating" in user:
                rating = user[u"maxRating"][u"rating"]
            else:
                rating = 0

            developers.append(Developer(handle, rating))

        yield Project(developers=developers, winner=winner)


def freelancer():
    con = sqlite3.connect("datasets/freelancer.sqlite")
    cursor = con.cursor()

    query = SEL_PROJECTS_QUERY % g_config.project_limit
    cursor.execute(query)

    for project in cursor.fetchall():
        developers = [Developer(int(dev)) for dev in project[0].split(' ')]

        for i, dev in enumerate(developers):
            cursor.execute(RATING_QUERY % dev.uid)
            row = cursor.fetchone()
            if row is None:
                continue

            developers[i].rating = row[0] + g_config.order_factor / (i + 1)

        yield Project(developers=developers, winner=project[1])


def output_result(nb_correct, nb_projects):
    logger = Logger()

    logger.log(g_config.raw)
    logger.log("----------")

    logger.log("# projects: %d" % nb_projects)
    logger.log("# correct: %d" % nb_correct)
    logger.log("Accuracy: %.2f%%" % ((float(nb_correct) / nb_projects) * 100.0))

    logger.save("naive-predictor-" + g_config.dataset)


def predict():
    nb_projects = 0
    nb_correct = 0

    for project in globals()[g_config.dataset]():
        nb_projects += 1

        topn = min(g_config.topn, len(project.developers))
        hightest = heapq.nlargest(topn, project.developers, key=lambda d: d.rating)

        for dev in hightest:
            if dev.uid == project.winner:
                nb_correct += 1
                break

    return nb_correct, nb_projects


def main():
    output_result(*predict())


if __name__ == "__main__":
    main()
