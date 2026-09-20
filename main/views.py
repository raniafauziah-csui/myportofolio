from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from main.forms import SkillForm, AchievementForm
from main.models import Experience, Skill, Achievement

# Create your views here.
def show_main(request):
    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "npm": "2506595070",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "CS student at Universitas Indonesia who is into "
            "coding and likes artsy things."
        ),
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

    data = serializers.serialize("json", skills)
    return HttpResponse(data, content_type="application/json")


def delete_skill(request, skill_id):
    skill = get_object_or_404(Skill, pk=skill_id)

    if request.method == "POST":
        skill.delete()
        messages.success(request, "Skill berhasil dihapus!")
        return redirect("main:show_skill")

    return redirect("main:show_skill")

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

    data = serializers.serialize("json", achievements)
    return HttpResponse(data, content_type="application/json")

def delete_achievement(request, achievement_id):
    achievement = get_object_or_404(Achievement, pk=achievement_id)

    if request.method == "POST":
        achievement.delete()
        messages.success(request, "Pencapaian berhasil dihapus!")
        return redirect("main:show_achievement")
    return redirect("main:show_achievement")

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