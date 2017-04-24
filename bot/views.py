from django.shortcuts import render
from django.views import generic
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json, requests, re, random
from pprint import pprint
from .models import Candidate

# Create your views here.
class lacbtView(generic.View):
    def get(self, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == '3445665234563845347569':
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error! invalid token')

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        for entry in incoming_message['entry']:
            print(entry)
            for message in entry['messaging']:
                if 'message' in message:
                    #pprint(message)
                    #call a function to analize and construct a response for the sender
                    candidate, created = Candidate.objects.get_or_create(uid=message['sender']['id'])
                    if candidate and created:
                        post_fb_message(message['sender']['id'], 'welcome to laCbt a platform for taking mock jamb exams')
                        post_fb_message(message['sender']['id'], 'Would like to take an exam?')
                    elif candidate and not created:
                        if candidate.has_taken_exam:
                            post_fb_message(message['sender']['id'], 'welcome back to LaCbt')
                            post_fb_message(message['sender']['id'], 'do you want to take an exam?')
                        else:
                            post_fb_message(message['sender']['id'], 'welcome back to LaCbt')
                            post_fb_message(message['sender']['id'], 'are you finally ready to take an exam?')
                    #message_to_send = analize(message)
                    #post_fb_message(message['sender']['id'], message_to_send)
        return HttpResponse()


def send_message():
    return "hello welcome to LaCBT, a platform for online test. Would you like to take a test now?"


def post_fb_message(fbid, received_message):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=EAAEEPxRnT7cBAK6HepI2S4uNvkrFuG4j4ZApLuQ2UW6czOLe5Pv7ZBZC4gn4H8Mz7mh8syDprYB5bVsmJ88ZAc7Q8kSjH85kHbXqmWM1ZAZC4YpK07h2QwWCZAyqgDaIUOuVpQ6zoIX7mZCZAEXIGXJnwkZBRleXkkyVe5sivFvaORtAZDZD'
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":received_message}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    print(status.json())
    
    
def analize(recvd_msg):
    token = re.sub(r"[^a-zA-Z0-9\s]",' ',recvd_msg['message']['text']).lower()
    positive_reply = ['yes', 'definately', 'i think so', 'lets do this', 'let do dis', 'yeah', 'yea']
    if token in positive_reply:
        return 'so you think you can'
    return 'ok, have a nice day'