
from pymongo import MongoClient
from datetime import datetime
from gen_data import cmp_datetime


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

    for challenge in db.challenges.find(condition):
        if u"registrants" not in challenge:
            continue

        d0 = challenge[u"postingDate"]
        count = 0

        regs = challenge[u"registrants"]
        regs.sort(cmp=lambda x, y: cmp_datetime(x[u"registrationDate"],
                                                y[u"registrationDate"]))

        for reg in regs:
            delta = (reg[u"registrationDate"] - d0).total_seconds()

            if delta <= minute * 60:
                count += 1

        num_ratios += 1
        ratio_sum += float(count) / len(regs)

    return ratio_sum / num_ratios if num_ratios > 0 else 0.0


def main():
    date_from = datetime(2015, 1, 1)

    minute = 1
    coverage = 0.0

    # 1024 minutes = 17 hours
    # 4096 minutes = 2.85 days
    # 8192 minutes = 5.69 days

    # 1 minutes: 0.77%
    # 2 minutes: 0.89%
    # 4 minutes: 1.27%
    # 8 minutes: 2.09%
    # 16 minutes: 3.63%
    # 32 minutes: 6.14%
    # 64 minutes: 10.46%
    # 128 minutes: 17.60%
    # 256 minutes: 27.31%
    # 512 minutes: 40.55%
    # 1024 minutes: 58.21%
    # 2048 minutes: 75.62%
    # 4096 minutes: 89.75%
    # 8192 minutes: 96.50%

    while coverage < 0.9:
        coverage = census(date_from, minute)
        print "%d minutes: %.2f%%" % (minute, coverage * 100)

        minute *= 2


if __name__ == "__main__":
    main()
