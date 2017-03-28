def topcoder_is_ok(challenge):
    if u"registrants" not in challenge:
        return False

    if len(challenge[u"registrants"]) == 0:
        return False

    return challenge[u"type"] == u"develop" and len(challenge[u"prize"]) > 0


def topcoder_get_winner(challenge):
    if u"finalSubmissions" in challenge:
        for submission in challenge[u"finalSubmissions"]:
            if submission[u"placement"] == 1:
                if submission[u"submissionStatus"] == u"Active":
                    handle = submission[u"handle"]
                    if handle != u"Applications":
                        return handle

    return None
