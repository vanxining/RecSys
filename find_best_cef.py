
import sys
import os
import ConfigParser

import collab_filtering
import sim


coefficients = ("alpha", "beta", "gamma",)


def load_config():
    config = ConfigParser.RawConfigParser()
    config.read("config/find_best_cef.ini")

    for cef in coefficients:
        val = config.getfloat("default", cef)
        if val > 0:
            sim.SetCoefficient(cef, val)


def find_best_coefficient(cef_name):
    cf = collab_filtering.CF()
    cf.train()

    nul = open(os.devnull, "w")
    stdout = sys.stdout
    sys.stdout = nul

    increment = 0.05

    coefficient = increment
    while coefficient < 1.02:
        sim.SetCoefficient(cef_name, coefficient)

        collab_filtering.run_all_tests(cf, first_hour=False)
        cf.results.clear()
        sim.ClearCache()

        stdout.write("%s = %.2f\n" % (cef_name, coefficient))
        stdout.write(repr(cf.test_rounds[-1]))
        stdout.write("\n-------\n")

        coefficient += increment

    sys.stdout = stdout

    accuracy_max = 0.0
    accuracy_max_cef = -1.0
    recall_max = 0.0
    recall_max_cef = -1.0
    diversity_max = 0.0
    diversity_max_cef = -1.0

    coefficient = increment
    for test_round in cf.test_rounds:
        if accuracy_max < test_round.accuracy:
            accuracy_max = test_round.accuracy
            accuracy_max_cef = coefficient

        if recall_max < test_round.recall:
            recall_max = test_round.recall
            recall_max_cef = coefficient

        if diversity_max < test_round.diversity:
            diversity_max = test_round.diversity
            diversity_max_cef = coefficient

        coefficient += increment

    print ""
    print "Accuracy:", accuracy_max, accuracy_max_cef
    print "Recall rate:", recall_max, recall_max_cef
    print "Diversity:", diversity_max, diversity_max_cef


def main():
    assert len(sys.argv) > 1
    assert sys.argv[1] in coefficients

    load_config()
    find_best_coefficient(sys.argv[1])


if __name__ == "__main__":
    main()
