import importlib.util
import os
import re
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.conf import settings as django_settings
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from main.forms import AchievementForm, SkillForm
from main.models import Achievement, Experience, Skill
from portofolio import settings as portofolio_settings


def extract_js_identifiers(html):
    """Kumpulkan identifier SCREAMING_SNAKE yang benar-benar dipakai di dalam
    blok <script> halaman.

    Komentar dan string literal dilewati supaya kata seperti 'POST' di
    ``method: 'POST'`` atau 'HTML' di dalam komentar tidak salah dianggap
    sebagai identifier yang belum dideklarasikan.
    """
    match = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    source = match.group(1) if match else ""

    identifiers = set()
    token = ""
    index = 0
    length = len(source)

    while index < length:
        char = source[index]

        if char in ("'", '"', "`"):
            quote = char
            index += 1
            while index < length:
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    index += 1
                    break
                index += 1
            continue

        if source.startswith("//", index):
            while index < length and source[index] != "\n":
                index += 1
            continue

        if source.startswith("/*", index):
            index += 2
            while index < length and not source.startswith("*/", index):
                index += 1
            index += 2
            continue

        if char.isalnum() or char in "_$":
            token += char
            index += 1
            continue

        if token:
            identifiers.add(token)
            token = ""
        index += 1

    if token:
        identifiers.add(token)

    return {name for name in identifiers if re.fullmatch(r"[A-Z][A-Z0-9_]+", name)}


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
            started_at=date(2024, 1, 15),
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

        # Halaman daftar hanya kerangka; data diambil lewat endpoint JSON
        self.assertContains(response, reverse("main:get_experiences_json"))
        self.assertContains(response, 'id="loading"')
        self.assertContains(response, 'id="error"')
        self.assertContains(response, 'id="empty"')
        self.assertContains(response, 'id="grid"')
        self.assertNotContains(response, self.experience.title)

    def test_experience_data_from_json_endpoint(self):
        response = self.client.get(reverse("main:get_experiences_json"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)

        fields = payload[0]["fields"]
        self.assertEqual(fields["title"], "Asisten Dosen PBP")
        self.assertEqual(fields["description"], "Membantu mahasiswa memahami pengembangan web.")
        self.assertEqual(fields["category_display"], "Part-Time")
        self.assertEqual(fields["started_at"], "2024-01-15")
        self.assertTrue(fields["is_ongoing"])
        self.assertEqual(fields["star_count"], 0)
        self.assertFalse(fields["is_starred"])

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")
        self.assertEqual(self.client.get(reverse("main:get_experiences_json")).json(), [])

    def test_completed_experience(self):
        self.experience.ended_at = date(2025, 6, 30)
        self.experience.save()

        self.assertFalse(self.experience.is_ongoing)

        fields = self.client.get(reverse("main:get_experiences_json")).json()[0]["fields"]
        self.assertEqual(fields["ended_at"], "2025-06-30")
        self.assertFalse(fields["is_ongoing"])

    def test_experience_json_search_by_title(self):
        Experience.objects.create(
            title="Staff OH Fasilkom",
            description="Divisi Visual Design.",
            category="part-time",
            started_at=date(2025, 1, 15),
        )

        endpoint = reverse("main:get_experiences_json")

        # Tanpa query: semua data
        self.assertEqual(len(self.client.get(endpoint).json()), 2)

        # Pencarian sebagian, tidak case-sensitive
        for query in ["staff", "STAFF", "Fasilkom", "oh"]:
            with self.subTest(query=query):
                payload = self.client.get(endpoint, {"title": query}).json()
                self.assertEqual(len(payload), 1)
                self.assertEqual(payload[0]["fields"]["title"], "Staff OH Fasilkom")

        # Hanya cocok sebagian, bukan harus utuh
        self.assertEqual(len(self.client.get(endpoint, {"title": "asisten"}).json()), 1)

        # Tidak ada hasil
        self.assertEqual(self.client.get(endpoint, {"title": "tidak-ada-ini"}).json(), [])

        # Query kosong diperlakukan seperti tanpa filter
        self.assertEqual(len(self.client.get(endpoint, {"title": "   "}).json()), 2)

        # Query dengan karakter khusus tidak memicu error
        for query in ["%", "_", "<script>", "a&b"]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get(endpoint, {"title": query}).status_code, 200)

    def test_experience_page_prefills_search_from_query_param(self):
        response = self.client.get(reverse("main:show_experience"), {"title": "asisten"})

        self.assertContains(response, 'id="experience-search-form"')
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'value="asisten"')


