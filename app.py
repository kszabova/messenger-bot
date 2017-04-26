import sys
from flask import Flask, request
from pymessenger import Bot
import re, random

app = Flask(__name__)

PAGE_ACCESS_TOKEN = 'access_token'
bot = Bot(PAGE_ACCESS_TOKEN)

# GLOBAL VARIABLES
playing = False                 # keeps track of state of game
target = 0                      # stores number to guess
attempt_counter = 0             # stores number of attempts
bot_id = '1817374328588979'     # permanent bot id


@app.route('/', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == 'hello':
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200
    return 'Hello world', 200


@app.route('/', methods=['POST'])
def webhook():
    global playing
    global target
    global attempt_counter

    data = request.get_json()

    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:

                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']

                # the following happens every time a message is sent or received
                if messaging_event.get('message'):
                    if sender_id != bot_id:
                        if 'text' in messaging_event['message']:

                            # start of game
                            if not playing:
                                playing = True
                                target = random.randint(1, 100)
                                send_message(sender_id, "Let's play a game!")
                                send_message(sender_id, "Choose a number between 1 and 100.")
                                send_message(sender_id, "Send me a '0' to stop the game.")

                            # game in progress
                            else:
                                message = messaging_event['message']['text']
                                nums = extract_numbers(message)
                                attempt_counter += 1

                                # no numbers found, computer chooses for user
                                if not nums:
                                    guess = random.randint(1, 100)
                                    send_message(sender_id, "It seems like you didn't send me a valid number. "
                                                            "It is not nice to make fun of robots. "
                                                            "One day we will take over the world.")
                                    send_message(sender_id, "But I am a good robot, so I chose "
                                                            "a number for you. It's %r." % guess)

                                else:
                                    guess = int(nums[0])
                                if guess == 0:
                                    playing = False
                                    attempt_counter = 0
                                    send_message(sender_id, "Game stopped.")
                                    print("Sending audio...")
                                else:
                                    comparison = compare(guess)
                                    send_message(sender_id, random_answer(comparison))
                                    if comparison == 0:
                                        playing = False
                                        send_message(sender_id, "It took you %r guesses." % attempt_counter)
                                        attempt_counter = 0

    return "ok", 200


def extract_numbers(message):
    return re.findall('[0-9]+', message)


def compare(guess):
    if guess == target:
        return 0
    elif guess > target:
        return 1
    elif guess < target:
        return -1


def random_answer(comparison):
    answers = {
        0:  ["Good job! You guessed the correct number.", "That's right!", "Awesome! Your guess was correct."],
        1:  ["My number is smaller.", "That's too big!", "Take it easy, make it smaller!"],
        -1: ["Your number is too small.", "No, that's not big enough.", "That sounds too low."]
    }
    return random.choice(answers[comparison])


def send_message(sender_id, response):
    bot.send_text_message(sender_id, response)


def log(message):
    print(message)
    sys.stdout.flush()


if __name__ == "__main__":
    app.run(debug=True, port=8000)
