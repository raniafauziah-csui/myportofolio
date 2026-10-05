import datetime
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required  
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from main.forms import SkillForm, AchievementForm, ExperienceForm
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
        "title_query": request.GET.get("title", "").strip(),
        "form": ExperienceForm(),
    }
    return render(request, "experience.html", context)

def show_skill(request):
    name_query = request.GET.get("name", "").strip()

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "name_query": name_query,
        "form": SkillForm()
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

def build_json_payload(queryset, request, extra_fields):
    """Bentuk payload JSON untuk endpoint API.

    Semua endpoint memakai bentuk yang sama: ``pk`` berisi primary key dan
    ``fields`` berisi data objek. Ditambahkan ``category_display`` supaya
    klien tidak perlu memetakan label kategori secara manual, plus informasi
    star yang bergantung pada user yang sedang login.
    """
    payload = []
    for obj in queryset.prefetch_related("starred_by"):
        starred_users = obj.starred_by.all()
        is_starred = request.user in starred_users if request.user.is_authenticated else False

        payload.append({
            "pk": str(obj.pk),
            "fields": {
                **extra_fields(obj),
                "category_display": obj.get_category_display(),
                "star_count": starred_users.count(),
                "is_starred": is_starred,
                "starred_by_names": ", ".join(user.username for user in starred_users),
            },
        })

    return JsonResponse(payload, safe=False)


def get_skills_json(request):
    name_query = request.GET.get("name", "").strip()
    skills = Skill.objects.all()

    if name_query:
        skills = skills.filter(name__icontains=name_query)

    return build_json_payload(
        skills,
        request,
        lambda skill: {
            "name": skill.name,
            "category": skill.category,
            "description": skill.description,
            "icon_url": skill.icon_url,
        },
    )

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
    name_query = request.GET.get("name", "").strip()
    achievements = Achievement.objects.all()

    if name_query:
        achievements = achievements.filter(name__icontains=name_query)

    return build_json_payload(
        achievements,
        request,
        lambda achievement: {
            "name": achievement.name,
            "category": achievement.category,
            "description": achievement.description,
            "position": achievement.position,
            "icon_url": achievement.icon_url,
            "timestamp_achieved": achievement.timestamp_achieved,
        },
    )

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

@require_POST
def create_skill_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Silakan login terlebih dahulu."},
            status=403,
        )

    if not request.user.has_perm("main.add_skill"):
        return JsonResponse(
            {"message": "Kamu tidak memiliki izin untuk menambahkan skill."},
            status=403,
        )

    form = SkillForm(request.POST)
    if form.is_valid():
        skill = form.save()
        return JsonResponse(
            {"message": "Skill berhasil ditambahkan.", "pk": str(skill.id)},
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

@editor_required("main.add_experience")
def create_experience(request):
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pengalaman baru berhasil ditambahkan!")
        return redirect("main:show_experience")

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "form": form,
        "form_action": reverse("main:create_experience"),
        "is_edit": False,
    }
    return render(request, "experiences_form.html", context)


@editor_required("main.change_experience")
def edit_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pengalaman berhasil diperbarui!")
        return redirect("main:show_experience")

    context = {
        "name": "Rania Fauziah Nur Wahyudi",
        "form": form,
        "form_action": reverse("main:edit_experience", args=[experience.id]),
        "is_edit": True,
    }
    return render(request, "experiences_form.html", context)


@editor_required("main.delete_experience")
def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Pengalaman berhasil dihapus!")
        return redirect("main:show_experience")

    return redirect("main:show_experience")


@require_POST
def create_experience_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Silakan login terlebih dahulu."},
            status=403,
        )

    if not request.user.has_perm("main.add_experience"):
        return JsonResponse(
            {"message": "Kamu tidak memiliki izin untuk menambahkan pengalaman."},
            status=403,
        )

    form = ExperienceForm(request.POST)
    if form.is_valid():
        experience = form.save()
        return JsonResponse(
            {"message": "Pengalaman berhasil ditambahkan.", "pk": str(experience.id)},
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


def get_experiences_json(request):
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all()

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    return build_json_payload(
        experiences,
        request,
        lambda experience: {
            "title": experience.title,
            "description": experience.description,
            "category": experience.category,
            "thumbnail": experience.thumbnail,
            "started_at": experience.started_at,
            "ended_at": experience.ended_at,
            "is_ongoing": experience.is_ongoing,
        },
    )