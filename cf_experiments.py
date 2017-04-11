#!/usr/bin/env python2

from collections import namedtuple

import cf
import config.cf as g_config


datasets = ("topcoder", "freelancer",)
sim_funcs = ("Naive", "Cosine", "Breese",
             "Neighbor", "Neighbor2", "NeighborGlobal",
             "Active",)

Result = namedtuple("Result", ("accuracy", "recall", "f1", "diversity",))

results = {}


def collect_results(_, session):
    nb_test_cases = 0
    accuracy_sums = [0.0] * len(session.test_rounds)
    recall_sums = list(accuracy_sums)
    f1_sums = list(accuracy_sums)

    for rs in session.results.itervalues():
        assert len(rs) == len(session.test_rounds)

        nb_test_cases += 1
        for i, result in enumerate(rs):
            accuracy_sums[i] += result.accuracy
            recall_sums[i] += result.recall
            f1_sums[i] += result.f1

    results[g_config.dataset][g_config.sim_func] = {}

    for i, nb_seeds in enumerate(g_config.nb_seeds):
        results[g_config.dataset][g_config.sim_func][nb_seeds] = Result(
            accuracy=accuracy_sums[i] / nb_test_cases * 100.0,
            recall=recall_sums[i] / nb_test_cases * 100.0,
            f1=f1_sums[i] / nb_test_cases,
            diversity=session.test_rounds[i].diversity * 100.0,
        )


def output_results():
    for dataset in datasets:
        print "\n%s:\n" % dataset

        for f in Result._fields:
            for nb_seeds in g_config.nb_seeds:
                for sim_func in sim_funcs:
                    result = results[dataset][sim_func][nb_seeds]
                    val = getattr(result, f)

                    if f != "f1":
                        print "%.2f%%" % val,
                    else:
                        print "%.2f" % val,

                # Every nb_seeds has its own line
                print ""


def main():
    cf.output_result = collect_results

    for dataset in datasets:
        g_config.dataset = dataset
        results[dataset] = {}

        for sim_func in sim_funcs:
            g_config.sim_func = sim_func

            cf.main()

    output_results()


if __name__ == "__main__":
    main()
