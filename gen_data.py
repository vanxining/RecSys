
from datetime import datetime
from pymongo import MongoClient

import numpy as np


client = MongoClient()
db = client.topcoder


def challenges(year_from):
    condition = {u"postingDate": {u"$gt": datetime(year_from, 1, 1)}}
    for challenge in db.challenges.find(condition):
        if u"registrants" not in challenge:
            continue

        yield challenge


def main(win_times, year_from):
    num_challenges = 0

    users = {}
    user_index = 0

    for challenge in challenges(year_from):
        num_challenges += 1

        for reg in challenge[u"registrants"]:
            handle = reg[u"handle"].lower()

            if handle not in users:
                users[handle] = user_index
                user_index += 1

    A = np.zeros((num_challenges, user_index + 1), dtype=np.int8)

    for challenge_index, challenge in enumerate(challenges(year_from)):
        for reg in challenge[u"registrants"]:
            handle = reg[u"handle"].lower()

            user_index = users[handle]
            A[challenge_index, user_index] = 1

    A = np.transpose(A)
    print A.shape, A.dtype

    print np.count_nonzero(A[123])

    S = np.zeros((A.shape[0], A.shape[0]), np.int8)

    R = 456

    for i in range(S.shape[0]):
        S[R, i] = np.count_nonzero(np.bitwise_and(A[R], A[i]))

    print np.count_nonzero(S[R])


if __name__ == '__main__':
    main(win_times=5, year_from=2014)
