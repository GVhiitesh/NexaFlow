def pre_filter_email(sender, subject, body):
    """
    Returns:
        "skip"    -> Don't send to Gemini
        "analyze" -> Send to Gemini
    """

    sender = sender.lower()
    subject = subject.lower()
    body = body.lower()

    text = f"{sender} {subject} {body}"

    # ======================================================
    # ALWAYS IMPORTANT
    # ======================================================

    important_keywords = [

        # Career
        "internship",
        "intern ",
        "placement",
        "pre-placement",
        "ppi",
        "job",
        "job opportunity",
        "hiring",
        "software engineer",
        "offer letter",
        "interview",
        "assessment",
        "coding challenge",

        # Competitions
        "hackathon",
        "competition",
        "contest",

        # College
        "exam",
        "assignment",
        "deadline",
        "registration",
        "semester",
        "academic",

        # Security
        "security alert",
        "login attempt",
        "password",
        "otp",
        "verify account",

        # Banking
        "bank",
        "transaction",

        # GitHub
        "github",
        "repository",
        "organization invitation",

        # Scholarships
        "scholarship"
    ]

    for keyword in important_keywords:
        if keyword in text:
            return "analyze"

    # ======================================================
    # ALWAYS SKIP SENDERS
    # ======================================================

    low_value_senders = [

        "redditmail.com",
        "spotify.com",
        "mail.apollo.io"
    ]

    for domain in low_value_senders:
        if domain in sender:
            return "skip"

    # ======================================================
    # LINKEDIN
    # ======================================================

    linkedin_skip = [

        "people you may know",
        "accepted your invitation",
        "new invitations",
        "add connection",
        "new skill available",
        "grow your network",
        "recommended for you",
        "suggested for you"
    ]

    for keyword in linkedin_skip:
        if keyword in subject:
            return "skip"

    # ======================================================
    # PROMOTIONS
    # ======================================================

    promotion_keywords = [

        "sale",
        "discount",
        "offer ends",
        "buy now",
        "coupon",
        "limited time",
        "free shipping",
        "deal",
        "concert",
        "playlist",
        "top stories",
        "daily digest",
        "weekly digest",
        "newsletter"
    ]

    for keyword in promotion_keywords:
        if keyword in subject:
            return "skip"

    # ======================================================
    # DEFAULT
    # ======================================================

    return "analyze"