from django.forms import ModelForm, TextInput, Textarea, URLInput, NumberInput, Select, DateInput

from main.models import Skill, Achievement, Experience

class SkillForm(ModelForm):
    class Meta:
        model = Skill
        fields = [
            "name",
            "category",
            "description",
            "icon_url",
        ]

        labels = {
            "name": "Nama Skill",
            "category": "Kategori Skill",
            "description": "Deskripsi Skill",
            "icon_url": "Tautan Skill",
        }

        widgets = {
            "name": TextInput(
                attrs={
                    "placeholder": "Portofolio Desain",
                    "maxlength": 255,
                }
            ),
            "category": Select(),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan Proyekmu",
                    "rows": 3,
                }
            ),
            "icon_url": URLInput(
                attrs={
                    "placeholder": "https://github.com/kakBurhan/burhanquestv4",
                }
            ),
        }

class AchievementForm(ModelForm):
    class Meta:
        model = Achievement
        fields = [
            "name",
            "category",
            "description",
            "position",
            "icon_url",
            "timestamp_achieved",
        ]

        labels = {
            "name": "Nama Lomba",
            "category": "Kategori Lomba",
            "description": "Deskripsi Lomba",
            "position": "Posisi/Urutan Juara",
            "icon_url": "Tautan Gambar",
            "timestamp_achieved": "Tahun"
        }

        widgets = {
            "name": TextInput(
                attrs={
                    "placeholder": "Hackathon UI",
                    "maxlength": 255,
                }
            ),

            "category": Select(),

            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan karyamu yang memenangkan lomba ini",
                    "rows": 3,
                }
            ),

            "position": TextInput(
                attrs={
                    "placeholder": "Juara berapa?",
                    "maxlength": 255,
                }
            ),

            "icon_url": URLInput(
                attrs={
                    "placeholder": "https://...",
                }
            ),

            "timestamp_achieved": NumberInput(
                attrs={
                    "placeholder": "2026",
                    "min": 2000,
                    "max": 2100,

                }
            )
        }

class ExperienceForm(ModelForm):
    class Meta:
        model = Experience
        fields = [
            "title",
            "description",
            "category",
            "thumbnail",
            "started_at",
            "ended_at",
        ]

        labels = {
            "title": "Judul Pengalaman",
            "description": "Deskripsi",
            "category": "Category",
            "thumbnail": "Link Gambar",
            "started_at": "Waktu Mulai",
            "ended_at": "Waktu Berakhir",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Staff OH Fasilkom 2025",
                    "maxlength": 255
                }
            ),

            "description": Textarea(
                attrs={
                    "placeholder": "Menjadi staff divisi Visual Design"
                }
            ),

            "category": Select(),

            "thumbnail": URLInput(
                attrs={
                    "placeholder": "https://...",
                }
            ),

            "started_at": DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "ended_at": DateInput(
                attrs={
                    "type": "date",
                }
            )
        }