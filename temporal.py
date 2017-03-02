from datetime import datetime

import pymongo

from collab_filtering import cmp_datetime


client = pymongo.MongoClient()
db = client.topcoder


def census(date_from, minute):
    num_ratios = 0
    ratio_sum = 0.0
    regs_sum = 0

    condition = {
        u"postingDate": {
            u"$gte": date_from,
        }
    }

    for challenge in db.challenges.find(condition):
        if u"registrants" not in challenge:
            continue

        regs = challenge[u"registrants"]
        if len(regs) == 0:
            continue

        regs.sort(cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                                y[u"registrationDate"]))

        d0 = challenge[u"postingDate"]
        count = 0

        for reg in regs:
            delta = (reg[u"registrationDate"] - d0).total_seconds()

            if delta <= minute * 60:
                count += 1

        num_ratios += 1
        ratio_sum += float(count) / len(regs)
        regs_sum += count

    if num_ratios > 0:
        return ratio_sum / num_ratios, float(regs_sum) / num_ratios
    else:
        return 0.0, 0.0


def print_all_dates(date_from):
    condition = {
        u"postingDate": {
            u"$gte": date_from,
        }
    }

    sorter = (u"postingDate", pymongo.DESCENDING)

    for challenge in db.challenges.find(condition).sort(*sorter):
        print challenge[u"postingDate"]


def main():
    date_from = datetime(2015, 1, 1)

    minute = 1
    coverage = 0.0

    # 1024 minutes = 17 hours
    # 4096 minutes = 2.85 days
    # 8192 minutes = 5.69 days

    # 1 minutes: 0.70% - 0.1
    # 2 minutes: 0.83% - 0.1
    # 4 minutes: 1.20% - 0.2
    # 8 minutes: 1.95% - 0.3
    # 16 minutes: 3.43% - 0.5
    # 32 minutes: 5.97% - 0.9
    # 64 minutes: 10.13% - 1.7
    # 128 minutes: 17.06% - 3.0
    # 256 minutes: 26.60% - 4.8
    # 512 minutes: 39.72% - 7.5
    # 1024 minutes: 57.48% - 11.3
    # 2048 minutes: 74.96% - 15.5
    # 4096 minutes: 89.30% - 19.3
    # 8192 minutes: 96.29% - 21.7

    while coverage < 0.9:
        coverage, regs_mean = census(date_from, minute)
        print "%d minutes: %.2f%% - %.1f" % (minute, coverage * 100, regs_mean)

        minute *= 2


if __name__ == "__main__":
    main()
