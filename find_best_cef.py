
import collab_filtering


def find_alpha():
    cf = collab_filtering.CF()
    cf.train()

    alpha = 0.0
    while alpha < 0.25:
        collab_filtering.run_all_tests(cf)
        cf.results.clear()

        alpha += 0.1

    accuracy_max = 0
    accuracy_max_cef = -1.0
    recall_max = 0
    recall_max_cef = -1.0
    diversity_max = 0
    diversity_max_cef = -1.0

    alpha = 0.0
    for test_round in cf.test_rounds:
        if accuracy_max < test_round.accuracy:
            accuracy_max = test_round.accuracy
            accuracy_max_cef = alpha

        if recall_max < test_round.recall:
            recall_max = test_round.recall
            recall_max_cef = alpha

        if diversity_max < test_round.diversity:
            diversity_max = test_round.diversity
            diversity_max_cef = alpha

        alpha += 0.1

    print ""
    print "Accuracy:", accuracy_max, accuracy_max_cef
    print "Recall rate:", recall_max, recall_max_cef
    print "Diversity:", diversity_max, diversity_max_cef


def main():
    find_alpha()


if __name__ == "__main__":
    main()
