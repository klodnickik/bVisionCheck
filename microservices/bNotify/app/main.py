from flask import Flask, request
from pymessenger.bot import Bot
from app import app
import logging
import base64
import json


access_token = app.config['ACCESS_TOKEN']
verify_token = app.config['VERIFY_TOKEN']
token = app.config['TOKEN']

recipient_id = '2866397626725399'


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

    logging.warning("Recipient: {} Message: {}".format(recipient_id,response_sent_text))
    if message_type == "text": response = bot.send_text_message(recipient_id, response_sent_text)
    if message_type == "button": response = bot.send_button_message(recipient_id, response_sent_text, extra_parameter)

    logging.warning("Response : {}".format(response))

    return "success"





@app.route('/send', methods=['POST'])
def pubsub_push():
    if (request.args.get('token', '') !=token):
        return 'Invalid request', 400
        
    envelope = json.loads(request.data.decode('utf-8'))
    payload = base64.b64decode(envelope['message']['data'])
    _payload = payload.decode('utf-8')

    logging.warning ("Recieved message from pubsub: {}".format(_payload))

    # send message

    response_type = 'text'
    response_extra_parameter = 'none'
    response_sent_text = _payload

    send_message(recipient_id, response_type, response_sent_text, response_extra_parameter)
    
    return 'OK', 200




if __name__ == "__main__":
    application.run()