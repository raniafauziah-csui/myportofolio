from django.urls import path

from main.views import (
    show_main,
    show_experience,
    show_skill,
    create_skill,
    get_skills_json,
    delete_skill,
    show_achievement,
    create_achievement,
    get_achievements_json,
    delete_achievement,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("skill/", show_skill, name="show_skill"),
    path("skill/add/", create_skill, name="create_skill"),
    path("api/skills/", get_skills_json, name="get_skills_json"),
    path("skill/<uuid:skill_id>/delete/", delete_skill, name="delete_skill"),
    path("achievement/", show_achievement, name="show_achievement"),
    path("achievement/add/", create_achievement, name="create_achievement"),
    path("api/achievements/", get_achievements_json, name="get_achievements_json"),
    path("achievement/<uuid:achievement_id>/delete/", delete_achievement, name="delete_achievement"),
]