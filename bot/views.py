from django.shortcuts import render
from django.views import generic
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json, requests, re, random
from pprint import pprint
from .models import Candidate, Conversation

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
    
    def greet_first_time_user(self, candidate, sender_id):
        convo = Conversation.object.create(candidate=candidate)
        self.send_message(convo, sender_id, ({
            'text': 'welcome to laCbt',
            'type': 'salute'
        },{
            'text': 'LaCbt is a platform for taking mock jamb exams',
            'type': 'statement'
        }))
        
    def send_message(self, convoModel, sender_id, messages):
        for message in messages:
            if message.type == 'salute':
                post_fb_message(sender_id, message.text)
                convoModel.salute = True
            if message.type == 'statement':
                post_fb_message(sender_id, message.text)
                convoModel.about = True
            if message.type == 'question':
                post_fb_message(sender_id, messages.text)
                convoModel.ask = True
            convoModel.previous_message = convoModel.current_message
            convoModel.current_message = message.text
        convoModel.save()

    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        for entry in incoming_message['entry']:
            print(entry)
            for message in entry['messaging']:
                if 'message' in message:
                    candidate, created = Candidate.objects.get_or_create(uid=message['sender']['id'])
                    #check if candidate is created, if yes initialize conversation, else, check conversation and respond.
                    if candidate and created:
                        self.greet_first_time_user(candidate, message['sender']['id'])
                    elif candidate and not created:
                        convo, created = Conversation.objects.get_or_create(candidate=candidate)
                        if convo and created: #conversation is just started
                            if candidate.has_not_taken_exam: #default is true, so the block should run for the first time
                                self.send_message(convo, message['sender']['id'], ({
                                    'text': 'welcome back to LaCbt',
                                    'type': 'salute'
                                },{
                                    'text': 'do you want to take an exam now?',
                                    'type': 'question'
                                }))
                            else: #candidate has taken exams before
                                self.send_message(convo, message['sender']['id'], ({
                                    'text': 'welcome back to LaCbt',
                                    'type': 'salute'
                                },{
                                    'text': 'do you want to take another exam?',
                                    'type': 'question'
                                }))
                        if convo and not created:
                            if not convo.ask: #default not true, so it will ask
                                self.send_message(convo, message['sender']['id'], ({
                                    'text': 'do you want to take an exam now?',
                                    'type': 'question'
                                },))
                            else:
                                message_to_send = analize(message)
                                self.send_message(convo, message['sender']['id'], ({
                                    'text': message_to_send,
                                    'type': 'statement'
                                },))
                                convo.delete()
                                candidate.has_not_taken_exam = False
                                candidate.save()
                    #message_to_send = analize(message)
                    #post_fb_message(message['sender']['id'], message_to_send)
        return HttpResponse()


# def send_message():
#     return "hello welcome to LaCBT, a platform for online test. Would you like to take a test now?"


def post_fb_message(fbid, received_message):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=EAAEEPxRnT7cBAK6HepI2S4uNvkrFuG4j4ZApLuQ2UW6czOLe5Pv7ZBZC4gn4H8Mz7mh8syDprYB5bVsmJ88ZAc7Q8kSjH85kHbXqmWM1ZAZC4YpK07h2QwWCZAyqgDaIUOuVpQ6zoIX7mZCZAEXIGXJnwkZBRleXkkyVe5sivFvaORtAZDZD'
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":received_message}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    print(status.json())
    
    
def analize(recvd_msg):
    token = re.sub(r"[^a-zA-Z0-9\s]",' ',recvd_msg['message']['text']).lower()
    positive_reply = ['yes', 'definately', 'i think so', 'lets do this', 'let do dis', 'yeah', 'yea', 'ready', 'am ready']
    negative_reply = ['not ready', 'may be later', 'later', 'another time', 'some other time', 'next time', 'no', 'not now']
    if token in positive_reply:
        return 'We will now now begin our exams'
    elif token in negative_reply:
        return 'let us know when you are ready'
    return 'Dont know what you are taking about'