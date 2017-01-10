#!/usr/bin/env python2

import heapq
import sqlite3

import config.naive as g_config
from logger import Logger


ID = 0
TYPE = 1
SUBMIT_DATE = 2
BUDGET_MIN = 3
BUDGET_MAX = 4
TECHNOLOGIES = 5
DEVELOPERS = 6
WINNER = 7

SEL_PROJECTS_QUERY = 'SELECT * FROM "projects" ORDER BY "submit_date" DESC LIMIT %d'
RATING_QUERY = 'SELECT "rating" FROM "dev_ratings" WHERE "uid" = %d'


class Developer(object):
    def __init__(self, uid):
        self.uid = uid
        self.rating = 0.0


def predict():
    logger = Logger()
    logger.log(g_config.raw)
    logger.log("----------")

    con = sqlite3.connect("datasets/freelancer.sqlite")
    cursor = con.cursor()

    nb_projects = 0
    nb_correct = 0

    query = SEL_PROJECTS_QUERY % g_config.project_limit
    cursor.execute(query)

    for project in cursor.fetchall():
        all_users_rated = True
        devs = [Developer(int(dev)) for dev in project[DEVELOPERS].split(' ')]

        for i, dev in enumerate(devs):
            cursor.execute(RATING_QUERY % dev.uid)
            row = cursor.fetchone()
            if row is None:
                all_users_rated = False
                break

            devs[i].rating = row[0] + g_config.order_factor / (i + 1)

        if not all_users_rated:
            continue

        nb_projects += 1

        topn = min(g_config.topn, len(devs))
        hightest = heapq.nlargest(topn, devs, key=lambda d: d.rating)
        correct = False

        for dev in hightest:
            if dev.uid == project[WINNER]:
                print "Correct"

                correct = True
                nb_correct += 1

        if not correct:
            print "Wrong"

    logger.log("# projects: %d" % nb_projects)
    logger.log("# correct: %d" % nb_correct)
    logger.log("Correct rate: %g%%" % ((float(nb_correct) / nb_projects) * 100))

    logger.save("naive_predictor")


def main():
    predict()


if __name__ == "__main__":
    main()
