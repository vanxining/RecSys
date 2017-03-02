#!/usr/bin/env python2

from collections import defaultdict
import sqlite3


count = defaultdict(int)

SDB_FILE = "datasets/freelancer.sqlite"
scon = sqlite3.connect(SDB_FILE)
sc = scon.cursor()

query = "SELECT technologies FROM projects"

for row in sc.execute(query):
    technologies = row[0].strip().split(' ')

    for tech in technologies:
        count[int(tech)] += 1

technologies = count.keys()
technologies.sort(key=lambda tech_index: count[tech_index], reverse=True)

for tech in technologies:
    print("%d\t%d" % (tech, count[tech]))
