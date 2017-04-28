from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Candidate(models.Model):
    uid = models.BigIntegerField()
    has_not_taken_exam = models.BooleanField(default=True)
    


class Conversation(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    salute = models.BooleanField(default=False)
    about = models.BooleanField(default=False)
    ask = models.BooleanField(default=False)
    first = models.BooleanField(default=False)
    previous_message = models.TextField(default='', null=True, blank=True)
    current_message = models.TextField(default='', null=True, blank=True)
    exam_in_progress = models.BooleanField(default=False)

class Exam(models.Model):
    """
         dgAAAAA
    """
    title = models.TextField()


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam')
    question_text = models.TextField()
    is_answered = models.BooleanField(default=False)

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='option')
    option_text = models.TextField()
    is_answer = models.BooleanField(default=False)


class ExamSession(models.Model):
    """
        candidate: represents the candidate 
    """
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)


class ExamScore(models.Model):
    session = models.OneToOneField(ExamSession, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
