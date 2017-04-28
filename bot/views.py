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
            convoModel.first=False
            convoModel.previous_message =''
            convoModel.save()

    def send_message(self, convoModel, sender_id, messages):
        for message in messages:
            if message['type'] == 'salute':
                post_fb_message(sender_id, message['text'])
            if message['type'] == 'statement':
                post_fb_message(sender_id, message['text'])
            if message['type'] == 'question':
                post_fb_message(sender_id, message['text'])
            if message['type'] == 'exam_question':
                options = [
{
	"title": option[0],
	"buttons":[
      {
        "type":"postback",
        "title":"is answer",
        "payload":option[1]
      }]
}
for option in messages[0]['options']
]
                post_fb_question(sender_id, messages[0])
                post_fb_options(sender_id, options)


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
                            if convo and createdd:
                                self.greet_returning_user(convo, message['sender']['id'])
                            if not createdd and not convo.ask:
                                self.send_message(convo, message['sender']['id'], ({'text': 'do you want to take an exam now?',
                                                                                    'type': 'question'
                                                                                },))
                                convo.ask=True
                                convo.save()
                            if not createdd and convo.ask:
                                resp_message = analize(message, convo)
                                self.send_message(convo, message['sender']['id'], resp_message)
                        if convo.exam_in_progress and not convo.first:
                            print('exams in progress')
                            if Exam.objects.filter(candidate__uid=message['sender']['id']).filter(finished=False):
                                exam = Exam.objects.filter(candidate__uid=message['sender']['id']).filter(finished=False)[0]
                                question  = ExamSession.objects.filter(exam=exam).filter(is_answered=False)[0].question
                                sQuestion = QuestionSerializer(question).data
                                question = sQuestion['question_text']
                                options = sQuestion['option']
                                option = []
                                for optn in options:
                                    option.append((optn['option_text'],optn['id']))
                                resp = ({'question':question,
                                    'options':option,
                                    'type':'exam_question'
                                },)
                                convo.first=True
                                convo.save()
                                self.send_message(convo, message['sender']['id'], resp)
                            else:
                                resp = ({'type':'statement',
                                    'text':'you dont have questions in the exams yet'
                                },)
                                self.send_message(convo, message['sender']['id'], resp)
                                convo.delete()
                #if postback instead
                #mark the question from the payload and increase score by 1 or 0
                #check there is an unanswered question in the exam-session
                #if there is, serve it, else, save and return exam-score and delete exam-session, conversation
                if 'postback' in message:
                    sid = message['sender']['id']
                    option_id = message['postback']['payload']
                    option=Option.objects.get(id=option_id)
                    convo = Conversation.objects.filter(candidate__uid=sid)
                    exam = Exam.objects.filter(examsession__question__option__id=option_id)[0]
                    question = ExamSession.objects.filter(question__option__id=option_id)[0]
                    if option.is_answer:
                        exam.score += 1
                        exam.save()
                    question.is_answered=True
                    question.save()
                    if not exam.finished and convo.first:
                        try:
                            question = ExamSession.objects.filter(exam=exam).filter(is_answered=False)
                            sQuestion = QuestionSerializer(question[0].question).data
                            question = sQuestion['question_text']
                            options = sQuestion['option']
                            option = []
                            for optn in options:
                                option.append((optn['option_text'],optn['id']))
                            resp = ({'question':question,
                                'options':option,
                                'type':'exam_question'
                            },)
                        except:
                            resp = ({'type':'statement',
                                'text':'you have answered all your questions for this session'
                            },)
                            self.send_message(convo, message['sender']['id'], resp)
                            score = exam.score
                            exam.finished = True
                            exam.save()
                            examsession = ExamSession.objects.filter(exam=exam)
                            for i in examsession:
                                i.delete()
                            resp = ({'type':'statement',
                                    'text':'your score for this exam is--' + str(score)
                                },{'type':'statement',
                                    'text':'we will love to see you again'
                                })
                        self.send_message(convo, message['sender']['id'], resp)
                        convo.delete()
                    else:
                        score = exam.score
                        exam.finished = True
                        exam.save()
                        examsession = ExamSession.objects.filter(exam=exam)
                        for i in examsession:
                            i.delete()
                        resp = ({'type':'statement',
                                'text':'your score for this exam is--' + str(score)
                            },)
                        self.send_message(convo, message['sender']['id'], resp)
                        convo.delete()
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
            'text':'Currently we have only Use of English available. Respond to start exams', 'type':'statement'
        })
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
    if convoModel.previous_message in positive_reply and not convoModel.exam_in_progress and token not in negative_reply:
        convoModel.exam_in_progress = True
        convoModel.save()
        questions = Question.objects.all().order_by('?')[:5]
        exam = Exam.objects.create(candidate=convoModel.candidate)
        examsession = ExamSession.objects.bulk_create([ExamSession(candidate=convoModel.candidate, exam=exam, question=q) for q in questions])
        return ({'text':'your exam begin now',
            'type':'statement'
        },)
    convoModel.delete()
    return ({'text':'Dont know what you are taking about',
    'type':'statement'
    },)


def process_exam():
    pass
