#!/usr/bin/env python2

from collections import namedtuple

import naive
import config.naive as g_config


datasets = ("topcoder", "freelancer",)
topN = (1, 2, 3, 4, 5,)
order_factors = (0.0, 0.1, 0.2, 0.3,)

Result = namedtuple("Result", ("accuracy",))

results = {}


def collect_results(nb_correct, nb_projects):
    result = Result(accuracy=float(nb_correct) / nb_projects * 100.0)
    results[g_config.dataset][g_config.topn][g_config.order_factor] = result


def run(dataset, topn, order_factor):
    g_config.dataset = dataset
    g_config.topn = topn
    g_config.order_factor = order_factor

    naive.main()


def output():
    for dataset in datasets:
        print "\n%s:\n" % dataset

        for topn in topN:
            for order_factor in order_factors:
                for f in Result._fields:
                    print "%.2f%%\t" % getattr(results[dataset][topn][order_factor], f),

            print ""


def main():
    naive.output_result = collect_results

    for dataset in datasets:
        results[dataset] = {}

        for topn in topN:
            results[dataset][topn] = {}

            for order_factor in order_factors:
                run(dataset, topn, order_factor)

    output()


if __name__ == "__main__":
    main()
