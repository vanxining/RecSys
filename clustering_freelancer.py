#!/usr/bin/env python2

import sqlite3

import numpy as np

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


def scikit_learn_format(dtype=np.uint8):
    technologies, nb_projects = index_technologies()
    data = np.zeros((nb_projects, len(technologies)), dtype=dtype)

    cursor.execute(SEL_PROJECTS_QUERY % g_config.fl_projects_limit)
    for index, row in enumerate(cursor.fetchall()):
        for tech in row[0].split(' '):
            data[index, technologies[int(tech)]] = 1

    return np.transpose(data)


def distance_matrix(dtype=np.uint32):
    tech_indices, _ = index_technologies()
    data = np.zeros((len(tech_indices), len(tech_indices)), dtype=dtype)

    cursor.execute(SEL_PROJECTS_QUERY % g_config.fl_projects_limit)
    for row in cursor.fetchall():
        technologies = [tech_indices[int(tech)] for tech in row[0].split(' ')]

        for x in technologies:
            for y in technologies:
                if x == y:
                    continue

                data[x, y] += 1

    max_element = data.max(axis=(0, 1))
    data = max_element - data

    return data, max_element


def kmeans():
    from sklearn.cluster import KMeans

    estimator = KMeans(n_clusters=g_config.nb_fl_clusters)
    return estimator.fit_predict(scikit_learn_format())


def dbscan():
    from sklearn.cluster import DBSCAN

    data, max_element = distance_matrix()

    db = DBSCAN(eps=(max_element - 1), min_samples=10, metric="precomputed")
    db.fit(data)

    return db.labels_


def spectral():
    from sklearn.cluster import SpectralClustering

    data, max_element = distance_matrix()

    s = SpectralClustering(n_clusters=g_config.nb_fl_clusters, affinity="precomputed")
    s.fit(data)

    return s.labels_


def cluster():
    labels = globals()[g_config.fl_clustering_algorithm]()
    print(labels)


def main():
    cluster()


if __name__ == "__main__":
    main()
