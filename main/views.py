import datetime
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required  
from django.core.exceptions import PermissionDenied
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from main.forms import SkillForm, AchievementForm
from main.models import Experience, Skill, Achievement

def editor_required(perm):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("/login/")
            if not request.user.has_perm(perm):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Create your views here.
def show_main(request):
    last_login = request.COOKIES.get('last_login', 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "npm": "2506595070",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "CS student at Universitas Indonesia who is into "
            "coding and likes artsy things."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)


def show_skill(request):
    skills = Skill.objects.all()
    name_query = request.GET.get("name", "").strip()
    if name_query:
        skills = skills.filter(name__icontains=name_query)

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "skill_list": skills,
        "name_query": name_query,
    }
    return render(request, "skill.html", context)

@editor_required("main.add_skill")
def create_skill(request):
    form = SkillForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Skill baru berhasil ditambahkan!")
        return redirect("main:show_skill")

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "form": form,
        "form_action": reverse("main:create_skill"),
    }
    return render(request, "skills_form.html", context)


def get_skills_json(request):
    skills = Skill.objects.all()
    name_query = request.GET.get("name", "").strip()
    if name_query:
        skills = skills.filter(name__icontains=name_query)

    data = serializers.serialize(
        "json",
        skills,
        use_natural_foreign_keys=True,
        fields=["name", "category", "description", "icon_url"],
    )
    return HttpResponse(data, content_type="application/json")

@editor_required("main.delete_skill")
def delete_skill(request, skill_id):
    skill = get_object_or_404(Skill, pk=skill_id)

    if request.method == "POST":
        skill.delete()
        messages.success(request, "Skill berhasil dihapus!")
        return redirect("main:show_skill")

    return redirect("main:show_skill")

@editor_required("main.change_skill")
def edit_skill(request, skill_id):
    skill = get_object_or_404(Skill, pk=skill_id)
    form = SkillForm(request.POST or None, instance=skill)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Skill berhasil diperbarui!")
        return redirect("main:show_skill")

    context = {
        "name": "Rania Fauziah Nur Wahyudi", 
        "form": form,
        "form_action": reverse("main:edit_skill", args=[skill.id]),
    }
    
    return render(request, "skills_form.html", context)

def show_achievement(request):
    achievements = Achievement.objects.all()
    name_query = request.GET.get("name", "").strip()
    if name_query:
        achievements = achievements.filter(name__icontains=name_query)

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "achievement_list": achievements,
        "name_query": name_query
    }
    return render(request, "achievement.html", context)

@editor_required("main.add_achievement")
def create_achievement(request):
    form = AchievementForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pencapaian baru berhasil ditambahkan!")
        return redirect("main:show_achievement")

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "form": form,
        "form_action": reverse("main:create_achievement"),
    }
    return render(request, "achievements_form.html", context)

def get_achievements_json(request):
    achievements = Achievement.objects.all()
    name_query = request.GET.get("name", "").strip()
    if name_query:
        achievements = achievements.filter(name__icontains=name_query)

    data = serializers.serialize(
        "json",
        achievements,
        use_natural_foreign_keys=True,
        fields=[
            "name",
            "category",
            "description",
            "position",
            "icon_url",
            "timestamp_achieved",
        ],
    )
    return HttpResponse(data, content_type="application/json")

@editor_required("main.delete_achievement")
def delete_achievement(request, achievement_id):
    achievement = get_object_or_404(Achievement, pk=achievement_id)

    if request.method == "POST":
        achievement.delete()
        messages.success(request, "Pencapaian berhasil dihapus!")
        return redirect("main:show_achievement")
    return redirect("main:show_achievement")

@editor_required("main.change_achievement")
def edit_achievement(request, achievement_id):
    achievement = get_object_or_404(Achievement, pk=achievement_id)
    form = AchievementForm(request.POST or None, instance=achievement)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Prestasi berhasil diperbarui!")
        return redirect("main:show_achievement")

    context = {
        "name": "Rania Fauziah Nur Wahyudi", 
        "form": form,
        "form_action": reverse("main:edit_achievement", args=[achievement.id]),
    }
    
    return render(request, "achievements_form.html", context)

def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

# Semua akun yang sudah login boleh memberi star
@login_required(login_url="/login/")
def toggle_star_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        if request.user in experience.starred_by.all():
            experience.starred_by.remove(request.user)
        else:
            experience.starred_by.add(request.user)

    return redirect("main:show_experience")


@login_required(login_url="/login/")
def toggle_star_skill(request, skill_id):
    skill = get_object_or_404(Skill, pk=skill_id)

    if request.method == "POST":
        if request.user in skill.starred_by.all():
            skill.starred_by.remove(request.user)
        else:
            skill.starred_by.add(request.user)

    return redirect("main:show_skill")


@login_required(login_url="/login/")
def toggle_star_achievement(request, achievement_id):
    achievement = get_object_or_404(Achievement, pk=achievement_id)

    if request.method == "POST":
        if request.user in achievement.starred_by.all():
            achievement.starred_by.remove(request.user)
        else:
            achievement.starred_by.add(request.user)

    return redirect("main:show_achievement")