import time
from pre_filter import pre_filter_email
from gmail_service import get_latest_emails
from email_classifier import classify_email
from notification_filter import should_notify
from whatsapp_sender import send_whatsapp_message
from processed_emails import is_processed, save_processed_email
from email_cleaner import clean_email_body


# ============================================================
# SETTINGS
# ============================================================

# Keep this low while developing to protect Gemini quota
MAX_EMAILS_PER_RUN = 2

# Delay between successful Gemini requests
AI_DELAY_SECONDS = 15

# Normal Gmail checking interval: 5 minutes
CHECK_INTERVAL = 300

# Wait after Gemini 429 / 503: 10 minutes
AI_ERROR_WAIT = 600

# Number of recent Gmail messages to inspect
GMAIL_FETCH_LIMIT = 5


# ============================================================
# DETECT TEMPORARY GEMINI ERRORS
# ============================================================

def is_temporary_ai_error(error):
    """
    Returns True for errors where we should STOP the current
    processing cycle instead of trying more emails.

    Examples:
    - 429 quota/rate limit
    - 503 model overloaded/unavailable
    """

    error_text = str(error).lower()

    keywords = [
        # 429 / quota errors
        "429",
        "resource_exhausted",
        "quota",
        "rate limit",
        "rate-limit",
        "too many requests",

        # 503 / overloaded errors
        "503",
        "unavailable",
        "high demand",
        "temporarily unavailable",
        "service unavailable"
    ]

    return any(
        keyword in error_text
        for keyword in keywords
    )


# ============================================================
# RUN ONE INBOXIQ CYCLE
# ============================================================

def run_inboxiq():

    print("\n" + "=" * 60)
    print("🚀 InboxIQ starting...")
    print("=" * 60)

    # --------------------------------------------------------
    # GET EMAILS
    # --------------------------------------------------------

    try:

        emails = get_latest_emails(
            limit=GMAIL_FETCH_LIMIT
        )

    except Exception as e:

        print("\n❌ Gmail error:")
        print(e)

        return "gmail_error"


    print(
        f"\n📧 Found {len(emails)} recent emails."
    )


    processed_count = 0


    # ========================================================
    # PROCESS EMAILS
    # ========================================================

    for email in emails:

        email_id = email["id"]


        # ----------------------------------------------------
        # DUPLICATE PROTECTION
        # ----------------------------------------------------

        if is_processed(email_id):

            print(
                f"⏭️ Skipping: {email['subject']}"
            )

            continue


        print("\n" + "=" * 60)

        print(
            f"📧 {email['subject']}"
        )

        print(
            f"From: {email['sender']}"
        )


        # ----------------------------------------------------
        # CLEAN EMAIL BODY
        # ----------------------------------------------------

        try:

            clean_body = clean_email_body(
                email.get("body", "")
            )
            

        except Exception as e:

            print(
                f"⚠️ Email cleaning failed: {e}"
            )

            # Fall back to original body
            clean_body = email.get(
                "body",
                ""
            )


        # Limit amount of text sent to Gemini
        clean_body = clean_body[:3000]

        # --------------------------------------------
        # PRE-FILTER
        # --------------------------------------------

        decision = pre_filter_email(
            email["sender"],
            email["subject"],
            clean_body
        )

        if decision == "skip":

            print("\n⚡ Skipped by pre-filter")

            save_processed_email(email_id)

            print("✅ Email marked as processed.")

            continue

        print("🤖 Sent to Gemini")


        # ----------------------------------------------------
        # GEMINI AI CLASSIFICATION
        # ----------------------------------------------------

        print("\n🤖 Analyzing...")


        try:

            result = classify_email(
                email["sender"],
                email["subject"],
                clean_body
            )


        except Exception as e:

            # =================================================
            # 429 OR 503
            # =================================================

            if is_temporary_ai_error(e):

                print(
                    "\n⚠️ GEMINI TEMPORARILY UNAVAILABLE"
                )

                print(
                    "429 quota limit or "
                    "503 server overload detected."
                )

                print(
                    "🛑 Stopping this processing cycle."
                )

                print(
                    "📧 Current email NOT marked as processed."
                )

                print(
                    "🔄 It will be retried later."
                )

                return "ai_unavailable"


            # =================================================
            # OTHER AI ERROR
            # =================================================

            print(
                "\n❌ AI classification failed:"
            )

            print(e)

            print(
                "📧 Email NOT marked as processed."
            )

            print(
                "🔄 It can be retried later."
            )

            # Don't mark it processed
            continue


        # ----------------------------------------------------
        # VALIDATE GEMINI RESULT
        # ----------------------------------------------------

        if not isinstance(result, dict):

            print(
                "\n❌ Invalid response from AI."
            )

            print(
                "📧 Email NOT marked as processed."
            )

            continue


        # ----------------------------------------------------
        # DISPLAY AI RESULT
        # ----------------------------------------------------

        print("\n--- InboxIQ Result ---")

        print(
            "Important:",
            result.get("important")
        )

        print(
            "Score:",
            result.get("importance_score")
        )

        print(
            "Category:",
            result.get("category")
        )

        print(
            "Summary:",
            result.get("summary")
        )

        print(
            "Action Required:",
            result.get("action_required")
        )

        print(
            "Action:",
            result.get("action")
        )

        print(
            "Deadline:",
            result.get("deadline")
        )


        # ====================================================
        # NOTIFICATION DECISION
        # ====================================================

        try:

            notification_required = should_notify(
                result
            )

        except Exception as e:

            print(
                "\n❌ Notification filter error:"
            )

            print(e)

            print(
                "📧 Email NOT marked as processed."
            )

            continue


        # ====================================================
        # IMPORTANT EMAIL
        # ====================================================

        if notification_required:

            print(
                "\n🚨 WHATSAPP NOTIFICATION REQUIRED"
            )


            whatsapp_message = f"""🚨 InboxIQ Alert

📧 {email['subject']}

From:
{email['sender']}

Summary:
{result.get('summary') or 'No summary available'}

Importance:
{result.get('importance_score', 0)}/100

Category:
{result.get('category') or 'Unknown'}

Action:
{result.get('action') or 'No specific action'}

Deadline:
{result.get('deadline') or 'None'}
"""


            # ------------------------------------------------
            # SEND WHATSAPP
            # ------------------------------------------------

            print(
                "\n📱 Sending WhatsApp..."
            )


            try:

                success = send_whatsapp_message(
                    whatsapp_message
                )

            except Exception as e:

                print(
                    "\n❌ WhatsApp error:"
                )

                print(e)

                success = False


            # ------------------------------------------------
            # WHATSAPP SUCCESS
            # ------------------------------------------------

            if success:

                print(
                    "✅ WhatsApp notification sent."
                )

                try:

                    save_processed_email(
                        email_id
                    )

                    print(
                        "✅ Email marked as processed."
                    )

                except Exception as e:

                    print(
                        "⚠️ Could not save processed ID:"
                    )

                    print(e)


            # ------------------------------------------------
            # WHATSAPP FAILURE
            # ------------------------------------------------

            else:

                print(
                    "❌ WhatsApp notification failed."
                )

                print(
                    "📧 Email NOT marked as processed."
                )

                print(
                    "🔄 It will be retried later."
                )


        # ====================================================
        # NOT IMPORTANT
        # ====================================================

        else:

            print(
                "\n🔕 No WhatsApp notification required."
            )


            try:

                save_processed_email(
                    email_id
                )

                print(
                    "✅ Email marked as processed."
                )

            except Exception as e:

                print(
                    "❌ Could not save processed email:"
                )

                print(e)


        # ----------------------------------------------------
        # COUNT EMAIL
        # ----------------------------------------------------

        processed_count += 1


        # ----------------------------------------------------
        # DEVELOPMENT SAFETY LIMIT
        # ----------------------------------------------------

        if processed_count >= MAX_EMAILS_PER_RUN:

            print(
                f"\n🛑 Development limit reached: "
                f"{MAX_EMAILS_PER_RUN} emails."
            )

            break


        # ----------------------------------------------------
        # DELAY BETWEEN GEMINI CALLS
        # ----------------------------------------------------

        print(
            f"\n⏳ Waiting "
            f"{AI_DELAY_SECONDS} seconds "
            f"before next AI request..."
        )

        time.sleep(
            AI_DELAY_SECONDS
        )


    # ========================================================
    # CYCLE FINISHED
    # ========================================================

    print("\n" + "=" * 60)

    print(
        "✅ InboxIQ cycle finished."
    )

    print(
        f"Processed "
        f"{processed_count} new email(s)."
    )

    print("=" * 60)


    return "success"


