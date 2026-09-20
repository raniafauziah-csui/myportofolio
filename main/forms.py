from django.forms import ModelForm, TextInput, Textarea, URLInput, NumberInput

from main.models import Skill, Achievement

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
            "category": TextInput(
                            attrs={
                                "placeholder": "Programming, Graphic Design, Drawing/Painting",
                            }
                        ),
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

            "category": TextInput(
                attrs={
                    "placeholder": "Hackathon",
                }
            ),

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