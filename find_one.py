#!/usr/bin/env python2

import argparse

from bson import json_util
import pymongo


client = pymongo.MongoClient()


def topcoder():
    db = client.topcoder
    row = db.challenges.find_one()

    return json_util.dumps(row)


def topcoder_user():
    db = client.topcoder
    row = db.users.find_one({"handle": "vvvpig"})

    return json_util.dumps(row)


def freelancer():
    db = client.freelancer
    row = db.projects.find_one({"result.bids": {"$size": 10}})

    return json_util.dumps(row)


def main():
    parser = argparse.ArgumentParser("find_one")
    parser.add_argument("dataset",
                        choices=("topcoder", "topcoder_user", "freelancer"),
                        help="the dataset to extract")

    args = parser.parse_args()
    print(globals()[args.dataset]())


if __name__ == "__main__":
    main()
