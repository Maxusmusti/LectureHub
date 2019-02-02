from twilio.rest import Client
import twilio

# Trial account info and access
account_sid = "ACf906b0f96afa242a51872ea899330d52"
auth_token = "19e8fb9d6c7e39724d3b5ca54b36a7dd"
client = Client(account_sid, auth_token)


# Tries to send a message to the user, does not send if user has requested to STOP receiving messages
def send_message(phone_number):
    try:
        message = client.messages.create(
            to=phone_number,
            from_="+17344363965",
            body="""Hey, you have some heating problemos. Reply with GIVE LEGAL INFO for instructions on how to file a 311 complaint. If you wish to no longer receive these messages, reply with STOP.""")
        print(message.sid)
    except twilio.base.exceptions.TwilioRestException:
        print("Message not sent, user said to STOP")
