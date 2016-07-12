#!/usr/bin/env python2

import ConfigParser
from StringIO import StringIO
from datetime import datetime

from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression

import datasets


class Config:
    def __init__(self):
        config = ConfigParser.RawConfigParser()

        fname = "config/classifiers.ini"
        with open(fname, "r") as inf:
            self.raw = inf.read()
            inf.seek(0)
            config.readfp(inf, fname)

        self.topn = config.getint("default", "topn")
        self.normalize_dataset = config.getboolean("default",
                                                   "normalize_dataset")
        self.classifier = config.get("default", "classifier")

    def create_classifier(self):
        if self.classifier == "NB":
            return GaussianNB()

        if self.classifier == "LR":
            return LogisticRegression()


g_config = Config()


def recommend(proba):
    pairs = []
    for index, p in enumerate(proba):
        pairs.append((index, p))

    pairs.sort(key=lambda pair: pair[1], reverse=True)

    rec = []
    for i in xrange(g_config.topn):
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

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    with open("results/%s-classifiers-%s.txt" % (ts, g_config.classifier),
              "w") as outf:
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
    run(g_config.create_classifier(), dataset)


if __name__ == "__main__":
    main()
