from rest_framework import filters


class TeachersListFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(author=request.user)


class ClassNumberFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(class_number=view.kwargs['class_number'])


class ClassLetterFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        class_letter = request.query_params.get('class_letter', '')
        return queryset.filter(class_letter=class_letter) if class_letter else queryset
