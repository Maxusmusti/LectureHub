from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():

    # Get user response
    reply = request.values.get('Body', None)

    # Start our response
    resp = MessagingResponse()

    # Add a message
    if reply == 'GIVE LEGAL INFO':
        resp.message("Hello I am lawyer here is 311 stuff: (311 Stuff)")
    elif reply != 'START':
        resp.message("Not a valid response.")

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True)
