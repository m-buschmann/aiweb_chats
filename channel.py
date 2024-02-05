## channel.py - a simple message channel
##
import datetime
from flask import Flask, request, render_template, jsonify, url_for
import json
import requests
import re
import random # for Eliza-style responses
from flask import Flask

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'https://temporary-server.de'
HUB_AUTHKEY = 'Crr-K3d-2N'

CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "The One for ELIZA"
CHANNEL_ENDPOINT = "http://vm954.rz.uni-osnabrueck.de/user031/channel.wsgi" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    # add message to messages
    messages = read_messages()
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    save_messages(messages)

    # call reply here 
    reply(message)
    return "OK", 200

def read_messages():
    global CHANNEL_FILE
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

def send_picture(image_name):
    """Send a picture to the client."""
    image_url = url_for('static', filename=image_name)
    # This function should send the image URL to the client.
    image_message = {
        "content": image_url,
        "sender": "bot",
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "image"  # This field indicates the type of message
    }

    messages = read_messages()
    messages.append(image_message)
    save_messages(messages)


def reply(message):
    """Answer to the user's message with a response from Eliza-style patterns."""
    eliza_patterns = [
        (r'hello|hi|hey', ['Hello!', 'Hi there!', 'Greetings!']),
        (r'what\'s up|what is up', ['Not much, just chatting with you!', 'The sky usually! But here in the digital world, it\'s just code.']),
        (r'how are you', ['I am just a bot, but thanks for asking!']),
        (r'your name', ['I am a chatbot, you can call me Chatty.']),
        (r'coxi', ['?- bist du auch coxi.']),
        (r'weather', ['I do not have a window, but it always feels sunny in this digital world.']),
        (r'joke|funny', ['Why did the computer go to therapy? It had too many bytes of emotional baggage!', 'Why don\'t scientists trust atoms? Because they make up everything!', 'What do you call a fake noodle? An Impasta!']),
        (r'favorite color', ['I see in binary, so it\'s all shades of 0s and 1s to me.']),
        (r'color', ['I\'ll have to ask Mary about that.']),
        (r'platypus', ['Wait, I think I have something for you! (Generated by Dall-E)']),
        (r'unicorn', ['Wait, I think I have something for you! (Generated by Dall-E)']),
        (r'help', ['I am here to listen.']),
        (r'sad|unhappy', ['I\'m here to listen. What\'s on your mind?', 'It\'s okay to feel sad. Do you want to talk about it?']),
        (r'happy|joy', ['Happiness is a wonderful feeling!', 'It\'s great to feel happy. What\'s making you feel good?']),
        (r'angry|mad', ['I\'m sorry you\'re feeling angry. What\'s making you feel this way?', 'It\'s okay to feel angry. Do you want to talk about it?']),
        (r'love', ['Love is a complex emotion, even for bots. What\'s on your mind?']),
        (r'family|parents', ['Family can be a great source of strength.', 'Tell me more about your family.']),
        (r'food|eat', ['If I could eat, I\'d probably like bytes and chips.']),
        (r'movie|film', ['Movies are a great way to unwind.', 'What type of movies do you like?', 'I would suggest going to the Sneak Peek on Mondays!']),
        (r'bye|goodbye|quit', ['Goodbye!', 'Bye!', 'Have a nice day!']),
        (r'(.*\?)', ['Sorry, I can\'t answer that.', 'I\'m not sure. What do you think?']),
        (r'(.*)', ['Tell me more!', 'Why do you say that?', 'I see.', 'Very interesting.', 'I see. And what does that tell you?', 'How does that make you feel?'])
    ]

    # Check if any pattern matches the message content
    for pattern, responses in eliza_patterns:
        if re.search(pattern, message['content'], re.IGNORECASE):

            # Select a random response from the matched pattern
            response = random.choice(responses)

            # Send a message from "bot" into the channel with the selected response
            bot_message = {
                "content": response,
                "sender": "bot",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Add the bot's message to the channel
            messages = read_messages()
            messages.append(bot_message)
            save_messages(messages)

            if 'platypus' in pattern.lower():
                image_name = '/platy.png'
                send_picture(image_name)
            if 'unicorn' in pattern.lower():
                image_name = '/unicorn.png'
                send_picture(image_name)
            return

    # If no patterns match, send a generic response
    generic_response = "I'm not sure how to respond to that. How can I help you?"
    bot_message = {
        "content": generic_response,
        "sender": "bot",
        "timestamp": datetime.datetime.now().isoformat()
    }
    messages = read_messages()
    messages.append(bot_message)
    save_messages(messages)
    return

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)
