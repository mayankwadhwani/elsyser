from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

from students.serializers import (
    UserLoginSerializer, UserInfoSerializer,
    StudentSerializer,
    SubjectSerializer,
    StudentProfileSerializer, TeacherProfileSerializer,
)
from students.models import Subject, Class, Student, Teacher
from students.permissions import IsStudent, IsTeacher


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

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )


class ProfileViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get_entry_model(self, user):
        return Teacher.objects.filter(user=user).first() or Student.objects.filter(user=user).first()


    def get_serializer_model(self, user):
        return TeacherProfileSerializer if Teacher.objects.filter(user=user) else StudentProfileSerializer


    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        entry = self.get_entry_model(user)

        serializer = self.get_serializer_model(user)(entry)

        response_data = serializer.data
        response_data['can_edit'] = (user == request.user)

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )


    def update(self, request, pk=None):
        user = get_object_or_404(User, id=pk)

        if user != request.user:
            return Response(
                {'message': 'You can only update your own profile.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        entry = self.get_entry_model(user)

        serializer = self.get_serializer_model(user)(
            entry, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK
        )


class SubjectsList(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsTeacher)
    serializer_class = SubjectSerializer


    def get(self, request):
        serializer = self.serializer_class(Subject.objects.all(), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