class SkillTest(TestCase):
    def setUp(self):
        self.skill = Skill.objects.create(
            name="Figma",
            description="Membuat desain poster menggunakan Figma.",
            category="design",
        )

    def test_skill_url_is_accessible(self):
        response = self.client.get(reverse("main:show_skill"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "skill.html")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_skill_page_embeds_skills_endpoint(self):
        response = self.client.get(reverse("main:show_skill"))

        self.assertContains(response, f'"{reverse("main:get_skills_json")}"')

    def test_skill_data_appears_in_json_api(self):
        response = self.client.get(reverse("main:get_skills_json"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["pk"], str(self.skill.id))
        self.assertEqual(payload[0]["fields"]["name"], "Figma")
        self.assertEqual(payload[0]["fields"]["description"], self.skill.description)
        self.assertEqual(payload[0]["fields"]["category"], "design")
        self.assertEqual(payload[0]["fields"]["category_display"], "Graphic Design")
        self.assertEqual(payload[0]["fields"]["star_count"], 0)
        self.assertFalse(payload[0]["fields"]["is_starred"])

    def test_skill_json_api_filters_by_name(self):
        Skill.objects.create(
            name="Python",
            description="Menulis kode backend.",
            category="programming",
        )

        response = self.client.get(reverse("main:get_skills_json"), {"name": "pyth"})

        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["fields"]["name"], "Python")

    def test_empty_skill_page(self):
        Skill.objects.all().delete()
        response = self.client.get(reverse("main:get_skills_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_empty_skill_page_renders_empty_state_copy(self):
        Skill.objects.all().delete()
        response = self.client.get(reverse("main:show_skill"))

        self.assertContains(response, "Belum ada skill yang ditambahkan.")

    def test_search_query_empty_state_copy(self):
        response = self.client.get(reverse("main:show_skill"), {"name": "tidak-ada"})

        self.assertContains(response, "Tidak ada skill dengan nama tersebut.")

    def test_skill_js_never_references_undefined_identifiers(self):
        """Cegah regresi: JS pernah crash karena salah nama variabel/endpoint."""
        response = self.client.get(reverse("main:show_skill"))
        script = response.content.decode()

        # Nama yang pernah salah ketik dan memicu ReferenceError
        for typo in (
            "projectsAbortController",
            "BASE_PROJECTS_ENDPOINT",
            "BASE_SKILLS_ENDPOINT",
            "skill_list",
        ):
            with self.subTest(typo=typo):
                self.assertNotIn(typo, script)

        for constant in (
            "SKILLS_ENDPOINT",
            "CREATE_SKILL_ENDPOINT",
            "DUMMY_UUID",
            "CSRF_TOKEN",
            "SEARCH_PARAM",
        ):
            with self.subTest(constant=constant):
                self.assertIn(f"const {constant} =", script)

        declared = set(re.findall(r"\b(?:const|let)\s+([A-Z][A-Z0-9_]+)\s*=", script))
        used = extract_js_identifiers(script)

        self.assertTrue(used, "tidak ada identifier JS yang terdeteksi")
        self.assertEqual(used - declared, set())

    def test_dummy_uuid_is_ascii_so_url_substitution_works(self):
        """Cegah regresi: nol subscript (U+2080) bikin .replace() gagal diam-diam."""
        response = self.client.get(reverse("main:show_skill"))
        script = response.content.decode()

        self.assertIn("const DUMMY_UUID = ", script)
        dummy = re.search(r"const DUMMY_UUID = '([^']+)'", script).group(1)

        self.assertEqual(dummy, "00000000-0000-0000-0000-000000000000")
        self.assertNotIn("\u2080", script)
        self.assertEqual(
            f"/skill/{dummy}/delete/".replace(dummy, str(self.skill.id)),
            f"/skill/{self.skill.id}/delete/",
        )

    def test_card_builder_only_reads_fields_the_api_provides(self):
        """Cegah regresi: JS pernah baca skill.skill_url yang tidak ada di API."""
        response = self.client.get(reverse("main:show_skill"))
        script = response.content.decode()

        self.assertIn("function buildSkillCardElement", script)
        self.assertIn("// Fetch data skill", script)

        card_builder = script[
            script.index("function buildSkillCardElement") : script.index("// Fetch data skill")
        ]
        referenced = set(re.findall(r"skill\.([A-Za-z_][A-Za-z0-9_]*)", card_builder))

        api_fields = set(
            self.client.get(reverse("main:get_skills_json")).json()[0]["fields"]
        )

        self.assertTrue(referenced, "tidak ada field skill.* yang terdeteksi")
        self.assertEqual(referenced - api_fields, set())

    def test_search_uses_query_param_the_view_reads(self):
        """Cegur regresi: JS pernah kirim ?title= padahal view baca ?name=."""
        response = self.client.get(reverse("main:show_skill"))

        self.assertContains(response, 'const SEARCH_PARAM = "name"')
        self.assertNotContains(response, "?title=")


class AuthorizationTest(TestCase):
    def setUp(self):
        self.skill = Skill.objects.create(
            name="Figma",
            description="Membuat desain poster menggunakan Figma.",
            category="design",
        )
        self.achievement = Achievement.objects.create(
            name="Juara 1 Hackathon",
            category="hackathon",
            description="Menang di kompetisi hackathon nasional.",
            position="Juara 1",
            timestamp_achieved=2025,
        )

        self.editor_group = Group.objects.create(name="Editor")
        self.editor_group.permissions.set(
            Permission.objects.filter(
                codename__in=[
                    "add_skill",
                    "change_skill",
                    "delete_skill",
                    "add_achievement",
                    "change_achievement",
                    "delete_achievement",
                ]
            )
        )

        self.editor = User.objects.create_user("editor", "editor@test.com", "pass123")
        self.editor.groups.add(self.editor_group)

        self.normal_user = User.objects.create_user("biasa", "biasa@test.com", "pass123")
        self.superuser = User.objects.create_superuser("admin", "admin@test.com", "pass123")

    def test_anonymous_redirected_to_login(self):
        for url_name in [
            "main:create_skill",
            "main:edit_skill",
            "main:delete_skill",
            "main:create_achievement",
            "main:edit_achievement",
            "main:delete_achievement",
        ]:
            with self.subTest(url_name=url_name):
                if "edit_" in url_name or "delete_" in url_name:
                    target = reverse(url_name, args=[self.skill.id if "skill" in url_name else self.achievement.id])
                else:
                    target = reverse(url_name)
                response = self.client.get(target)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login/", response.url)

    def test_normal_user_forbidden(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            reverse("main:create_skill"),
            {"name": "Python", "description": "Coding", "category": "programming"},
        )
        self.assertEqual(response.status_code, 403)

    def test_normal_user_cannot_see_action_buttons(self):
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse("main:show_skill"))

        self.assertNotContains(response, "Tambah Skill")
        self.assertContains(response, 'const CAN_ADD_SKILL = "false" === "true"')
        self.assertContains(response, 'const CAN_EDIT_SKILL = "false" === "true"')
        self.assertContains(response, 'const CAN_DELETE_SKILL = "false" === "true"')

    def test_editor_sees_add_button_and_modal(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse("main:show_skill"))

        self.assertContains(response, "Tambah Skill")
        self.assertContains(response, 'id="add-skill-modal"')
        self.assertContains(response, 'const CAN_ADD_SKILL = "true" === "true"')

    def test_editor_can_create_skill(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("main:create_skill"),
            {"name": "Python", "description": "Coding", "category": "programming"},
        )
        self.assertRedirects(response, reverse("main:show_skill"))
        self.assertTrue(Skill.objects.filter(name="Python").exists())

    def test_editor_can_edit_skill(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("main:edit_skill", args=[self.skill.id]),
            {"name": "Figma Baru", "description": "Deskripsi baru", "category": "design"},
        )
        self.assertRedirects(response, reverse("main:show_skill"))
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.name, "Figma Baru")

    def test_editor_can_delete_achievement(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("main:delete_achievement", args=[self.achievement.id])
        )
        self.assertRedirects(response, reverse("main:show_achievement"))
        self.assertFalse(Achievement.objects.filter(id=self.achievement.id).exists())

    def test_editor_can_delete_skill(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse("main:delete_skill", args=[self.skill.id]))

        self.assertRedirects(response, reverse("main:show_skill"))
        self.assertFalse(Skill.objects.filter(id=self.skill.id).exists())
        self.assertNotIn(self.skill.id, [
            item["pk"] for item in self.client.get(reverse("main:get_skills_json")).json()
        ])

    def test_normal_user_cannot_delete_skill(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(reverse("main:delete_skill", args=[self.skill.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Skill.objects.filter(id=self.skill.id).exists())

    def test_superuser_can_access_all(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:create_skill"),
            {"name": "Superuser Skill", "description": "Coding", "category": "programming"},
        )
        self.assertRedirects(response, reverse("main:show_skill"))
        self.assertTrue(Skill.objects.filter(name="Superuser Skill").exists())


class SkillAjaxTest(TestCase):
    def setUp(self):
        self.editor_group = Group.objects.create(name="Editor Ajax")
        self.editor_group.permissions.set(
            Permission.objects.filter(codename__in=["add_skill"])
        )
        self.editor = User.objects.create_user("editor_ajax", "editor_ajax@test.com", "pass123")
        self.editor.groups.add(self.editor_group)
        self.normal_user = User.objects.create_user("biasa_ajax", "biasa_ajax@test.com", "pass123")
        self.superuser = User.objects.create_superuser("admin_ajax", "admin_ajax@test.com", "pass123")

        self.payload = {
            "name": "Python",
            "description": "Menulis kode backend.",
            "category": "programming",
        }

    def test_anonymous_gets_json_403(self):
        response = self.client.post(reverse("main:create_skill_ajax"), self.payload)

        self.assertEqual(response.status_code, 403)
        self.assertIn("message", response.json())
        self.assertFalse(Skill.objects.filter(name="Python").exists())

    def test_normal_user_gets_json_403(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(reverse("main:create_skill_ajax"), self.payload)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Skill.objects.filter(name="Python").exists())

    def test_editor_with_add_permission_can_create(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse("main:create_skill_ajax"), self.payload)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Skill.objects.filter(name="Python").exists())
        self.assertIn("pk", response.json())

    def test_superuser_can_create(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse("main:create_skill_ajax"), self.payload)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Skill.objects.filter(name="Python").exists())

    def test_invalid_payload_returns_field_errors(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:create_skill_ajax"),
            {"name": "", "description": "", "category": "programming"},
        )

        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("name", errors)
        self.assertIn("description", errors)
        self.assertFalse(Skill.objects.exists())

    def test_category_rejects_display_label(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:create_skill_ajax"),
            {"name": "Figma", "description": "Desain", "category": "Graphic Design"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("category", response.json()["errors"])
        self.assertFalse(Skill.objects.exists())

    def test_get_is_not_allowed(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("main:create_skill_ajax"))

        self.assertEqual(response.status_code, 405)


class AuthFlowTest(TestCase):
    """Route register, login, dan logout sebelumnya tidak punya test sama sekali."""

    def setUp(self):
        self.user = User.objects.create_user("boba", "boba@test.com", "pass12345")

    def test_register_page_renders(self):
        response = self.client.get(reverse("main:register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")

    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": "baru",
                "password1": "rahasia-kuat-123",
                "password2": "rahasia-kuat-123",
            },
        )

        self.assertRedirects(response, reverse("main:login"))
        self.assertTrue(User.objects.filter(username="baru").exists())

    def test_register_rejects_password_mismatch(self):
        response = self.client.post(
            reverse("main:register"),
            {"username": "baru2", "password1": "rahasia-kuat-123", "password2": "beda-123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="baru2").exists())

    def test_login_page_renders(self):
        response = self.client.get(reverse("main:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_with_valid_credentials_redirects_home(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "boba", "password": "pass12345"},
        )

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_with_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "boba", "password": "salah"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_sets_last_login_cookie(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "boba", "password": "pass12345"},
        )

        self.assertIn("last_login", response.cookies)

    def test_logout_clears_session_and_cookie(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("main:logout"))

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.cookies["last_login"].value, "")

    def test_register_message_reaches_login_page(self):
        """Pesan sukses register harus tampil di halaman tujuan."""
        self.client.post(
            reverse("main:register"),
            {
                "username": "baru3",
                "password1": "rahasia-kuat-123",
                "password2": "rahasia-kuat-123",
            },
        )

        response = self.client.get(reverse("main:login"), follow=True)

        self.assertContains(response, "Akun berhasil dibuat")


class StarTest(TestCase):
    """Route toggle_star_* sebelumnya tidak punya test sama sekali."""

    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
            started_at=date(2024, 1, 15),
        )
        self.skill = Skill.objects.create(
            name="Figma",
            description="Membuat desain poster.",
            category="design",
        )
        self.achievement = Achievement.objects.create(
            name="Juara 1 Hackathon",
            category="hackathon",
            description="Menang di kompetisi hackathon nasional.",
            position="Juara 1",
            timestamp_achieved=2025,
        )
        self.user = User.objects.create_user("penintip", "penintip@test.com", "pass12345")

    def test_anonymous_cannot_star(self):
        for url_name, obj in (
            ("main:toggle_star_experience", self.experience),
            ("main:toggle_star_skill", self.skill),
            ("main:toggle_star_achievement", self.achievement),
        ):
            with self.subTest(url_name=url_name):
                response = self.client.post(reverse(url_name, args=[obj.id]))
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login/", response.url)

    def test_star_turns_on_then_off(self):
        cases = (
            ("main:toggle_star_experience", self.experience, "starred_experiences"),
            ("main:toggle_star_skill", self.skill, "starred_skills"),
            ("main:toggle_star_achievement", self.achievement, "starred_achievements"),
        )
        for url_name, obj, relation in cases:
            with self.subTest(url_name=url_name):
                self.client.force_login(self.user)

                self.client.post(reverse(url_name, args=[obj.id]))
                self.assertTrue(getattr(self.user, relation).filter(pk=obj.pk).exists())

                self.client.post(reverse(url_name, args=[obj.id]))
                self.assertFalse(getattr(self.user, relation).filter(pk=obj.pk).exists())

    def test_two_users_can_star_the_same_object(self):
        other = User.objects.create_user("penintip2", "penintip2@test.com", "pass12345")

        self.client.force_login(self.user)
        self.client.post(reverse("main:toggle_star_skill", args=[self.skill.id]))
        self.client.force_login(other)
        self.client.post(reverse("main:toggle_star_skill", args=[self.skill.id]))

        self.assertEqual(self.skill.starred_by.count(), 2)

        payload = self.client.get(reverse("main:get_skills_json")).json()
        self.assertEqual(payload[0]["fields"]["star_count"], 2)
        self.assertEqual(
            sorted(payload[0]["fields"]["starred_by_names"].split(", ")),
            ["penintip", "penintip2"],
        )

    def test_star_unknown_id_returns_404(self):
        self.client.force_login(self.user)
        missing = uuid.uuid4()

        for url_name in (
            "main:toggle_star_experience",
            "main:toggle_star_skill",
            "main:toggle_star_achievement",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.post(reverse(url_name, args=[missing]))
                self.assertEqual(response.status_code, 404)

    def test_star_redirects_back_to_own_page(self):
        self.client.force_login(self.user)

        self.assertRedirects(
            self.client.post(reverse("main:toggle_star_experience", args=[self.experience.id])),
            reverse("main:show_experience"),
        )
        self.assertRedirects(
            self.client.post(reverse("main:toggle_star_skill", args=[self.skill.id])),
            reverse("main:show_skill"),
        )
        self.assertRedirects(
            self.client.post(reverse("main:toggle_star_achievement", args=[self.achievement.id])),
            reverse("main:show_achievement"),
        )


class AchievementApiTest(TestCase):
    """Route get_achievements_json sebelumnya tidak punya test sama sekali."""

    def setUp(self):
        self.achievement = Achievement.objects.create(
            name="Juara 1 Hackathon",
            category="hackathon",
            description="Menang di kompetisi hackathon nasional.",
            position="Juara 1",
            timestamp_achieved=2025,
        )

    def test_api_returns_achievements(self):
        response = self.client.get(reverse("main:get_achievements_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["pk"], str(self.achievement.id))
        self.assertEqual(payload[0]["fields"]["name"], "Juara 1 Hackathon")
        self.assertEqual(payload[0]["fields"]["position"], "Juara 1")
        self.assertEqual(payload[0]["fields"]["timestamp_achieved"], 2025)
        self.assertEqual(payload[0]["fields"]["category_display"], "Hackathon")
        self.assertEqual(payload[0]["fields"]["star_count"], 0)
        self.assertFalse(payload[0]["fields"]["is_starred"])

    def test_api_filters_by_name(self):
        Achievement.objects.create(
            name="Juara 2 Poster",
            category="poster",
            description="Poster terbaik.",
            position="Juara 2",
            timestamp_achieved=2024,
        )

        payload = self.client.get(reverse("main:get_achievements_json"), {"name": "poster"}).json()

        self.assertEqual([item["fields"]["name"] for item in payload], ["Juara 2 Poster"])

    def test_api_empty_returns_empty_list(self):
        Achievement.objects.all().delete()

        response = self.client.get(reverse("main:get_achievements_json"))

        self.assertEqual(response.json(), [])

    def test_api_shape_matches_skill_api(self):
        """Kedua endpoint API harus punya kontrak yang sama."""
        Skill.objects.create(
            name="Figma",
            description="Membuat desain poster.",
            category="design",
        )

        skill_fields = set(
            self.client.get(reverse("main:get_skills_json")).json()[0]["fields"]
        )
        achievement_fields = set(
            self.client.get(reverse("main:get_achievements_json")).json()[0]["fields"]
        )

        shared = {"name", "category", "category_display", "description", "icon_url",
                  "star_count", "is_starred", "starred_by_names"}
        self.assertTrue(skill_fields.issuperset(shared))
        self.assertTrue(achievement_fields.issuperset(shared))


class TemplateFixTest(TestCase):
    """Cegah regresi untuk perbaikan pada kelompok A."""

    def setUp(self):
        self.skill = Skill.objects.create(
            name="Figma",
            description="Membuat desain poster.",
            category="design",
        )
        self.achievement = Achievement.objects.create(
            name="Juara 1 Hackathon",
            category="hackathon",
            description="Menang di kompetisi hackathon nasional.",
            position="Juara 1",
            timestamp_achieved=2025,
        )

    def test_social_links_are_absolute_urls(self):
        """Cegah regresi: LinkedIn tanpa https:// jadi tautan relatif mati."""
        response = self.client.get(reverse("main:show_main"))
        html = response.content.decode()

        for href in re.findall(r'class="social-link"[^>]*|href="([^"]+)"\s+class="social-link"', html):
            self.assertTrue(href.startswith(("http://", "https://", "mailto:")), href)

        self.assertContains(response, 'href="https://www.linkedin.com/')
        self.assertNotContains(response, 'href="www.')

    def test_skill_empty_state_message_is_updated_by_javascript(self):
        """Cegah regresi: teks empty state harus ikut berubah saatSearching client-side."""
        response = self.client.get(reverse("main:show_skill"))
        html = response.content.decode()

        self.assertContains(response, 'id="empty-message"')
        self.assertIn("emptyMessage.textContent = searchQuery", html)
        self.assertIn("'Tidak ada skill dengan nama tersebut.'", html)
        self.assertIn("'Belum ada skill yang ditambahkan.'", html)

    def test_category_fields_render_as_select(self):
        """Cegah regresi: category pernah TextInput sehingga label tidak valid."""
        for form_class in (SkillForm, AchievementForm):
            with self.subTest(form_class=form_class.__name__):
                widget = form_class()["category"].field.widget
                self.assertEqual(type(widget).__name__, "Select")

    def test_category_rejects_label_in_both_forms(self):
        skill_form = SkillForm({
            "name": "X", "description": "Y", "category": "Graphic Design",
        })
        achievement_form = AchievementForm({
            "name": "X", "description": "Y", "position": "Juara 1",
            "timestamp_achieved": 2025, "category": "Hackathon",
        })

        self.assertFalse(skill_form.is_valid())
        self.assertIn("category", skill_form.errors)
        self.assertFalse(achievement_form.is_valid())
        self.assertIn("category", achievement_form.errors)

    def test_success_message_appears_after_skill_created_without_js(self):
        """Cegah regresi: messages.success() pernah tidak pernah dirender."""
        group = Group.objects.create(name="Editor Pesan")
        group.permissions.set(Permission.objects.filter(codename="add_skill"))
        editor = User.objects.create_user("editor_pesan", "editor_pesan@test.com", "pass12345")
        editor.groups.add(group)
        self.client.force_login(editor)

        response = self.client.post(
            reverse("main:create_skill"),
            {"name": "Skill Via Form", "description": "Tanpa JS.", "category": "design"},
            follow=True,
        )

        self.assertContains(response, "Skill baru berhasil ditambahkan!")
        self.assertContains(response, "form-message--success")

    def test_success_message_appears_after_achievement_created(self):
        group = Group.objects.create(name="Editor Pesan 2")
        group.permissions.set(Permission.objects.filter(codename="add_achievement"))
        editor = User.objects.create_user("editor_pesan2", "editor_pesan2@test.com", "pass12345")
        editor.groups.add(group)
        self.client.force_login(editor)

        response = self.client.post(
            reverse("main:create_achievement"),
            {
                "name": "Prestasi Baru",
                "description": "Deskripsi.",
                "position": "Juara 1",
                "timestamp_achieved": 2025,
                "category": "hackathon",
            },
            follow=True,
        )

        self.assertContains(response, "Pencapaian baru berhasil ditambahkan!")

    def test_no_page_renders_messages_twice(self):
        """base.html yang merender messages, jadi tidak boleh ada duplikat di template lain."""
        base_dir = Path(django_settings.BASE_DIR) / "templates"
        occurrences = sum(
            path.read_text(encoding="utf-8").count("{% for message in messages %}")
            for path in base_dir.rglob("*.html")
        )

        self.assertEqual(occurrences, 1)

    def test_login_page_still_shows_messages(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "tidak-ada", "password": "salah"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct")


class ProductionSettingsTest(SimpleTestCase):
    """Cegah regresi: DEBUG pernah hardcoded True sehingga aktif juga di produksi."""

    INSPECTED = (
        "PRODUCTION",
        "DEBUG",
        "SECRET_KEY",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
        "DATABASES",
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SECURE_HSTS_SECONDS",
        "SECURE_PROXY_SSL_HEADER",
    )

    def _load_settings(self, **environment):
        """Jalankan settings.py di module baru dengan environment tertentu.

        Dua hal diisolasi supaya hasil test tidak bergantung pada file lokal:
        - importlib.reload memakai objek module yang sama, jadi atribut produksi
          bisa "bocor" ke skenario development.
        - .env / .env.prod milik developer dimock, supaya hanya environment
          yang dipakai test yang menentukan hasil.
        """
        saved = dict(os.environ)
        os.environ.clear()
        os.environ.update(environment)
        loaded_files = []

        def fake_load_dotenv(path, *args, **kwargs):
            loaded_files.append(Path(path).name)
            return True

        try:
            with mock.patch("dotenv.load_dotenv", fake_load_dotenv):
                spec = importlib.util.spec_from_file_location(
                    "portofolio_settings_probe", Path(portofolio_settings.__file__)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            return SimpleNamespace(**{
                name: getattr(module, name, None) for name in self.INSPECTED
            }), loaded_files
        finally:
            os.environ.clear()
            os.environ.update(saved)

    def _production_env(self, **extra):
        return {
            "PRODUCTION": "true",
            "SECRET_KEY": "x" * 60,
            "DB_NAME": "d",
            "DB_USER": "u",
            "DB_PASSWORD": "p",
            "DB_HOST": "h",
            "DB_PORT": "5432",
            **extra,
        }

    def test_debug_is_off_in_production(self):
        settings, _ = self._load_settings(**self._production_env())

        self.assertTrue(settings.PRODUCTION)
        self.assertFalse(settings.DEBUG)

    def test_debug_is_on_in_development(self):
        settings, _ = self._load_settings(PRODUCTION="false")

        self.assertFalse(settings.PRODUCTION)
        self.assertTrue(settings.DEBUG)

    def test_secret_key_comes_from_env_in_production(self):
        settings, _ = self._load_settings(**self._production_env(SECRET_KEY="a" * 60))

        self.assertEqual(settings.SECRET_KEY, "a" * 60)

    def test_production_enables_https_and_secure_cookies(self):
        settings, _ = self._load_settings(**self._production_env())

        self.assertTrue(settings.SECURE_SSL_REDIRECT)
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)
        self.assertGreater(settings.SECURE_HSTS_SECONDS, 0)
        # Wajib ada, kalau tidak SECURE_SSL_REDIRECT looping di belakang proxy.
        self.assertEqual(
            settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https")
        )

    def test_development_does_not_force_https(self):
        settings, _ = self._load_settings(PRODUCTION="false")

        for name in (
            "SECURE_SSL_REDIRECT",
            "SESSION_COOKIE_SECURE",
            "CSRF_COOKIE_SECURE",
            "SECURE_HSTS_SECONDS",
            "SECURE_PROXY_SSL_HEADER",
        ):
            with self.subTest(setting=name):
                self.assertFalse(getattr(settings, name, None))

    def test_allowed_hosts_accepts_comma_separated_env(self):
        settings, _ = self._load_settings(
            PRODUCTION="false",
            ALLOWED_HOSTS="example.com, www.example.com ,",
        )

        self.assertEqual(settings.ALLOWED_HOSTS, ["example.com", "www.example.com"])

    def test_csrf_trusted_origins_accepts_env(self):
        settings, _ = self._load_settings(
            PRODUCTION="false",
            CSRF_TRUSTED_ORIGINS="https://a.example.com, https://b.example.com",
        )

        self.assertEqual(
            settings.CSRF_TRUSTED_ORIGINS,
            ["https://a.example.com", "https://b.example.com"],
        )

    def test_production_uses_postgresql(self):
        settings, _ = self._load_settings(**self._production_env())

        engine = settings.DATABASES["default"]["ENGINE"]
        self.assertEqual(engine, "django.db.backends.postgresql")
        self.assertEqual(settings.DATABASES["default"]["NAME"], "d")

    def test_development_uses_sqlite(self):
        settings, _ = self._load_settings(PRODUCTION="false")

        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3"
        )

    def test_production_refuses_to_start_without_secret_key(self):
        """Jangan pernah jalan dengan SECRET_KEY django-insecure di produksi."""
        with self.assertRaises(ImproperlyConfigured) as caught:
            self._load_settings(PRODUCTION="true", DB_NAME="d")

        self.assertIn("SECRET_KEY", str(caught.exception))

    def test_production_refuses_to_start_without_db_credentials(self):
        with self.assertRaises(ImproperlyConfigured) as caught:
            self._load_settings(PRODUCTION="true", SECRET_KEY="x" * 60)

        self.assertIn("DB_HOST", str(caught.exception))

    def test_insecure_development_key_is_not_used_in_production(self):
        settings, _ = self._load_settings(**self._production_env(SECRET_KEY="a" * 60))

        self.assertNotIn("django-insecure", settings.SECRET_KEY)

    def test_env_prod_is_loaded_only_in_production(self):
        _, prod_files = self._load_settings(**self._production_env())
        _, dev_files = self._load_settings(PRODUCTION="false")

        self.assertIn(".env.prod", prod_files)
        self.assertNotIn(".env.prod", dev_files)

    def test_env_file_is_always_loaded(self):
        _, prod_files = self._load_settings(**self._production_env())
        _, dev_files = self._load_settings(PRODUCTION="false")

        self.assertIn(".env", prod_files)
        self.assertIn(".env", dev_files)

    def test_production_is_not_inferred_from_env_prod(self):
        """PRODUCTION hanya dari environment, jadi file lokal tidak bisa menyalakan HTTPS."""
        _, _ = self._load_settings(SECRET_KEY="x" * 60)
        settings, _ = self._load_settings()

        self.assertFalse(settings.PRODUCTION)
        self.assertTrue(settings.DEBUG)
