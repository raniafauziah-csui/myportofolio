from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import Achievement, Experience, Skill


class AchievementSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = [
            "id", "name", "category", "description", "position",
            "icon_url", "timestamp_achieved", "timestamp_created",
            "star_count", "is_starred",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_description(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Description cannot be empty.")
        return value

    def validate_category(self, value):
        return strip_tags(value).strip()

    def validate_position(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Position cannot be empty.")
        return value

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()


class ExperienceSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = [
            "id", "title", "description", "category", "thumbnail",
            "started_at", "ended_at", "is_ongoing", "star_count", "is_starred",
        ]
        read_only_fields = ["id", "is_ongoing"]

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_description(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Description cannot be empty.")
        return value

    def validate_category(self, value):
        return strip_tags(value).strip()

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()


class SkillSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = [
            "id", "name", "category", "description", "icon_url",
            "star_count", "is_starred",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_description(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Description cannot be empty.")
        return value

    def validate_category(self, value):
        return strip_tags(value).strip()

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()
