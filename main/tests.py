from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Achievement, Experience, Skill


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
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
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")


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

    def test_skill_data_appears_on_page(self):
        response = self.client.get(reverse("main:show_skill"))

        self.assertContains(response, self.skill.name)
        self.assertContains(response, self.skill.description)
        self.assertContains(response, self.skill.get_category_display())
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_skill_page(self):
        Skill.objects.all().delete()
        response = self.client.get(reverse("main:show_skill"))

        self.assertContains(response, "Belum ada skill yang ditambahkan.")


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
        self.assertNotContains(response, ">Edit</a>")

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

    def test_superuser_can_access_all(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:create_skill"),
            {"name": "Superuser Skill", "description": "Coding", "category": "programming"},
        )
        self.assertRedirects(response, reverse("main:show_skill"))
        self.assertTrue(Skill.objects.filter(name="Superuser Skill").exists())
