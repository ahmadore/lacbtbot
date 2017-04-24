from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Candidate(models.Model):
    uid = models.BigIntegerField()
    has_taken_exam = models.BooleanField(default=False)