from django.contrib import admin
from .models import Candidate, Conversation, Exam, ExamSession, Question, Option

# Register your models here.
admin.site.register(Candidate)
admin.site.register(Conversation)
admin.site.register(Exam)
admin.site.register(ExamSession)
admin.site.register(Question)
admin.site.register(Option)
