from django.urls import path
from .views import EndExamView, StartExamView, me, RegisterWithProfileView, ExamListView , my_certificates, certificate_public

urlpatterns = [
    path('me/', me, name='me'),
    path('auth/register/', RegisterWithProfileView.as_view(), name='register_with_profile'),
    path('exams/<int:exam_id>/start/', StartExamView.as_view()),
    path('exams/attempts/<int:attempt_id>/end/', EndExamView.as_view()),
    path('exams/', ExamListView.as_view()),
    path('certificates/', my_certificates, name='my-certificates'),
    path('certificates/<int:attempt_id>/', certificate_public, name='certificate-public'),
]
