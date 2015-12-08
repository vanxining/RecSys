
from pymongo import MongoClient
from datetime import datetime
from cf import cmp_datetime


client = MongoClient()
db = client.topcoder


def census(date_from, minute):
    condition = {
        u"postingDate": {
            u"$gte": date_from,
        }
    }

    num_ratios = 0
    ratio_sum = 0.0
    regs_sum = 0

    for challenge in db.challenges.find(condition):
        if u"registrants" not in challenge:
            continue

        d0 = challenge[u"postingDate"]
        count = 0

        regs = challenge[u"registrants"]
        if len(regs) == 0:
            continue

        regs.sort(cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                                y[u"registrationDate"]))

        for reg in regs:
            delta = (reg[u"registrationDate"] - d0).total_seconds()

            if delta <= minute * 60:
                count += 1

        num_ratios += 1
        ratio_sum += float(count) / len(regs)
        regs_sum += count

    if num_ratios > 0:
        return ratio_sum / num_ratios, int(round(regs_sum / num_ratios))
    else:
        return 0.0, 0


def main():
    date_from = datetime(2015, 1, 1)

    minute = 1
    coverage = 0.0

    # 1024 minutes = 17 hours
    # 4096 minutes = 2.85 days
    # 8192 minutes = 5.69 days

    # 1 minutes: 0.72% - 0
    # 2 minutes: 0.84% - 0
    # 4 minutes: 1.20% - 0
    # 8 minutes: 1.98% - 0
    # 16 minutes: 3.48% - 0
    # 32 minutes: 6.00% - 0
    # 64 minutes: 10.21% - 1
    # 128 minutes: 17.29% - 2
    # 256 minutes: 26.90% - 4
    # 512 minutes: 40.07% - 7
    # 1024 minutes: 57.74% - 10
    # 2048 minutes: 75.16% - 14
    # 4096 minutes: 89.52% - 18
    # 8192 minutes: 96.42% - 20

    while coverage < 0.9:
        coverage, regs_mean = census(date_from, minute)
        print "%d minutes: %.2f%% - %d" % (minute, coverage * 100, regs_mean)

        minute *= 2


if __name__ == "__main__":
    main()
