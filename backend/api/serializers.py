from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ExamAttempt, Profile, Exam, Question, Option

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)  # include profile in user response

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'options']

class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'title', 'duration_minutes', 'total_questions', 'questions']

class ExamAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempt
        fields = ['id', 'exam', 'start_time', 'end_time', 'is_valid', 'score']

class StartExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempt
        fields = ['id', 'exam', 'start_time']

class ExamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['id', 'title', 'duration_minutes', 'number_of_questions']