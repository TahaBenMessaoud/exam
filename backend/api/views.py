from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from dj_rest_auth.registration.views import RegisterView
from django.contrib.auth import get_user_model
from .models import Profile, Exam, ExamAttempt, Question, Option
from .serializers import ExamListSerializer, UserSerializer, QuestionSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.utils import timezone
import random
from django.db.models import F


User = get_user_model()

# ------------------------------
# GET /api/me/ endpoint
# ------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# ------------------------------
# Custom register with profile
# ------------------------------
class RegisterWithProfileView(APIView):
    """
    Handles user registration and profile creation in one request.
    Works with dj-rest-auth.
    """
    def post(self, request):
        data = request.data.copy()  # mutable copy

        name = data.pop('name', None)  # extract profile field

        # Use dj-rest-auth serializer directly
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(request)

        # Create profile
        if name:
            Profile.objects.create(user=user, name=name)

        return Response({
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
class StartExamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, exam_id):
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({"detail": "Exam not found"}, status=status.HTTP_404_NOT_FOUND)

        # 1. Create exam attempt
        attempt = ExamAttempt.objects.create(
            user=request.user,
            exam=exam,
            start_time=timezone.now(),
            is_valid=True  # default True for now
        )

        # 2. Get all questions for this exam
        questions = list(Question.objects.filter(exam=exam))

        # 3. Randomly pick the number of questions if exam.number_of_questions < total
        num_to_pick = min(exam.number_of_questions, len(questions))
        questions = random.sample(questions, num_to_pick)
        attempt.save()
        attempt.questions.set(questions)

        # 4. Serialize questions with options
        serialized_questions = QuestionSerializer(questions, many=True).data

        # 5. Return attempt id and exam info
        return Response({
            "attempt_id": attempt.id,
            "exam": {
                "exam_id": exam.id,
                "title": exam.title,
                "duration_minutes": exam.duration_minutes,
                "questions": serialized_questions
            }
        }, status=status.HTTP_201_CREATED)


class EndExamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = ExamAttempt.objects.get(id=attempt_id, user=request.user)
        if attempt.end_time:
            return Response({"detail": "Exam already ended."}, status=status.HTTP_400_BAD_REQUEST)

        attempt.end_time = timezone.now()

        submitted_answers = request.data.get("answers") or []
        submitted_map = {ans["option_id"]: ans["selected"] for ans in submitted_answers}

        score = 0
        questions = attempt.questions.prefetch_related("options")

        for question in questions:
            correct = True
            for option in question.options.all():
                selected = submitted_map.get(option.id, False)
                if option.is_correct != selected:
                    correct = False
                    break
            if correct:
                score += 1

        question_count = questions.count()
        attempt.score = (score / question_count * 100) if question_count else 0

        
        # Check duration validity (with 10% tolerance)
        duration_seconds = attempt.exam.duration_minutes * 60
        tolerance = duration_seconds * 0.10  # 10% extra time allowed
        elapsed = (attempt.end_time - attempt.start_time).total_seconds()

        if elapsed > duration_seconds + tolerance:
            attempt.is_valid = False


        attempt.save()

        return Response({
            "score": attempt.score,
            "is_valid": attempt.is_valid
        })

    
class ExamListView(APIView):
    permission_classes = []  # Public, no authentication required

    def get(self, request):
        exams = Exam.objects.all()
        serializer = ExamListSerializer(exams, many=True)
        return Response(serializer.data)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_certificates(request):
    attempts = ExamAttempt.objects.filter(
        user=request.user,
        is_valid=True,
        end_time__isnull=False,
        score__gte=F('exam__passing_score')
    ).select_related('exam')
    
    data = [
        {
            "certificate_id": a.id,
            "exam_title": a.exam.title,
            "profile_name": a.user.profile.name,
            "passing_date": a.end_time,
            "score": a.score,
        }
        for a in attempts
    ]
    return Response(data)


@api_view(['GET'])
@permission_classes([])  # no auth required
def certificate_public(request, attempt_id):
    try:
        attempt = ExamAttempt.objects.select_related('exam', 'user').get(pk=attempt_id)
    except ExamAttempt.DoesNotExist:
        return Response({"error": "Certificate not found."}, status=status.HTTP_404_NOT_FOUND)

    # Validate certificate eligibility
    if not (attempt.is_valid and attempt.end_time and attempt.score >= attempt.exam.passing_score):
        return Response({"error": "This attempt did not qualify for a certificate."},
                        status=status.HTTP_403_FORBIDDEN)

    data = {
        "exam_title": attempt.exam.title,
        "profile_name": attempt.user.profile.name,
        "passing_date": attempt.end_time,
        "score": attempt.score,
        "certificate_id": attempt.id,
    }
    return Response(data)