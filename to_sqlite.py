#!/usr/bin/env python2

import sqlite3
from collections import namedtuple

import pymongo


mclient = pymongo.MongoClient()
mdb = mclient.freelancer

SDB_FILE = "datasets/freelancer.sqlite"
scon = sqlite3.connect(SDB_FILE)
sc = scon.cursor()

EXISTS_QUERY = 'SELECT id FROM "projects" WHERE "id"=?'
INS_QUERY = '''INSERT INTO "projects"
("id","type","submit_date","budget_min","budget_max","technologies","developers","winner")
VALUES (?,?,?,?,?,?,?,?)'''


def init_db():
    scon.executescript(open("config/fl_projects.sql").read())


def project_exists(pid):
    sc.execute(EXISTS_QUERY, (pid,))
    return sc.fetchone() is not None


Bid = namedtuple("Bid", ("dev", "date",))


def to_sqlite3():
    num_inserted = 0

    for index, project in enumerate(mdb.projects.find()):
        if (index + 1) % 100 == 0:
            print "Counter:", index + 1

        if "result" in project and "bids" in project["result"]:
            if len(project["jobs"]) == 0:
                continue

            if len(project["result"]["bids"]) == 0:
                continue

            if "minimum" not in project["budget"]:
                continue

            pid = project["id"]

            if project_exists(pid):
                continue

            technologies = ""
            for tech in project["jobs"]:
                technologies += str(tech["id"]) + ' '

            bids = []
            winner = -1

            for bid in project["result"]["bids"]:
                bids.append(Bid(str(bid["users_id"]), int(bid["submitdate_ts"])))

                if "is_awarded" in bid and bid["is_awarded"]:
                    winner = bids[-1].dev

            bids.sort(key=lambda b: b.date)

            developers = ""
            for bid in bids:
                developers += bid.dev + ' '

            if winner != -1:
                bmin = project["budget"]["minimum"]
                bmax = bmin
                if "maximum" in project["budget"]:
                    bmax = project["budget"]["maximum"]

                scon.execute(INS_QUERY, (
                    pid,
                    0 if project["type"] == "fixed" else 1,
                    project["submitdate"],
                    bmin,
                    bmax,
                    technologies[:-1],
                    developers[:-1],
                    winner,
                ))

                num_inserted += 1

    scon.commit()
    scon.close()

    print "# inserted:", num_inserted


def main():
    init_db()
    to_sqlite3()


if __name__ == "__main__":
    main()
