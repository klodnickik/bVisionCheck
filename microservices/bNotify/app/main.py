from flask import Flask, request
from pymessenger.bot import Bot
from app import app
import logging


access_token = app.config['ACCESS_TOKEN']
verify_token = app.config['VERIFY_TOKEN'] 


bot = Bot(access_token)

buttons = []

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

@app.route("/bot", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    else:

       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):

                logging.warning(message)     
                msg_text = message['message']['text']           
                
                
                recipient_id = message['sender']['id']
                response_type = 'text'
                response_extra_parameter = 'none'
                response_sent_text = "Odpowiedz " + msg_text


                # wysylam wiadomosc zwrotna
                send_message(recipient_id, response_type, response_sent_text, response_extra_parameter)

    return "OK"

def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    if token_sent == verify_token:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def send_message(recipient_id, message_type, response_sent_text, extra_parameter):
    #sends user the text message provided via input response parameter

    if message_type == "text": response = bot.send_text_message(recipient_id, response_sent_text)
    if message_type == "button": response = bot.send_button_message(recipient_id, response_sent_text, extra_parameter)

    logging.info(response)

    return "success"


if __name__ == "__main__":
    application.run()