from django.shortcuts import render

from main.models import Experience

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
