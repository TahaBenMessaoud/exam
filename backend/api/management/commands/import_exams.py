import json
from django.core.management.base import BaseCommand
from api.models import Exam, Question, Option

class Command(BaseCommand):
    help = 'Import exams from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing exams')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for exam_data in data:
            exam = Exam.objects.create(
                title=exam_data['title'],
                duration_minutes=exam_data['duration_minutes'],
                number_of_questions=exam_data['number_of_questions'],
                passing_score=exam_data['passing_score']
            )

            for q in exam_data.get('questions', []):
                question = Question.objects.create(
                    exam=exam,
                    text=q['text']
                )
                for opt in q.get('options', []):
                    Option.objects.create(
                        question=question,
                        text=opt['text'],
                        is_correct=opt['is_correct']
                    )

        self.stdout.write(self.style.SUCCESS('Exams imported successfully!'))
