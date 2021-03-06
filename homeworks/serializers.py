from django.contrib.auth.models import User

from rest_framework import serializers

from students.serializers import (
    ClassSerializer, SubjectSerializer, TeacherAuthorSerializer, StudentAuthorSerializer
)
from students.utils import send_creation_email

from .models import Homework, Submission


class SubmissionSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=2048, allow_blank=False)
    solution_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = Submission
        fields = ('id', 'homework', 'student', 'content', 'solution_url', 'checked')
        depth = 1

    def create(self, validated_data):
        homework = self.context['homework']
        request = self.context['request']

        student = request.user.student

        return Submission.objects.create(homework=homework, student=student, **validated_data)


class SubmissionReadSerializer(SubmissionSerializer):
    student = StudentAuthorSerializer(read_only=True)


class HomeworkSerializer(serializers.ModelSerializer):
    details = serializers.CharField(max_length=256, allow_blank=True)

    class Meta:
        model = Homework
        fields = ('id', 'topic', 'subject', 'clazz', 'deadline', 'details', 'author')
        depth = 1

    def create(self, validated_data):
        request = self.context['request']

        author = request.user.teacher
        subject = author.subject
        clazz = self.context['clazz']

        homework = Homework.objects.create(
            subject=subject,
            author=author,
            clazz=clazz,
            **validated_data
        )

        recipient_list = User.objects.filter(student__clazz=clazz)
        for user in recipient_list:
            send_creation_email(user, model=homework)

        return homework


class HomeworkReadSerializer(HomeworkSerializer):
    subject = SubjectSerializer(read_only=True)
    clazz = ClassSerializer(read_only=True)
    author = TeacherAuthorSerializer(read_only=True)
