#!/usr/bin/env python2

from collections import defaultdict
import sqlite3

import config.data_freelancer as data_config
import logger


ID = 0
TYPE = 1
SUBMIT_DATE = 2
BUDGET_MIN = 3
BUDGET_MAX = 4
TECHNOLOGIES = 5
DEVELOPERS = 6
WINNER = 7


class Data(object):
    def __init__(self):
        self.logger = logger.Logger()

        self.con = sqlite3.connect("datasets/freelancer.sqlite")
        self.cursor = self.con.cursor()

        self.technologies = {}
        self.winners = {}

    def extract_training_set(self):
        query = '''SELECT * FROM "projects"
                   WHERE "submit_date" >= %d AND "submit_date" < %d
                   ORDER BY "submit_date" DESC LIMIT %d''' % (
            data_config.training_set_begin_date,
            data_config.training_set_end_date,
            data_config.training_set_limit,
        )

        win_times = defaultdict(int)

        self.cursor.execute(query)
        for index, project in enumerate(self.cursor.fetchall()):
            if (index + 1) % 100 == 0:
                print "Training set #1 counter:", index + 1

            win_times[project[WINNER]] += 1

        for winner, times in win_times.iteritems():
            if times >= data_config.win_times_threshold:
                if winner not in self.winners:
                    self.winners[winner] = len(self.winners)

        self.cursor.execute(query)
        for index, project in enumerate(self.cursor.fetchall()):
            if (index + 1) % 100 == 0:
                print "Training set #2 counter:", index + 1

            if project[WINNER] not in self.winners:
                continue

            for tech in project[TECHNOLOGIES].split(' '):
                t = int(tech)
                if t not in self.technologies:
                    self.technologies[t] = len(self.technologies)

        self.cursor.execute(query)
        count = self._save("training", self.cursor.fetchall())

        self.logger.log("# technologies: %d" % len(self.technologies))
        self.logger.log("Max win times: %d" % max(win_times.values()))
        self.logger.log("Training set size: %d" % count)

    def extract_test_set(self):
        query = '''SELECT * FROM "projects"
                   WHERE "submit_date" >= %d
                   ORDER BY "submit_date" LIMIT %d''' % (
            data_config.training_set_end_date,
            data_config.test_set_limit,
        )

        projects = []

        self.cursor.execute(query)
        for index, project in enumerate(self.cursor.fetchall()):
            if (index + 1) % 100 == 0:
                print "Test set counter:", index + 1

            if project[WINNER] not in self.winners:
                continue

            new_tech = False

            for tech in project[TECHNOLOGIES].split(' '):
                if int(tech) not in self.technologies:
                    new_tech = True
                    break

            if new_tech:
                continue

            projects.append(project)

        self._save("test", projects)

        self.logger.log("Test set size: %d" % len(projects))

    def _save(self, fname, iterable):
        ts = set()
        count = 0

        with open("datasets/%s_freelancer.txt" % fname, "w") as outf:
            def append(value, delim=' '):
                outf.write(str(value) + delim)

            for index, project in enumerate(iterable):
                if (index + 1) % 100 == 0:
                    print "Output %s set counter:" % fname, index + 1

                winner = project[WINNER]
                if winner not in self.winners:
                    continue

                append(project[TYPE])
                append(project[BUDGET_MIN])
                append(project[BUDGET_MAX])

                for tech in project[TECHNOLOGIES].split(' '):
                    ts.add(self.technologies[int(tech)])

                for i in xrange(len(self.technologies)):
                    append(1 if i in ts else 0)

                append(self.winners[winner], delim='\n')

                ts.clear()
                count += 1

        return count

    def _save_developer_mappings(self):
        with open("datasets/dev_mappings_freelancer.py", 'w') as outf:
            outf.write("devs = (\n")

            mappings = [0] * len(self.winners)

            for dev, nindex in self.winners.iteritems():
                mappings[nindex] = dev

            for dev in mappings:
                outf.write("    %d,\n" % dev)

            outf.write(")\n")

    def generate(self):
        self.logger.log(data_config.raw)
        self.logger.log("----------")

        self.extract_training_set()
        self.extract_test_set()

        self._save_developer_mappings()

        self.logger.save("freelancer-dataset")


if __name__ == "__main__":
    data = Data()
    data.generate()
