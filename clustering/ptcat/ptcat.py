
platech = {}
for index, line in enumerate(open("platech.txt").readlines()):
    platech[line[:line.index(':')]] = index

categories = open("result.txt").read().split(',')


def get_category(pt):
    if pt in platech:
        return categories[platech[pt]]


if __name__ == "__main__":
    assert get_category("Java") == "5"
    assert get_category("MySQL") == "10"
