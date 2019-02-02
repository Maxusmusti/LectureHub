TestCases.py is the place to run the send messages test.

run.py (in Scripts, which shouldhonestly contain testo and
TestCases as well), is what one would run in a virtualenv to
set up local web server (with flask), then use ngrok to make
it accessible. This enables the user to send custom replies
(other than the default STOP and START) to get additional
responses.

I USE THIS FOR run.py:
C:\Users\maxus\TestFolder\Scripts>python run.py
AS WELL AS:
C:\Users\maxus>ngrok http 5000

ALSO: Make sure the twilio number is reading messages from the public
      ngrok link with /sms appended (within Twilio phone# settings).