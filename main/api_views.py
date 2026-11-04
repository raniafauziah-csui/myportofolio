from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import Achievement
from main.permissions import IsAchievementOwnerOrReadOnly
from main.serializers import AchievementSerializer


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAchievementOwnerOrReadOnly])
def achievement_list(request):
    if request.method in ("GET", "HEAD"):
        achievements = Achievement.objects.prefetch_related("starred_by").order_by("name", "id")
        name = request.query_params.get("name", "").strip()
        if name:
            achievements = achievements.filter(name__icontains=name)
        serializer = AchievementSerializer(
            achievements, many=True, context={"request": request},
        )
        return Response(serializer.data)

    serializer = AchievementSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAchievementOwnerOrReadOnly])
def achievement_detail(request, achievement_id):
    achievement = get_object_or_404(
        Achievement.objects.prefetch_related("starred_by"), pk=achievement_id,
    )
    if request.method in ("GET", "HEAD"):
        serializer = AchievementSerializer(achievement, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        achievement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = AchievementSerializer(
        achievement, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)

@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def achievement_star(request, achievement_id):
    achievement = get_object_or_404(Achievement, pk=achievement_id)
    if achievement.starred_by.filter(pk=request.user.pk).exists():
        achievement.starred_by.remove(request.user)
    else:
        achievement.starred_by.add(request.user)
    serializer = AchievementSerializer(achievement, context={"request": request})
    return Response(serializer.data)