#!/usr/bin/env python2

import sqlite3

import numpy as np
from sklearn.cluster import KMeans

import config.clustering as g_config
from logger import Logger


logger = Logger()

SEL_PROJECTS_QUERY = 'SELECT "technologies" FROM "projects" LIMIT %d'

con = sqlite3.connect("datasets/freelancer.sqlite")
cursor = con.cursor()


def index_technologies():
    technologies = {}
    nb_projects = 0

    cursor.execute(SEL_PROJECTS_QUERY % g_config.fl_projects_limit)
    for row in cursor.fetchall():
        nb_projects += 1

        for tech in row[0].split(' '):
            t = int(tech)
            if t not in technologies:
                technologies[t] = len(technologies)

    logger.log("# technologies: %d" % len(technologies))
    logger.log("# projects: %d" % nb_projects)

    return technologies, nb_projects


def scikit_learn_format():
    technologies, nb_projects = index_technologies()
    data = np.zeros((nb_projects, len(technologies)), dtype=np.uint8)

    cursor.execute(SEL_PROJECTS_QUERY % g_config.fl_projects_limit)
    for index, row in enumerate(cursor.fetchall()):
        for tech in row[0].split(' '):
            data[index, technologies[int(tech)]] = 1

    return np.transpose(data)


def cluster():
    estimator = KMeans(n_clusters=g_config.nb_fl_clusters)
    data = scikit_learn_format()

    labels = estimator.fit_predict(data)
    print(labels)


def main():
    cluster()


if __name__ == "__main__":
    main()
