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
    exam_in_progress = models.BooleanField(default=False)

class Exam(models.Model):
    candidate=models.ForeignKey(Candidate, on_delete=models.CASCADE)
    finished=models.BooleanField(default=False)
    score = models.IntegerField(default=0)


class Question(models.Model):
    question_text = models.TextField()
    
    def __str__(self):
        return '%i' %self.id


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='option')
    option_text = models.TextField()
    is_answer = models.BooleanField(default=False)


class ExamSession(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    is_answered=models.BooleanField(default=False)
