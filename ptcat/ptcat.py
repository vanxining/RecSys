#!/usr/bin/env python2

import os


def _get_path(fname):
    if os.path.exists(fname):
        return fname

    fname = os.path.abspath(os.path.dirname(__file__) + os.sep + fname)
    assert os.path.exists(fname)

    return fname


platech = {}
for index, line in enumerate(open(_get_path("platech.txt"))):
    platech[line[:line.index(':')]] = index

categories = [int(n.strip()) for n in open(_get_path("result.txt"))]


def get_category(pt, categorize):
    raw_index = platech[pt]
    return categories[raw_index] if categorize else raw_index


def get_number_of_platech(categorize):
    return max(categories) if categorize else len(platech)


def _test():
    assert get_number_of_platech(categorize=True) == 11
    assert get_category("Java", categorize=True) == 5
    assert get_category("MySQL", categorize=True) == 10
    assert get_category("Predix", categorize=True) == 4
    assert get_category("Web Application", categorize=True) == 1


if __name__ == "__main__":
    _test()
