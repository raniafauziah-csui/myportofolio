from django.contrib import admin

from main.models import Achievement, Experience, Skill


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "started_at", "ended_at")
    list_filter = ("category",)
    search_fields = ("title", "description")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name", "description")
    filter_horizontal = ("starred_by",)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "position", "timestamp_achieved")
    list_filter = ("category",)
    search_fields = ("name", "description", "position")
    filter_horizontal = ("starred_by",)
