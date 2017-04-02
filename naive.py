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


_mongo_client = None
_mongo_db = None

_sqlite_conn = None
_sqlite_cursor = None


def _connect_to_mongodb():
    global _mongo_client, _mongo_db

    if _mongo_client is None:
        _mongo_client = pymongo.MongoClient()
        _mongo_db = _mongo_client.topcoder


def _connect_to_sqlite_db():
    global _sqlite_conn, _sqlite_cursor

    _sqlite_conn = sqlite3.connect("datasets/freelancer.sqlite")
    _sqlite_cursor = _sqlite_conn.cursor()


def topcoder_rate(developers):
    _connect_to_mongodb()

    for i, dev in enumerate(developers):
        user = _mongo_db.users.find_one({u"handle": dev.uid})
        if user is not None:
            if g_config.topcoder_max_rating and u"maxRating" in user:
                dev.rating = user[u"maxRating"][u"rating"]
            else:
                dev.rating = 1.0

            if u"stats" in user:
                stats = user[u"stats"][u"DEVELOP"]

                if g_config.topcoder_winning_rate and stats[u"challenges"] > 0:
                    dev.rating *= (1.0 + float(stats[u"wins"]) / stats[u"challenges"])

                if g_config.topcoder_reliability:
                    max_reliability = 0.0

                    for subtrack in stats[u"subTracks"]:
                        r = subtrack[u"rank"][u"reliability"]
                        if r is not None:
                            max_reliability = max(max_reliability, r)

                    dev.rating *= (1.0 + max_reliability)

        dev.rating *= (1.0 + g_config.order_factor / (i + 1))

    return developers


def _topcoder():
    _connect_to_mongodb()

    for challenge in (_mongo_db.challenges
                               .find().sort(u"postingDate", pymongo.DESCENDING)
                               .limit(g_config.project_limit)):
        if not datasets.util.topcoder_is_ok(challenge):
            continue

        winner = datasets.util.topcoder_get_winner(challenge)
        if winner is None:
            continue

        registrants = challenge[u"registrants"]
        registrants.sort(key=lambda r: r[u"registrationDate"])

        developers = [Developer(reg[u"handle"]) for reg in registrants]
        topcoder_rate(developers)

        yield Project(developers=developers, winner=winner)


def freelancer_rate(developers):
    _connect_to_sqlite_db()

    for i, dev in enumerate(developers):
        _sqlite_cursor.execute(RATING_QUERY % dev.uid)
        row = _sqlite_cursor.fetchone()
        if row is None:
            continue

        developers[i].rating = row[0] * (1.0 + g_config.order_factor / (i + 1))

    return developers


def _freelancer():
    _connect_to_sqlite_db()

    query = SEL_PROJECTS_QUERY % g_config.project_limit
    _sqlite_cursor.execute(query)

    for project in _sqlite_cursor.fetchall():
        developers = [Developer(int(dev)) for dev in project[0].split(' ')]
        freelancer_rate(developers)

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

    for project in globals()['_' + g_config.dataset]():
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
