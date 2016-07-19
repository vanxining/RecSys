#!/usr/bin/env python2

from StringIO import StringIO
from myconfig import get_current_timestamp

import datasets
import config.classifiers as g_config


def _create_classifier():
    if g_config.classifier == "NB":
        from sklearn.naive_bayes import GaussianNB
        return GaussianNB()

    if g_config.classifier == "LR":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression()

    if g_config.classifier == "MLP":
        from mlp import MLP
        return MLP()


def recommend(proba):
    pairs = []
    for index, p in enumerate(proba):
        pairs.append((index, p))

    pairs.sort(key=lambda pair: pair[1], reverse=True)

    rec = []
    for i in xrange(min(g_config.topn, len(proba) / 2)):
        rec.append(pairs[i][0])

    return rec


def output_result(classifier, nb_test, nb_correct):
    sio = StringIO()

    sio.write(str(type(classifier)) + "\n")
    sio.write(g_config.raw.strip() + "\n")
    sio.write("----------\n")
    sio.write("# Correct: %d\n" % nb_correct)
    sio.write("%g%%" % (float(nb_correct) / nb_test * 100))

    print(sio.getvalue())

    ts = get_current_timestamp()
    fpath = "results/%s-classifiers-%s.log" % (ts, g_config.classifier)
    with open(fpath, "w") as outf:
        outf.write(sio.getvalue())


def run(classifier, dataset):
    classifier.fit(dataset.X_train, dataset.y_train)
    proba = classifier.predict_proba(dataset.X_test)

    nb_correct = 0

    for p, real in zip(proba, dataset.y_test):
        rec_list = recommend(p)

        if real in rec_list:
            nb_correct += 1

    output_result(classifier, len(dataset.y_test), nb_correct)


def main():
    dataset = datasets.topcoder(normalize=g_config.normalize_dataset)
    run(_create_classifier(), dataset)


if __name__ == "__main__":
    main()
