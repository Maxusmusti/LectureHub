import testo

# List of phone numbers (1st is mine which receives msgs, 2nd is Justin's which has 'STOP'ed)
phone_number = ["+16039304539", "+18475329344"]

# List of results from "check"
is_violated = [True, True]

# Goes through each phone# and runs the send message function if there is a violation (in testo.py)
for i in range(phone_number.__len__()):
    print("REE")
    if is_violated[i] is True:
        testo.send_message(phone_number[i])
