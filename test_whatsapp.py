from whatsapp_sender import send_whatsapp_message

message = """🚀 InboxIQ Test

If you received this message,
your WhatsApp integration is working correctly.

Time to build the dashboard! 🎉
"""

success = send_whatsapp_message(message)

print("Success:", success)