from collections import defaultdict

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

from .serializers import (
    UserLoginSerializer, UserInfoSerializer,
    ClassSerializer,
    StudentSerializer,
    SubjectSerializer,
    StudentProfileSerializer, TeacherProfileSerializer,
    GradesSerializer
)
from .models import Subject, Class, Student, Teacher, Grade
from .permissions import IsValidUser, IsStudent, IsTeacher, IsTeachersSubject


class StudentRegistration(generics.CreateAPIView):
    serializer_class = StudentSerializer


class UserLogin(generics.CreateAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        response_data = UserInfoSerializer(user).data
        response_data['token'] = token.key
        response_data['is_teacher'] = Teacher.objects.filter(user=user).exists()

        return Response(response_data, status=status.HTTP_200_OK)


class ProfileViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    permission_classes_by_action = {
        'retrieve': (IsAuthenticated,),
        'update': (IsAuthenticated, IsValidUser),
    }

    def get_permissions(self):
        return [
            permission()
            for permission
            in self.permission_classes_by_action[self.action]
        ]

    def get_entry_model(self, user):
        teachers = Teacher.objects.filter(user=user)
        students = Student.objects.filter(user=user)

        return teachers.first() or students.first()

    def get_serializer_model(self, user):
        teachers = Teacher.objects.filter(user=user)

        return TeacherProfileSerializer if teachers else StudentProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs['pk'])
        entry = self.get_entry_model(user)

        serializer = self.get_serializer_model(user)(entry)

        response_data = serializer.data
        response_data['can_edit'] = (user == request.user)

        return Response(response_data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs['pk'])
        self.check_object_permissions(request, user)

        entry = self.get_entry_model(user)

        serializer = self.get_serializer_model(user)(
            entry, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class SubjectsList(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SubjectSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(Subject.objects.all(), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class GradesList(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = GradesSerializer

    def get(self, request, *args, **kwargs):
        grades = Grade.objects.filter(subject__id=kwargs['subject_pk']).order_by('-pk')

        serializer = self.serializer_class(grades, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class GradesDetail(generics.ListCreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes_by_action = {
        'get': (IsAuthenticated,),
        'post': (IsAuthenticated, IsTeacher, IsTeachersSubject)
    }
    serializer_class = GradesSerializer

    def get_permissions(self):
        return [
            permission()
            for permission
            in self.permission_classes_by_action[self.request.method.lower()]
        ]

    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs['user_pk'])
        student = user.student

        if IsStudent().has_permission(request, self):
            if student != request.user.student:
                return Response(
                    {'message': 'You can view only your own grades.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        grades = Grade.objects.filter(
            subject__id=kwargs['subject_pk']
        ).filter(
            student__id=user.student.pk
        )

        serializer = self.serializer_class(grades, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, id=kwargs['subject_pk'])
        self.check_object_permissions(request, subject)

        user = get_object_or_404(User, id=kwargs['user_pk'])

        context = {
            'request': request,
            'subject': subject,
            'student': user.student
        }

        serializer = self.serializer_class(context=context, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)

        return Response(serializer.validated_data, status=status.HTTP_201_CREATED, headers=headers)


class StudentsList(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = StudentProfileSerializer

    def get(self, request, *args, **kwargs):
        clazz = get_object_or_404(
            Class,
            number=kwargs['class_number'],
            letter=kwargs['class_letter']
        )
        students = Student.objects.filter(clazz=clazz)

        serializer = self.serializer_class(students, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ClassesList(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ClassSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(Class.objects.all(), many=True)

        data = defaultdict(list)
        for clazz in serializer.data:
            data[clazz['number']].append(clazz)

        return Response(data, status=status.HTTP_200_OK)


class ClassesNumberList(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ClassSerializer

    def get(self, request, *args, **kwargs):
        classes = Class.objects.filter(number=kwargs['class_number'])
        serializer = self.serializer_class(classes, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
