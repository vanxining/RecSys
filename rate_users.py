#!/usr/bin/env python2

from math import log
import sqlite3

import pymongo


mclient = pymongo.MongoClient()
mdb = mclient.freelancer

SDB_FILE = "datasets/freelancer.sqlite"
scon = sqlite3.connect(SDB_FILE)
sc = scon.cursor()

EXISTS_QUERY = 'SELECT id FROM "projects" WHERE "id"=?'
INS_QUERY = '''INSERT INTO "dev_ratings" ("uid","rating") VALUES (?,?)'''


def init_db():
    scon.executescript(open("config/init_sdb.sql").read())


def _log(num):
    return log(num) if num > 0 else 0.0


class User(object):

    IGNORE_FIELDS = ("id", "rating",)

    def __init__(self, doc):
        self.id = doc["id"]

        self.rating_count = _log(doc["rating"]["count"])
        self.rating_avg = float(doc["rating"]["avg"])
        self.reputation_rate = float(doc["reputation_rate"])

        # The developer rates the project or requester?
        # self.seller_rating_count = _log(doc["seller_rating"]["count"])

        self.rating = 0.0


def detect_fields(users):
    fields = []

    for user in users.itervalues():
        for key in vars(user):
            if key not in User.IGNORE_FIELDS:
                fields.append(key)

        break

    return fields


def normalize(users, fields):
    field_min_values = [100000000.0] * len(fields)
    field_max_values = [0.0] * len(fields)

    for i, field in enumerate(fields):
        for user in users.itervalues():
            value = getattr(user, field)

            if field_min_values[i] > value:
                field_min_values[i] = value

            if field_max_values[i] < value:
                field_max_values[i] = value

    for i, field in enumerate(fields):
        nmax = field_max_values[i] - field_min_values[i]

        for user in users.itervalues():
            if nmax > 0.0:
                value = getattr(user, field)
                nv = (value - field_min_values[i]) / nmax
            else:
                nv = 0.0

            setattr(user, field, nv)


def rate_users():
    users = {}

    for index, project in enumerate(mdb.projects.find()):
        if (index + 1) % 100 == 0:
            print "Counter:", index + 1

        if not "result" in project or not "bids" in project["result"]:
            continue

        for bid in project["result"]["bids"]:
            user_doc = bid["user"]
            uid = user_doc["id"]
            if uid not in users:
                try:
                    users[uid] = User(user_doc)
                except TypeError:
                    pass

    fields = detect_fields(users)

    # Normalize fields
    normalize(users, fields)

    # Add up the normalized fields
    for user in users.itervalues():
        for field in fields:
            user.rating += getattr(user, field)

    return users


def save_to_db(users):
    init_db()

    for user in users.itervalues():
        sc.execute(INS_QUERY, (user.id, user.rating,))

    scon.commit()
    scon.close()


def main():
    users = rate_users()
    save_to_db(users)

    for index, user in enumerate(users.itervalues()):
        print vars(user)

        if index == 50:
            break

    print "Count:", len(users)


if __name__ == "__main__":
    main()
