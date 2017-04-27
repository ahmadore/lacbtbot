from django.shortcuts import render
from django.views import generic
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json, requests, re, random
from pprint import pprint
from .models import Candidate, Conversation, ExamSession, Question
from .serializers import *

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
        convo = Conversation.objects.create(candidate=candidate)
        self.send_message(convo, sender_id, ({
            'text': 'welcome to laCbt',
            'type': 'salute'
        },{
            'text': 'LaCbt is a platform for taking mock jamb exams',
            'type': 'statement'
        }))
        convo.salute = True
        convo.about = True
        convo.save()

    def greet_returning_user(self, convoModel, sender_id):
            messages = ({
                            'text': 'welcome back to LaCbt',
                            'type': 'salute'
                        },{
                            'text': 'do you want to take an exam now?',
                            'type': 'question'
                        })
            self.send_message(convoModel, sender_id,messages)
            convoModel.salute = True
            convoModel.about = True
            convoModel.ask = True
            convoModel.save()

    def send_message(self, convoModel, sender_id, messages):
        for message in messages:
            if message['type'] == 'salute':
                post_fb_message(sender_id, message['text'])
                convoModel.salute = True
            if message['type'] == 'statement':
                post_fb_message(sender_id, message['text'])
                convoModel.about = True
            if message['type'] == 'question':
                post_fb_message(sender_id, message['text'])
                convoModel.ask = True
            if message['type'] == 'exam_question':
                options = [
{
	"title": option,
	"buttons":[
      {
        "type":"postback",
        "title":"is answer",
        "payload":"DEVELOPER_DEFINED_PAYLOAD"
      }]
}
for option in messages[0]['options']
]
                post_fb_question(sender_id, messages[0])
                post_fb_options(sender_id, options)
        convoModel.save()

    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                if 'message' in message:
                    candidate, created = Candidate.objects.get_or_create(uid=message['sender']['id'])
                    #check if candidate is created, if yes initialize conversation, else, check conversation and respond.
                    if candidate and created:
                        self.greet_first_time_user(candidate, message['sender']['id'])
                    elif candidate and not created:
                        convo, createdd = Conversation.objects.get_or_create(candidate=candidate)
                        if not convo.exam_in_progress:
                            if createdd:
                                self.greet_returning_user(convo, message['sender']['id'])
                            if not createdd and not convo.ask:
                                self.send_message(convo, message['sender']['id'], ({'text': 'do you want to take an exam now?',
                                                                                    'type': 'question'
                                                                                },))
                            else:
                                resp_message = analize(message, convo)
                                self.send_message(convo, message['sender']['id'], resp_message)
                        if convo.exam_in_progress:
                            print('exams in progress')
                            try:
                                question = Question.objects.filter(examsession__candidate=candidate).filter(is_answered=False).first()
                                #question = Question.objects.all()
                                #print(question)
                                sQuestion = QuestionSerializer(question).data
                                print(question)
                                question = sQuestion['question_text']
                                #print(question)
                                options = sQuestion['option']
                                print("---------")
                                print(options)
                                print(sQuestion['option'])
                                print("---------")
                                option = []
                                for optn in options:
                                    option.append(optn['option_text'])
                                print(options)
                                resp = ({'question':question,
                                    'options':option,
                                    'type':'exam_question'
                                },)
                                # return
                            except:
                                raise
                                resp = ({'type':'statement',
                                    'text':'you dont have questions in the exams yet'
                                },)
                                #convo.exam_in_progress = False
                                #convo.ask = False
                                convo.delete()
                            self.send_message(convo, message['sender']['id'], resp)
        return HttpResponse()


def post_fb_message(fbid, received_message):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=EAAEEPxRnT7cBAK6HepI2S4uNvkrFuG4j4ZApLuQ2UW6czOLe5Pv7ZBZC4gn4H8Mz7mh8syDprYB5bVsmJ88ZAc7Q8kSjH85kHbXqmWM1ZAZC4YpK07h2QwWCZAyqgDaIUOuVpQ6zoIX7mZCZAEXIGXJnwkZBRleXkkyVe5sivFvaORtAZDZD'
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":received_message}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    #print(status.json())


def post_fb_question(fbid, messages):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=EAAEEPxRnT7cBAK6HepI2S4uNvkrFuG4j4ZApLuQ2UW6czOLe5Pv7ZBZC4gn4H8Mz7mh8syDprYB5bVsmJ88ZAc7Q8kSjH85kHbXqmWM1ZAZC4YpK07h2QwWCZAyqgDaIUOuVpQ6zoIX7mZCZAEXIGXJnwkZBRleXkkyVe5sivFvaORtAZDZD'
    response_msg = json.dumps({
                          "recipient":{
                            "id":fbid
                          }, 
                          "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "generic",
                                    "elements": [
                                        {
                                            "title": messages['question'],
                                            "subtitle": 'anything',
                                        }
                                    ]
                                }
                            }
                        }}
                        )
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    #print(status.json())
    
    
def post_fb_options(fbid, options):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=EAAEEPxRnT7cBAK6HepI2S4uNvkrFuG4j4ZApLuQ2UW6czOLe5Pv7ZBZC4gn4H8Mz7mh8syDprYB5bVsmJ88ZAc7Q8kSjH85kHbXqmWM1ZAZC4YpK07h2QwWCZAyqgDaIUOuVpQ6zoIX7mZCZAEXIGXJnwkZBRleXkkyVe5sivFvaORtAZDZD'
    response_msg = json.dumps({
  "recipient":{
    "id":fbid
  }, "message": {
    "attachment": {
        "type": "template",
        "payload": {
            "template_type": "list",
            "top_element_style": "compact",
            "elements": options 
        }
    }
}}
)
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    #print(status.json())


def analize(recvd_msg, convoModel):
    token = re.sub(r"[^a-zA-Z0-9\s]",' ',recvd_msg['message']['text']).lower()
    positive_reply = ['yes', 'definately', 'i think so', 'lets do this', 'let do dis', 'yeah', 'yea', 'ready', 'am ready']
    negative_reply = ['not ready', 'may be later', 'later', 'another time', 'some other time', 'next time', 'no', 'not now']
    resp = ({
            'text':'These are the currently available exams', 'type':'statement',
        },{
            'text':'A-use of english', 'type':'statement'
        },{
            'text':'B-Mathemaics', 'type':'statement'
        },{
            'text':'C-Physics', 'type':'statement'
        },{
            'text':'D-Chemistry', 'type':'statement'
        },{
            'text':'E-Biology', 'type':'statement'
        })
    elist = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':6}
    if token in positive_reply and convoModel.previous_message not in positive_reply:
        convoModel.previous_message = token
        convoModel.save()
        return resp
    if token in negative_reply:
        convoModel.delete()
        return ({'text':'let us know when you are ready',
        'type':'statement'
        },
        {'text':'Have nice day',
        'type':'statement'
        },)
    if convoModel.previous_message in positive_reply:
        convoModel.exam_in_progress = True
        convoModel.save()
        #if token.lower() in elist.keys():
        #    exam_id = elist[token.lower()]
        exam = Exam.objects.get(id=1)
        #questions = Question.objects.filter(exam=exam).order_by('?')[:20]
        questions = Question.objects.all()
        examsession = ExamSession.objects.bulk_create([ExamSession(candidate=convoModel.candidate, question=q) for q in questions])
        print(examsession)
        return ({'text':'your exam begin now',
            'type':'statement'
        },)
    convoModel.candidate.delete()
    return ({'text':'Dont know what you are taking about',
    'type':'statement'
    },)


def process_exam():
    pass