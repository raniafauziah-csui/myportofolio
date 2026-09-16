from django.forms import ModelForm, TextInput, Textarea, URLInput

from main.models import Skill

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