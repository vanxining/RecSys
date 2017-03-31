#!/usr/bin/env python2

import numpy as np

import config.classifiers as g_config
import datasets

from logger import Logger


def _create_classifier():
    if g_config.classifier == "NB":
        from sklearn.naive_bayes import GaussianNB
        return GaussianNB()

    if g_config.classifier.startswith("DT"):
        from sklearn import tree

        criterion = "entropy"
        if g_config.classifier == "DTG":
            criterion = "gini"

        return tree.DecisionTreeClassifier(criterion=criterion)

    if g_config.classifier == "LR":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression()

    if g_config.classifier == "MLP":
        from mlp import MLP
        return MLP()


def update_ratings(devs):
    if g_config.dataset != "freelancer":
        return False

    import datasets.dev_mappings_freelancer as mappings

    import sqlite3
    conn = sqlite3.connect("datasets/freelancer.sqlite")
    cursor = conn.cursor()

    for dev in devs:
        cursor.execute('SELECT "rating" FROM "dev_ratings" WHERE "uid" = %d' %
                        mappings.developers[dev[0]])
        row = cursor.fetchone()
        if row is None:
            return

        dev[1] = row[0]

    devs.sort(key=lambda d: d[1], reverse=True)

    return True


def recommend(proba):
    pairs = []
    for index, p in enumerate(proba):
        pairs.append([index, p])

    pairs.sort(key=lambda pair: pair[1], reverse=True)

    nb_rec = min(g_config.topn, len(proba) / 2)

    if g_config.adjust_rec_list:
        nb_intact = g_config.rec_list_intact_length
        if nb_intact < nb_rec:
            nb_candidates = (nb_rec - nb_intact) * 2
            candidates = pairs[nb_intact:(nb_intact + nb_candidates)]

            if update_ratings(candidates):
                pairs = pairs[:nb_intact] + candidates

    rec = []
    for dev in pairs[:nb_rec]:
        rec.append(dev[0])

    return rec


def output_result(classifier, nb_test, nb_correct, diversity):
    logger = Logger()

    logger.log(str(type(classifier)))
    logger.log(g_config.raw)
    logger.log("----------")
    logger.log("# correct: %g/%d" % (nb_correct, nb_test))
    logger.log("Accuracy: %.2f%%" % (float(nb_correct) / nb_test * 100.0))
    logger.log("Diversity: %.2f%%" % (diversity * 100.0))

    fname = "classifiers-%s-%s" % (g_config.dataset, g_config.classifier)
    logger.save(fname)


def run(classifier, dataset):
    classifier.fit(dataset.X_train, dataset.y_train)

    with np.errstate(over="ignore"):
        proba = classifier.predict_proba(dataset.X_test)

    lucky = set()
    nb_correct = 0

    for p, real in zip(proba, dataset.y_test):
        rec_list = recommend(p)
        lucky.update(rec_list)

        if real in rec_list:
            nb_correct += 1

    return nb_correct, lucky


def run_helper(classifier, dataset):
    if g_config.classifier not in g_config.random_classifiers:
        repetition = 1
    else:
        repetition = g_config.random_repetition

    nb_correct_sum = 0
    diversity_sum = 0.0

    for i in xrange(repetition):
        if i > 0:
            print("Repetition: %d/%d\n" % (i + 1, repetition))

        nb_correct, lucky = run(classifier, dataset)

        nb_correct_sum += nb_correct
        diversity_sum += len(lucky) / float(len(dataset.labels))

        if g_config.classifier == "MLP":
            print("\n")

    return nb_correct_sum / float(repetition), diversity_sum / repetition


def main():
    dataset = datasets.load_dataset(g_config.dataset,
                                    g_config.normalize_dataset)

    classifier = _create_classifier()
    nb_correct, diversity = run_helper(classifier, dataset)

    output_result(classifier=classifier,
                  nb_test=len(dataset.y_test),
                  nb_correct=nb_correct,
                  diversity=diversity)


if __name__ == "__main__":
    main()
