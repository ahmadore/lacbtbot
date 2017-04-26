from .models import *


from rest_framework import serializers


class ExamSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Exam
        fields = '__all__'


class OptionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Option
        fields = ('id', 'option_text', 'is_answer')


class QuestionSerializer(serializers.ModelSerializer):
    option = OptionSerializer(many=True)
    
    class Meta:
        model = Question
        fields = ('id', 'question_text', 'option')


class ExamSessionSerializer(serializers.ModelSerializer):
#    candidate = CandidateSerializer()
    question = QuestionSerializer()
    class Meta:
        model = ExamSession
        fields = ('id', 'question')
