#!/usr/bin/env python2

import datasets
from sklearn.naive_bayes import GaussianNB


TopN = 30


def recommend(proba, n):
    pairs = []
    for index, p in enumerate(proba):
        pairs.append((index, p))

    pairs.sort(key=lambda pair: pair[1], reverse=True)

    rec = []
    for i in xrange(n):
        rec.append(pairs[i][0])

    return rec


def output_result(classifier, nb_test, nb_correct):
    print type(classifier)
    print "# Correct:", nb_correct
    print "%g%%" % (float(nb_correct) / nb_test * 100)


def run(classifier, dataset):
    classifier.fit(dataset.X_train, dataset.y_train)
    proba = classifier.predict_proba(dataset.X_test)

    nb_correct = 0

    for p, real in zip(proba, dataset.y_test):
        rec_list = recommend(p, TopN)

        if real in rec_list:
            nb_correct += 1

    output_result(classifier, len(dataset.y_test), nb_correct)


def main():
    dataset = datasets.topcoder(normalize=False)
    gnb = GaussianNB()

    run(gnb, dataset)


if __name__ == "__main__":
    main()
