from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import Achievement, Experience, Skill
from main.permissions import IsPortfolioOwnerOrEditorOrReadOnly
from main.serializers import (
    AchievementSerializer, ExperienceSerializer, SkillSerializer,
)


def _list_or_create(request, model, serializer_class, search_field):
    """Handle GET (with search) and POST for a model's list endpoint."""
    if request.method in ("GET", "HEAD"):
        objects = model.objects.prefetch_related("starred_by")
        query = request.query_params.get(search_field, "").strip()
        if query:
            objects = objects.filter(**{f"{search_field}__icontains": query})
        objects = objects.order_by(search_field, "id")
        serializer = serializer_class(
            objects, many=True, context={"request": request},
        )
        return Response(serializer.data)

    serializer = serializer_class(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def _detail(request, model, object_id, serializer_class):
    """Handle GET, PUT, PATCH, and DELETE for a model's detail endpoint."""
    obj = get_object_or_404(
        model.objects.prefetch_related("starred_by"), pk=object_id,
    )

    if request.method in ("GET", "HEAD"):
        serializer = serializer_class(obj, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = serializer_class(
        obj, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


def _toggle_star(request, model, object_id, serializer_class):
    """Toggle the current user's star on an object."""
    obj = get_object_or_404(model, pk=object_id)
    if obj.starred_by.filter(pk=request.user.pk).exists():
        obj.starred_by.remove(request.user)
    else:
        obj.starred_by.add(request.user)
    serializer = serializer_class(obj, context={"request": request})
    return Response(serializer.data)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_list(request):
    return _list_or_create(request, Experience, ExperienceSerializer, "title")


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_detail(request, experience_id):
    return _detail(request, Experience, experience_id, ExperienceSerializer)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def experience_star(request, experience_id):
    return _toggle_star(request, Experience, experience_id, ExperienceSerializer)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def skill_list(request):
    return _list_or_create(request, Skill, SkillSerializer, "name")


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def skill_detail(request, skill_id):
    return _detail(request, Skill, skill_id, SkillSerializer)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def skill_star(request, skill_id):
    return _toggle_star(request, Skill, skill_id, SkillSerializer)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def achievement_list(request):
    return _list_or_create(request, Achievement, AchievementSerializer, "name")


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def achievement_detail(request, achievement_id):
    return _detail(request, Achievement, achievement_id, AchievementSerializer)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def achievement_star(request, achievement_id):
    return _toggle_star(request, Achievement, achievement_id, AchievementSerializer)