# ============================================================
# CONTINUOUS MONITOR
# ============================================================

if __name__ == "__main__":

    print("\n🚀 InboxIQ Monitor Started")

    print(
        f"📧 Gmail check interval: "
        f"{CHECK_INTERVAL} seconds"
    )

    print(
        f"🤖 Maximum AI emails per cycle: "
        f"{MAX_EMAILS_PER_RUN}"
    )

    print(
        f"⚠️ AI error cooldown: "
        f"{AI_ERROR_WAIT} seconds"
    )

    print(
        "\nPress Ctrl + C to stop."
    )


    try:

        while True:

            status = run_inboxiq()


            # =================================================
            # GEMINI 429 / 503
            # =================================================

            if status == "ai_unavailable":

                print(
                    "\n⏸️ Gemini is currently unavailable."
                )

                print(
                    "This can be caused by:"
                )

                print(
                    "• API quota being exhausted (429)"
                )

                print(
                    "• Gemini server overload (503)"
                )

                print(
                    f"\n⏳ Waiting "
                    f"{AI_ERROR_WAIT} seconds "
                    f"before trying again..."
                )

                time.sleep(
                    AI_ERROR_WAIT
                )


            # =================================================
            # GMAIL ERROR
            # =================================================

            elif status == "gmail_error":

                print(
                    "\n⚠️ Gmail connection failed."
                )

                print(
                    f"⏳ Retrying in "
                    f"{CHECK_INTERVAL} seconds..."
                )

                time.sleep(
                    CHECK_INTERVAL
                )


            # =================================================
            # NORMAL CYCLE
            # =================================================

            else:

                print(
                    f"\n⏳ Next Gmail check in "
                    f"{CHECK_INTERVAL} seconds..."
                )

                time.sleep(
                    CHECK_INTERVAL
                )


    except KeyboardInterrupt:

        print(
            "\n\n🛑 InboxIQ Monitor Stopped."
        )

        print(
            "Goodbye! 👋"
        )