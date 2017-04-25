from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Candidate(models.Model):
    uid = models.BigIntegerField()
    has_not_taken_exam = models.BooleanField(default=True)


class Conversation(models.Model):
    candidate = models.ForeignKey(Candidate)
    salute = models.BooleanField(default=False)
    about = models.BooleanField(default=False)
    ask = models.BooleanField(default=False)
    previous_message = models.TextField(default='')
    current_message = models.TextField(default='')
