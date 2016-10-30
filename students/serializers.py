from django.contrib.auth.models import User
from django.contrib.auth import login

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Subject, Class, Student, Exam, News


class SubjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = ('title',)


class ClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = Class
        fields = ('title', 'number')


class ExamSerializer(serializers.ModelSerializer):

    subject = SubjectSerializer()

    class Meta:
        model = Exam
        fields = ('subject', 'date', 'topic')


class NewsSerializer(serializers.ModelSerializer):

    class Meta:
        model = News
        fields = ('title', 'content', 'date')


class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        style={
            'input_type': 'password',
        },
        error_messages={
            'blank': 'Password cannot be empty.',
            'min_length': 'Password too short.',
        },
    )

    email = serializers.EmailField(
        max_length=100,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Student with this email already exists.'
            )
        ],
    )

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password',
        )
        extra_kwargs = {
            'username': {'read_only': True},
            'password': {'write_only': True},
        }


class StudentSerializer(serializers.ModelSerializer):

    user = UserRegistrationSerializer()
    clazz = ClassSerializer()

    class Meta:
        model = Student
        fields = ('user', 'clazz')

    def create(self, validated_data):
        user_data = validated_data.pop('user')

        first_name = user_data.pop('first_name')
        last_name = user_data.pop('last_name')
        username = first_name + '_' + last_name
        email = user_data.pop('email')

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        user.set_password(user_data.pop('password'))
        user.save()

        login(self.context['request'], user)

        return Student.objects.create(user=user, **validated_data)
