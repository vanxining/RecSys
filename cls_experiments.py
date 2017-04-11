#!/usr/bin/env python2

from collections import namedtuple

import classifiers
import config.classifiers as g_config


datasets = ("topcoder", "freelancer",)
klassifiers = ("NB", "DTG", "DTE", "LR", "MLP",)
topN = (5, 10, 15, 20, 30,)

Result = namedtuple("Result", ("accuracy", "diversity",))

results = {}


def collect_results(classifier, nb_test, nb_correct, diversity):
    results[g_config.dataset][g_config.classifier][g_config.topn] = Result(
        accuracy=float(nb_correct) / nb_test * 100.0,
        diversity=diversity * 100.0,
    )


def run(dataset, cls, topn):
    g_config.dataset = dataset
    g_config.classifier = cls
    g_config.topn = topn

    classifiers.main()


def output():
    for dataset in datasets:
        print "\n%s:\n" % dataset

        for f in Result._fields:
            for topn in topN:
                for cls in klassifiers:
                    print "%.2f%%\t" % getattr(results[dataset][cls][topn], f),

                print ""


def main():
    classifiers.output_result = collect_results

    for dataset in datasets:
        results[dataset] = {}

        for cls in klassifiers:
            results[dataset][cls] = {}

            for topn in topN:
                run(dataset, cls, topn)

    output()


if __name__ == "__main__":
    main()
