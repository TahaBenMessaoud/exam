from django.db import models
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name or self.user.username


class Exam(models.Model):
    title = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField()
    number_of_questions = models.PositiveIntegerField()
    passing_score = models.FloatField()

    def __str__(self):
        return self.title


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

    def __str__(self):
        return f"{self.exam.title} - Q{self.id}"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.id}: {self.text}"
    
class ExamAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    questions = models.ManyToManyField(Question, blank=True)  
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.exam.title} attempt"

    def validate_duration(self, tolerance_seconds=5):
        """
        Checks if the attempt duration is within allowed exam duration + tolerance.
        """
        if not self.end_time:
            return False
        duration = (self.end_time - self.start_time).total_seconds()
        allowed = self.exam.duration_minutes * 60 + tolerance_seconds
        self.is_valid = duration <= allowed
        self.save()
        return self.is_valid
