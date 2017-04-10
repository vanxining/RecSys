#!/usr/bin/env python2
import importlib

import numpy as np

import config.classifiers as g_config
import datasets
import naive
from logger import Logger


class _Developer(naive.Developer):
    def __init__(self, uid, label, rating):
        super(_Developer, self).__init__(uid, rating)
        self.label = label


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


def update_ratings(developers):
    mappings = importlib.import_module("datasets.dev_mappings_" + g_config.dataset)

    for dev in developers:
        dev.uid = mappings.developers[dev.label]

    getattr(naive, g_config.dataset + "_rate")(developers)
    developers.sort(key=lambda d: d.rating, reverse=True)


def recommend(proba):
    developers = []
    for label, p in enumerate(proba):
        developers.append(_Developer(-1, label, p))

    developers.sort(key=lambda d: d.rating, reverse=True)

    nb_rec = min(g_config.topn, len(proba) / 2)

    if g_config.adjust_rec_list:
        nb_intact = g_config.rec_list_intact_length
        if nb_intact < nb_rec:
            nb_candidates = (nb_rec - nb_intact) * 2
            candidates = developers[nb_intact:(nb_intact + nb_candidates)]

            update_ratings(candidates)
            developers = developers[:nb_intact] + candidates

    return [dev.label for dev in developers[:nb_rec]]


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
                                    g_config.normalize_dataset())

    classifier = _create_classifier()
    nb_correct, diversity = run_helper(classifier, dataset)

    output_result(classifier=classifier,
                  nb_test=len(dataset.y_test),
                  nb_correct=nb_correct,
                  diversity=diversity)


if __name__ == "__main__":
    main()
