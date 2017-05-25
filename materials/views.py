from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from students.models import Subject
from students.permissions import IsTeacher, IsTeacherAuthor
from .serializers import MaterialSerializer, MaterialReadSerializer
from .models import Material


class MaterialsViewSet(viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes_by_action = {
        'list': (IsAuthenticated,),
        'retrieve': (IsAuthenticated,),
        'create': (IsAuthenticated, IsTeacher),
        'update': (IsAuthenticated, IsTeacher, IsTeacherAuthor),
        'destroy': (IsAuthenticated, IsTeacher, IsTeacherAuthor)
    }

    def get_serializer_class(self):
        is_get_request = self.request.method in ('GET',)
        return MaterialReadSerializer if is_get_request else MaterialSerializer

    def get_permissions(self):
        return [
            permission()
            for permission
            in self.permission_classes_by_action[self.action]
        ]


class MaterialsListViewSet(mixins.ListModelMixin, MaterialsViewSet):
    def get_queryset(self):
        request = self.request
        all_materials = Material.objects.all()

        if IsTeacher().has_permission(request, self):
            return all_materials.filter(subject=request.user.teacher.subject)

        return all_materials.filter(class_number=request.user.student.clazz.number)


class NestedMaterialsViewSet(mixins.RetrieveModelMixin,
                             mixins.CreateModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             MaterialsListViewSet):
    def get_queryset(self):
        subject_id = self.kwargs['subject_pk']
        subject = get_object_or_404(Subject, id=subject_id)

        return super().get_queryset().filter(subject=subject)

    def retrieve(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, id=kwargs['subject_pk'])
        material = get_object_or_404(subject.material_set, id=kwargs['pk'])

        serializer = self.get_serializer(material)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, id=kwargs['subject_pk'])
        context = {'subject': subject, 'request': request}

        serializer = self.get_serializer_class()(context=context, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)

        return Response(serializer.validated_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, id=kwargs['subject_pk'])
        material = get_object_or_404(subject.material_set, id=kwargs['pk'])
        self.check_object_permissions(request, material)

        serializer = self.get_serializer_class()(material, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
            headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        subject = get_object_or_404(Subject, id=kwargs['subject_pk'])
        material = get_object_or_404(subject.material_set, id=kwargs['pk'])
        self.check_object_permissions(request, material)

        material.delete()

        return Response(
            {'message': 'Material successfully deleted.'},
            status=status.HTTP_200_OK
        )
