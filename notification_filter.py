SEND_THRESHOLD = 75


def should_notify(result):
    """
    Decide whether an email should trigger a notification.
    """

    important = result.get("important", False)
    score = result.get("importance_score", 0)

    if important and score >= SEND_THRESHOLD:
        return True

    return False