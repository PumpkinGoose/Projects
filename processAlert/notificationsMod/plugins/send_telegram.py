#!/usr/bin/python3
# Llamado desde notify.py con los parametros (bot_token, chat_id, subject, body, parse_mode='html')
import sys
import requests

def send_message(bot_token, chat_id, body, parse_mode='html'):

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        'chat_id': chat_id,
        'text': body,
        'parse_mode': parse_mode,
    }
    error_message = None
    try:
        response = requests.get(url, params=params).json()
    except Exception as e:
        print(f"Error: {e}")
        error_message = "Request failed, error: {e}"

    if error_message is not None:
        print (error_message)
    else:
        if response.get('ok'):
            print ("Message sent successfully")
        else:
            print (f"Failed to send message. Error: {response['description']}")
