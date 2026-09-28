from django.urls import path

from main.views import (
    show_main,
    show_experience,
    show_skill,
    create_skill,
    get_skills_json,
    delete_skill,
    edit_skill,
    show_achievement,
    create_achievement,
    get_achievements_json,
    delete_achievement,
    edit_achievement,
    register,
    login_user,
    logout_user,
    toggle_star_experience,
    toggle_star_skill,
    toggle_star_achievement,
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
    path("skill/<uuid:skill_id>/edit/", edit_skill, name="edit_skill"),
    path("achievement/<uuid:achievement_id>/edit/", edit_achievement, name="edit_achievement"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path(
        "experience/<uuid:experience_id>/toggle-star/",
        toggle_star_experience,
        name="toggle_star_experience",
    ),
    path(
        "skill/<uuid:skill_id>/toggle-star/",
        toggle_star_skill,
        name="toggle_star_skill",
    ),
    path(
        "achievement/<uuid:achievement_id>/toggle-star/",
        toggle_star_achievement,
        name="toggle_star_achievement",
    ),
]