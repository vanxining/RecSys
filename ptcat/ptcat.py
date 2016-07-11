
import os


def _get_path(fname):
    return os.path.abspath(os.path.dirname(__file__) + os.sep + fname)


platech = {}
for index, line in enumerate(open(_get_path("platech.txt")).readlines()):
    platech[line[:line.index(':')]] = index

categories = [int(n) for n in open(_get_path("result.txt")).read().split(',')]


def get_category(pt):
    if pt in platech:
        return categories[platech[pt]]


def get_number_of_platech():
    return max(categories)


if __name__ == "__main__":
    assert get_number_of_platech() == 11
    assert get_category("Java") == 5
    assert get_category("MySQL") == 10
