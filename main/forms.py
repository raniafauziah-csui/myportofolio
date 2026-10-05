from django.core.exceptions import ValidationError
from django.forms import ModelForm, TextInput, Textarea, URLInput, NumberInput, Select, DateInput
from django.utils.html import strip_tags

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

    def _clean_text(self, field_name):
        """Buang tag HTML dari input teks pengguna.

        Perhatian: ``clean_<field>`` dipanggil SETELAH validasi field, jadi
        nilai hasil ``strip_tags`` tidak otomatis dicek ulang. Input yang hanya
        berisi tag (``<b></b>``) akan menjadi string kosong, dan string kosong
        lolos ke database karena validasi ``blank`` sudah terlewati.
        Karena itu hasilnya kita periksa sendiri di sini.
        """
        value = strip_tags(self.cleaned_data[field_name])
        if not value.strip():
            raise ValidationError(
                "%s tidak boleh hanya berisi tag HTML." % self.Meta.labels[field_name],
                code="html_only",
            )
        return value

    def clean_title(self):
        return self._clean_text("title")

    def clean_description(self):
        return self._clean_text("description")

    def clean_thumbnail(self):
        # Sabuk pengaman tambahan. Pada model sekarang thumbnail adalah
        # URLField, jadi nilainya sudah ditolak lebih dulu oleh URLValidator
        # sebelum method ini dipanggil -- defense in depth saja kalau someday
        # field-nya diubah jadi CharField.
        #
        # Catatan: nilai kosong dari form adalah None, dan strip_tags(None)
        # menghasilkan string "None" yang gagal validasi URL, jadi dikembalikan
        # apa adanya.
        value = self.cleaned_data["thumbnail"]
        if not value:
            return value
        return strip_tags(value)